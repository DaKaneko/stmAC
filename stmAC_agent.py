#!/usr/bin/env python3
'''OCS agent for kikusui PCR 500MA for stimulator
'''
import time
import os
import txaio
from ocs import ocs_agent, site_config
from ocs.ocs_twisted import TimeoutLock
from kikusuiPCR import PCR500MA

#IPADDR_DEFAULT = "169.254.140.171"
IPADDR_DEFAULT = "10.0.0.4"
WaitTimeStep  = 15.  # Seconds (same as PB2)
WaitTimeForce = 10.
VoltStep   = 1.      # Minimum step sige to change voltage (integer)
#VoltLimit  = 51.     # Safety limit for too high voltage

class stmACAgent:
    '''
    OCS agent class for stimulator AC source
    '''
    def __init__(self, agent, ipaddr=IPADDR_DEFAULT):
        '''
        Parameters
        ----------
        ipaddr : str
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
        self.agent.register_feed('acsupply', record=True, agg_params=agg_params, buffer_time=1)

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
            self.init_pcr500(session)
            
        #with self.lock.acquire_timeout(timeout=0, job='acq') as acquired:
        #    if not acquired:
        #        self.log.warn("Could not start acq because {} is already running".format(self.lock.job))
        #        return False, "Could not acquire lock."

        session.set_status('running')
        self.take_data = True
        session.data = {"fields": {}}
        while self.take_data:
                with self.lock.acquire_timeout(timeout=1, job='acq') as acquired:
                    if not acquired:
                        print(f"Lock could not be acquired because it is held by {self.lock.job}")
                        return False

                    current_time = time.time()
                    data = {'timestamp':current_time, 'block_name':'acsupply','data':{}}
                    voltage = self._pcr.getVoltage()
                    current = self._pcr.getCurrent()
                    power = self._pcr.getPower()
                    if not self.lock.release_and_acquire(timeout=10):
                        print(f"Could not re-acquire lock now held by {self.lock.job}.")
                        return False
                    
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

        volt : float
            operate AC voltage
        '''
        if params is None:
            params = {}

        with self.lock.acquire_timeout(3, job='set_values') as acquired:
            if not acquired:
                self.log.warn('Could not start set_values because '
                              f'{self.lock.job} is already running')
                return False, 'Could not acquire lock.'

            volt = params.get('volt')
            if not volt is None:
                self.voltsetting = volt
            #    self._ble2.set_speed(speed)
            
    def get_values(self, session, params=None):
        '''A task to provide configuration information
        '''
        pass

    def switchPower(self, session, params=None, state=0):
        '''A task to turn switch, state 0 = off, 1 = on
        '''
        pass


    def get_settings(self, session, params=None):
        ''' Get relay states'''
        if params is None:
            params = {}

        with self.lock.acquire_timeout(3, job='get_settings') as acquired:
            if not acquired:
                self.log.warn('Could not start get_setting because '
                              f'{self.lock.job} is already running')
                return False, 'Could not acquire lock.'

            setV = self.Voltage
            session.data = {'volt': setV}

        return True, f'Got AC status'

    
    def getACstatus(self, session, params=None):
        with self.lock.acquire_timeout(3, job='get_settings') as acquired:
            if not acquired:
                self.log.warn('Could not start get_setting because '
                              f'{self.lock.job} is already running')
                return False, 'Could not acquire lock.'

            #print(self, session, params)
            volt = self._pcr._a('MEAS:VOLT:AC?')
            curr = self._pcr._a('MEAS:CURR:AC?')
            freq = self._pcr._a('MEAS:FREQ?')
            power = self._pcr._a('MEAS:POW:AC?')
            preac = self._pcr._a('MEAS:POW:AC:REAC?')
        print(volt, curr, freq, power, preac)
        return True, f'AC {volt}, {curr}, {freq}, {power}, {preac}'
        
    def rampVoltage(self, session, params=None): # normal temperature control
        print(params)
        voltgoal = params.get('volt',0)    
        print(voltgoal)
        if(voltgoal<0):
            print("Voltage cannot be negative!")
            return False, 'Voltage cannot be negative'

        while(abs(voltgoal - self._pcr.Voltage) > VoltStep):
            if(self._pcr.Voltage < voltgoal):
                self._pcr.Voltage = self._pcr.Voltage+VoltStep
            elif(self._pcr.Voltage > voltgoal):
                self._pcr.Voltage = self._pcr.Voltage-VoltStep

            with self.lock.acquire_timeout(timeout=3, job='set_voltage') as acquired:
                print("Set ", self._pcr.Voltage)
                self._pcr.setVoltage(self._pcr.Voltage)
                time.sleep(0.5)
                print(self._pcr.getCurrent())
            time.sleep(WaitTimeStep-0.5)

        with self.lock.acquire_timeout(timeout=3, job='set_voltage') as acquired:
            print("last step to", voltgoal)
            self._pcr.Voltage = voltgoal
            print(self,self._pcr.getCurrent())
            self._pcr.setVoltage(self._pcr.Voltage)
            time.sleep(0.5)
            print(self._pcr.getCurrent())
        
        return True, f'Reached to voltage {voltgoal}'
        
    def forceZero(self, session, params=None): #for site work
        while(self._pcr.Voltage > VoltStep):
            with self.lock.acquire_timeout(timeout=3, job='set_voltage') as acquired:
                self._pcr.Voltage = self._pcr.Voltage - VoltStep
                print("go down to ", self._pcr.Voltage)
                self._pcr.setVoltage(self._pcr.Voltage)
            time.sleep(WaitTimeForce)

        print("set to 0 Volt")
        with self.lock.acquire_timeout(timeout=3, job='set_voltage') as acquired:
            self._pcr.Voltage = 0.0
            self._pcr.setVoltage(0.0)
        
        return True, f'Ramped down to 0 volt.'
        
def main():
    '''Boot OCS agent'''
    txaio.start_logging(level=os.environ.get('LOGLEVEL', 'info'))

    parser = site_config.add_arguments()

    args = site_config.parse_args('stmACAgent')
    agent_inst, runner = ocs_agent.init_site_agent(args)
    stm_ac_agent = stmACAgent(agent_inst)

   # agent_inst.register_task(
   #     'init_pcr',
   #     stm_ac_agent.init_pcr500
   # )

    agent_inst.register_process(
        'acq',
        stm_ac_agent.start_acq,
        stm_ac_agent.stop_acq,
        startup=True
    )

    agent_inst.register_task(
        'set_values',
        stm_ac_agent.set_values
    )

    agent_inst.register_task(
        'get_values',
        stm_ac_agent.get_values
    )

    agent_inst.register_task(
       'getACstatus',
        stm_ac_agent.getACstatus
    )

    agent_inst.register_task(
       'rampVoltage',
        stm_ac_agent.rampVoltage
    )

    agent_inst.register_task(
       'forceZero',
        stm_ac_agent.forceZero
    )

    runner.run(agent_inst, auto_reconnect=True)

if __name__ == '__main__':
    main()

