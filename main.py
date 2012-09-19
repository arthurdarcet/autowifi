import os
from argparse import ArgumentParser

from aircrack.airodump import select_target_network
from helpers import settings, shared
from interfaces import InterfacesSelection
from networks import update_local, update_remote


def main():
    if os.getuid() != 0:
        raise Exception('Need to be root')
    parser = ArgumentParser()
    parser.add_argument('-i', '--use-if', default='', help='List of comma separated interfaces the script can use. If empty all interfaces are used. Default: empty.')
    args = parser.parse_args()
    shared.interfaces.TO_USE_IF = [dev.strip() for dev in args.use_if.split(',') if dev]
    shared.interfaces.start()

    select_target_network()

if __name__ == '__main__':
    main()
