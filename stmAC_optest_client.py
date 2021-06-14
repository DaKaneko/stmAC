#!/usr/bin/env python3
'''OCS client for kikusui PCR 500MA for stimulator'''

from time import sleep
from ocs.matched_client import MatchedClient
from ocs import OK
from argparse import ArgumentParser


def main():
    '''Stimulator AC supply client'''
    parser = ArgumentParser()
    parser.add_argument('-v', '--volt', type=float,
                        help='Operate AC Voltage (peak).')

    args = parser.parse_args()

    stmac_client = MatchedClient('stmAC', args=[])
    #status, message, session = stmac_client.get_values()
    #print(status, message)
    #print(session['data'])

    #sleep(1)
    print("this is stmac client")
    print(stmac_client)

    #status, message, _ = stmac_client.set_values()
    #print(message)    
    
    status, message, session = stmac_client.getACstatus()
    #print("return is", message)
    #sleep(1)
    
    #stmac_client.rampVoltage(volt=2.0)
    #print("ramped up 10")
    #sleep(30)
    #stmac_client.rampVoltage(volt=4.0)
    #print("ramped up 20")
    #sleep(600)
    #stmac_client.rampVoltage(volt=30.0)
    #print("ramped up 30")
    #sleep(600)
    
    stmac_client.rampVoltage(volt=40.0)
    print("ramped up 40")
    
    #stmac_client.forceZero()
    
    #status, message, session = stcac_client.get_values(channel=0)
    #print(status, message)
    #print(session['data'])

if __name__ == '__main__':
    main()
