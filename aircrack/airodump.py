import csv, logging, re, time
from collections import defaultdict

from sh import airodump_ng, glob, rm
from storm.locals import And, Or

from helpers import local_db, settings
from networks import Network


logger = logging.getLogger('airodump')

def select_target_network(interface):
    rm(glob('data/*'), _ok_code=[0,1])
    networks = None
    while networks is None:
        try:
            airodump_process = airodump_ng('--encrypt', 'wep', '-w', 'data/scan', interface.dev, _err=lambda l: 0)
            time.sleep(settings.AIRODUMP_SCAN_WAIT)
            airodump_process.terminate()
            networks = Reader('data/scan-01.csv').get_sorted_networks()
        except UnicodeDecodeError, e:
            logger.warning('Decoding the output of airodump failed, trying again from scratch (Error: %s)', e)
    local = local_db()
    for net in networks:
        known_net = local.find(Network, And(Or(Network.bssid.like(u'_%'), Network.bssid == net['bssid']), Network.essid == net['essid']))
        if known_net.is_empty():
            return net
    return None


class Reader(object):
    def __init__(self, csv_path):
        self._networks = defaultdict(lambda: {'clients': set()})
        self._clients = defaultdict(dict)
        with open(csv_path, 'r') as f:
            parsing_networks = True
            for line in csv.reader(f):
                if not line or line[0] == 'BSSID':
                    continue
                if line[0] == 'Station MAC':
                    parsing_networks = False
                    continue
                logger.debug('Parsing data line %s', line)
                line = map(unicode, line)
                if parsing_networks:
                    self[line[0]].update({
                        'bssid': line[0],
                        'power': int(line[8]),
                        'nb_beacons': int(line[9]),
                        'nb_data': int(line[10]),
                        'ch': int(line[3]),
                        'essid': line[13][1:],
                    })
                else:
                    self[line[5].strip()]['clients'].add(line[0])
                    self._clients[line[0]].update({
                        'station': line[0],
                        'bssid': line[5].strip(),
                        'power': int(line[3]),
                        'packets': int(line[4]),
                        'probes': line[6].split(', '),
                    })

    def __getitem__(self, item):
        return self._networks[item]

    def __setitem__(self, item, value):
        self._networks[item] = value

    def get_sorted_networks(self):
        return sorted(filter(lambda d: 'bssid' in d, self._networks.values()), key=lambda net: -net['power'])
