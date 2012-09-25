import logging, re, time, threading, urllib2

from sh import CommandNotFound, iw, iwconfig, kill

from helpers import local_db, settings
from interfaces.generic import Interface
from networks import Network, update_db


logger = logging.getLogger('managed')

class ManagedInterface(Interface):
    LOOP_SLEEP = 30
    LABEL = Interface.MANAGED
    _DHCPCD_SUCCESS_LINE = re.compile(r'dhcpcd\[[0-9]+\]: forked to background, child pid ([0-9]+)')

    def __init__(self):
        super(ManagedInterface, self).__init__()
        self.has_internet = threading.Event()
        self._dhcpcd_pid = None

    def _run(self):
        if _check_connectivity():
            if not self.has_internet.is_set():
                self.on_internet()
                self.has_internet.set()
        elif not self.dummy:
            self.has_internet.clear()
            for net in self.scan():
                logger.debug('Trying to connect to %s with key %s', net['essid'], net['key'])
                if self.connect(net['essid'], net['key']):
                    break

        return self.has_internet.is_set()

    def on_internet(self):
        logger.info('Internet connection found! (ESSID: %s)', self.param('essid'))
        update_db()

    def scan(self):
        powers = {}
        raw_scan = iw('dev', self.dev, 'scan')
        for i in range(4,-1,-1):
            raw_scan = raw_scan.replace('\t'*i + '\n', '<tab{}>'.format(i))
        for network in raw_scan.split('<tab0>'):
            essid = None
            power = None
            for param in network.split('<tab1>'):
                if not ': ' in param:
                    continue
                param = param.split(': ', 1)
                if param[0] == 'SSID':
                    essid = param[1]
                elif param[0] == 'signal':
                    power = int(param[1][0:5])
            if essid is None or power is None:
                logger.warning('Failure parsing the output of iw for essid %s. Complete line: %r', essid, network)
                continue
            powers[essid] = power

        logger.debug('Scan found networks %r', powers.keys())
        nets = []
        local = local_db()
        for net in local.find(Network, Network.essid.In(powers.keys())):
            nets.append({
                'essid': net.essid,
                'key': net.key,
                'power': powers[net.essid],
            })
        return sorted(nets, lambda v: v['power'])

    def connect(self, essid, key):
        try:
            from sh import dhcpcd as dhcp
        except CommandNotFound:
            from sh import dhclient as dhcp
        if self._dhcpcd_pid is not None:
            kill(self._dhcpcd_pid)

        iwconfig(self.dev, 'essid', essid)
        iwconfig(self.dev, 'key', key)
        for line in dhcp(self.dev, _err_to_out, _iter=True):
            m = ManagedInterface._DHCPCD_SUCCESS_LINE.match(line)
            if m is not None:
                self._dhcpcd_pid = m.group(1)
                return True
        return False


def _check_connectivity():
    try:
        urllib2.urlopen(settings.HAS_INTERNET_REFERENCE, timeout=1)
        return True
    except:
        return False
