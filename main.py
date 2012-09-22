import logging, os, threading
from argparse import ArgumentParser

from sh import glob, rm

from aircrack import Thread as AircrackThread
from interfaces import Interface, InterfacesSelection


def main():
    if os.getuid() != 0:
        raise Exception('Need to be root')

    try:
        from sh import aircrack_ng, airodump_ng, aireplay_ng
    except ImportError:
        raise Exception('aircrack_ng need to be installed')

    parser = ArgumentParser()
    parser.add_argument('-i', '--use-if', default='', help='List of comma separated interfaces the script can use. If empty all interfaces are used. Default: empty.')
    args = parser.parse_args()
    exclude_interface = [dev.strip() for dev in args.use_if.split(',') if dev]

    logging.debug('Cleaning up previous data')
    rm(glob('data/*'), _ok_code=[0,1])

    while True:
        start(exclude_interface)

excluded_networks = set()
def start(exclude_interface):
    interfaces = InterfacesSelection(exclude_interface)
    interfaces.start()

    aircrack = AircrackThread(interfaces[Interface.MONITOR], excluded_networks)
    if not aircrack.run():
        excluded_networks.add(aircrack.target['bssid'])
    interfaces.terminate()

if __name__ == '__main__':
    main()
