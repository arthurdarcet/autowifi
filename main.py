import os
from argparse import ArgumentParser

from aircrack import Thread as AircrackThread
from interfaces import Interface, InterfacesSelection


def main():
    if os.getuid() != 0:
        raise Exception('Need to be root')
    parser = ArgumentParser()
    parser.add_argument('-i', '--use-if', default='', help='List of comma separated interfaces the script can use. If empty all interfaces are used. Default: empty.')
    args = parser.parse_args()

    interfaces = InterfacesSelection([dev.strip() for dev in args.use_if.split(',') if dev])
    interfaces.start()

    aircrack = AircrackThread(interfaces[Interface.MONITOR])
    aircrack.start()

if __name__ == '__main__':
    main()
