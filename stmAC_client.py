#!/usr/bin/env python3
'''OCS client for kikusui PCR 500MA for stimulator'''

from time import sleep
from ocs.matched_client import MatchedClient

def main():
    '''Stimulator AC supply client'''
    
    stmac_client = MatchedClient('pcr')
    status, message, session = stmac_client.get_values(channel=0)
    print(status, message)
    print(session['data'])

    sleep(1)

    #stmac_client.set_values(channel=0, tc_type=3)

    sleep(1)

    status, message, session = stcac_client.get_values(channel=0)
    print(status, message)
    print(session['data'])


if __name__ == '__main__':
    main()
