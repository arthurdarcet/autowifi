import logging, re, threading

from sh import aireplay_ng

from helpers import settings


logger = logging.getLogger('aireplay')

class _Thread(threading.Thread):
    def __init__(self, essid, interface):
        self.essid = essid
        self.dev = interface.dev
        self.ready = threading.Event()
        super(_Thread, self).__init__()
        self.args.append(self.dev)
        self.start()

    def run(self):
        self._process = aireplay_ng('-e', self.essid, '-h', settings.AIREPLAY_INJECTION_MAC, *self.args, _out=self._process_out)
        self._process.join()

    def _process_out(self, line):
        raise NotImplemented()

    def terminate(self):
        self._process.terminate()


class Injection(_Thread):
    RESULTS = re.compile(r'Read ([0-9]+) packets \(got ([0-9]+) ARP requests and ([0-9]+) ACKs\), sent ([0-9]+) packets...\(([0-9]+) pps\)')
    args = ['-3']

    def _process_out(self, line):
        m = RESULTS.match(line)
        if m is None:
            return
        self.read_packets = m.group(1)
        self.arp = m.group(2)
        self.acks = m.group(3)
        self.sent_packets = m.group(4)
        self.speed = m.group(5)
        if self.speed > 200 and self.arp > 200:
            self.ready.set()
        if self.sent_packets > 10000 and self.arp < 200:
            logger.warn('Injection is failing, restarting aireplay')
            self.ready.clear()
            self.run()


class Fakeauth(_Thread):
    SUCCESS = re.compile(r'^[0-9]{2}:[0-9]{2}:[0-9]{2}  Association successful :-\).*$')
    KEEP_ALIVE = re.compile(r'^[0-9]{2}:[0-9]{2}:[0-9]{2}  Sending keep-alive packet.*$')
    args = ['-1', settings.AIREPLAY_DELAY_BETWEEN_FAKE_AUTH, '-q', settings.AIREPLAY_DELAY_BETWEEN_KEEP_ALIVE]

    def _process_out(self, line):
        if not line:
            return
        if SUCCESS.match(line) or KEEP_ALIVE.match(line):
            logger.debug('Successful fakeauth :-)')
            self.ready.set()
        else:
            logger.debug('Fakeauth not ok')
            self.ready.clear()


class Deauth(_Thread):
    def __init__(self, essid, interface, client=None):
        self.args = ['-0', settings.AIREPLAY_DEAUTH_COUNT]
        if client is not None:
            self.args.append('-c', client)
        super(Deauth, self).__init__(essid, interface)

    def _process_out(self, line):
        pass
