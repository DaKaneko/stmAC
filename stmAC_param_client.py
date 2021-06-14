#!/usr/bin/env python3
'''stmAC operation parameter setter'''
import sys
from argparse import ArgumentParser

from ocs.matched_client import MatchedClient
#from dS378 import RelayStatus


def main():
    '''stmAC setter client'''
    stmac_client = MatchedClient('stmAC', args=[])

    parser = ArgumentParser()
    parser.add_argument('-v', '--volt', type=float,
                        help='Operation Voltage (peak).')

    args = parser.parse_args()

    stmac_client = MatchedClient('stmac', args=[])

    params = {k: v for k, v in args.__dict__.items() if v is not None}
    status, message, _ = stmac_client.set_values(**params)
    print(message)

"""
    op_type = sys.argv[1]

    if op_type == 'get':
        _, _, session = stmac_client.get_relays()
        print(session['data'])
        for key, val in session['data'].items():
            print(key, val)
    elif op_type == 'set':
        param_name = sys.argv[2]
        value = sys.argv[3]

        if not value == None:
            
            
        else:
            usage()
            sys.exit(1)

        ds_client.set_relay(relay_number=relay_number, on_off=on_off)
    else:
        usage()
"""

if __name__ == '__main__':
    main()
