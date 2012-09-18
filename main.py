import logging, os
from argparse import ArgumentParser
from time import sleep

import settings
from iwconfig import select_if, NeedInterface


def main():
    if os.getuid() != 0:
        raise Exception('Need to be root')
    parser = ArgumentParser()
    parser.add_argument('-i', '--use-if', default=None, help='List of comma separated interfaces the script can use. If empty all interfaces are used. Default: empty.')
    args = parser.parse_args()
    while True:
        try:
            monitor_if, master_if = select_if(use_if=[dev.strip() for dev in args.use_if.split(',')])
            break
        except NeedInterface:
            logging.critical('No monitor-able interface were found. Trying again in {} seconds'.format(settings.NO_MONITOR_TRY_AGAIN))
            sleep(settings.NO_MONITOR_TRY_AGAIN)


if __name__ == '__main__':
    main()