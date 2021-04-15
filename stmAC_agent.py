#!/usr/bin/env python3
'''OCS agent for kikusui PCR 500MA for stimulator
'''
import time
import os
import txaio
from ocs import ocs_agent, site_config
from ocs.ocs_twisted import TimeoutLock
from kikusuiPCR import PCR500MA

IPADDR_DEFAULT = "169.254.140.171"
WaitTimeStep  = 15.  # Seconds (same as PB2)
WaitTimeForce = 10.
VoltStep   = 1.      # Minimum step sige to change voltage (integer)
VoltLimit  = 51.     # Safety limit for too high voltage

class StmACAgent:
    '''
    OCS agent class for stimulator AC source
    '''
    def __init__(self, agent, ipaddr=None,):
        '''
        Parameters
        ----------
        ipaddr : str(4)
           IP address of AC supply
        '''
        self.active = True
        self.agent = agent
        self.log = agent.log
        self.lock = TimeoutLock()
        self.take_data = False
        self.initialized = False
        self._pcr = PCR500MA(ipaddr)

        agg_params = {'frame_length':60}
        self.agent.register_feed('acsupply', record=True, agg_params=agg_params, buffer_time=1}

    def init_pcr500(self, session, params=None):
        '''Initialization of pcr500 AC supply
        '''
        if self.initialized:
            return True, "Already initialized."

        with self.lock.acquire_timeout(timeout=0, job='init') as acquired:
            if not acquired:
                self.log.warn("Could not start init because {} is already running".format(self.lock.job))
                return False, "Could not acquire lock."
            try:
                self._pcr.checkID()
            except ValueError:
                pass
            print("AC supply PCR500 initialized.")

        self.initialized = True
        return True, "AC supply PCR500 initialized."

    def start_acq(self, session, params):
        '''Starts acquiring data.
        '''
        
        f_sample = params.get('sampling frequency', 0.1)
        sleep_time = 1/f_sample - 0.1
        if not self.initialized:
            self.init_pcr500()
            
        with self.lock.acquire_timeout(timeout=0, job='acq') as acquired:
            if not acquired:
                self.log.warn("Could not start acq because {} is already running".format(self.lock.job))
                                return False, "Could not acquire lock."
                session.set_status('running')
                self.take_data = True
                session.data = {"fields": {}}
                while self.take_data:
                    current_time = time.time()
                    data = {'timestamp':current_time, 'block_name':'acsupply','data':{}}
                    voltage = self.instr.getVoltage()
                    current = self.instr.getCurrent()
                    power = self.instr.getPower()
                    data['data']['voltage'] = voltage
                    data['data']['current'] = current
                    data['data']['power'] = power

                    field_dict = {f'acsupply': {'voltage':voltage, 'current':current, 'power':power} }
                    session.data['fields'].update(field_dict)
                    
                    time.sleep(sleep_time)
                    self.agent.publish_to_feed('acsupply',data)

                self.agent.feeds['acsupply'].flush_buffer()

        return True, 'Acquisition exited cleanly.'

    def stop_acq(self, session, params=None):
        """
        Stops the data acquisiton.
        """
        if self.take_data:
            self.take_data = False
            return True, 'requested to stop taking data.'

        return False, 'acq is not currently running.'


    def set_values(self, session, params=None):
        '''A task to set sensor parameters for AC supply
        '''
        pass
        
    def get_values(self, session, params=None):
        '''A task to provide configuration information
        '''
        pass
    
    def getACstatus(self):
        print("volt(peak) =", self._pcr.__a('MEAS:VOLT:AC?'))
        print("curr(peak) =", self._pcr.__a('MEAS:CURR:AC?'))
        print("freq =", self._pcr.__a('MEAS:FREQ?'))
        print("power =", self._pcr.__a('MEAS:POW:AC?'))
        print("preac =", self._pcr.__a('MEAS:POW:AC:REAC?'))

    def rampVoltage(self, svolt): # normal temperature control
        voltgoal = float(svolt)
        if(voltgoal<0):
            print("Voltage cannot be negative!")
            return

        while(abs(voltgoal - self.Voltage) > VoltStep):
            if(self.Voltage < voltgoal):
                self.Voltage = self.Voltage+VoltStep
            elif(self.Voltage > voltgoal):
                self.Voltage = self.Voltage-VoltStep
                
            print("Set ", self.Voltage)
            self._pcr.setVoltage(self, self.Voltage)
            sleep(1.)
            print(self._pcr.getCurrent())
            sleep(WaitTimeStep-1.)

        print("last step to", voltgoal)
        self.Voltage = voltgoal
        self._pcr.setVoltage(self, self.Voltage)
        print("Reached to ", self.Voltage)
      
    def forceZero(self): #for site work
        while(self.Voltage > VoltStep):
            self.Voltage = self.Voltage - VoltStep
            print("go down to ", self.Voltage)
            self._pcr.setVoltage(self, self.Voltage)
            sleep(WaitTimeForce)

        print("set to 0 Volt")
        self.Voltage = 0.0
        self._pcr.setVoltage(0.0)

def main():
    '''Boot OCS agent'''
    txaio.start_logging(level=os.environ.get('LOGLEVEL', 'info'))

    parser = site_config.add_arguments()

    args = site_config.parse_args('StmACAgent')
    agent_inst, runner = ocs_agent.init_site_agent(args)

    stm_ac_agent = StmACAgent(agent_inst)

    agent_inst.register_task(
        'set_values',
        stm_ac_agent.set_values
    )

    agent_inst.register_task(
        'get_values',
        stm_ac_agent.get_values
    )

    agent_inst.register_process(
        'acq',
        stm_ac_agent.start_acq,
        stm_ac_agent.stop_acq,
        startup=True
    )

    runner.run(agent_inst, auto_reconnect=True)

if __name__ == '__main__':
    main()

