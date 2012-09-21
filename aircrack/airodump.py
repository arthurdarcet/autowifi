import logging, re, threading
from collections import defaultdict
from time import sleep

from sh import airodump_ng

from networks import Network


class Thread(threading.Thread):
    def __init__(self, interface):
        super(Thread, self).__init__()
        self.interface = interface

    def run(self):
        self.interface.ready.wait()
        self.target_network = self.select_target_network()

    def select_target_network(self):
        parser = Parser()
        airodump_ng('--encrypt', 'wep', self.interface.dev, _err=parser.feed_line)
        sleep(30)
        print parser._networks, parser._clients
        print parser.get_sorted_networks()

        return Network(None, None)


class Parser(object):
    DATA_LINE = re.compile(r'^ (\(not associated\)|[ABCDEF0-9]{2}(:[ABCDEF0-9]{2}){5})  .*$')
    NETWORKS_HEADER = u' BSSID              PWR  Beacons    #Data, #/s  CH  MB   ENC  CIPHER AUTH ESSID\n'
    CLIENTS_HEADER = u' BSSID              STATION            PWR   Rate    Lost  Packets  Probes     \n'

    def __init__(self):
        self._parsing_networks = False
        self._networks = defaultdict(lambda: {'clients': set()})
        self._clients = defaultdict(dict)

    def feed_line(self, line):
        if Parser.DATA_LINE.match(line) is not None:
            logging.debug('Airodump: parsing data line {}', line)
            bssid = line[1:18].strip()
            if self._parsing_networks:
                self[bssid].update({
                    'bssid': bssid,
                    'power': int(line[19:23]),
                    'nb_beacons': int(line[24:32]),
                    'nb_data': int(line[33:41]),
                    'inj_speed': int(line[42:46]),
                    'ch': int(line[47:50]),
                    'essid': line[74:-1],  # TODO get full essid
                })
            else:
                station = line[20:37]
                self[bssid]['clients'].add(station)
                self._clients[station].update({
                    'station': station,
                    'power': int(line[38:42]),
                    'packets': int(line[58:67]),
                    'lost': int(line[51:58]),
                    'probes': line[67:-1],
                })
        elif line == Parser.NETWORKS_HEADER:
            self._parsing_networks = True
        elif line == Parser.CLIENTS_HEADER:
            self._parsing_networks = False
        return False

    def __getitem__(self, item):
        return self._networks[item]

    def __setitem__(self, item, value):
        self._networks[item] = value

    def get_sorted_networks(self):
        return sorted(self._networks.values(), key=lambda net: -net['power'])
