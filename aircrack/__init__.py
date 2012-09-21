import logging, time, threading

from helpers import settings

from aircrack.airodump import select_target_network

logger = logging.getLogger('aircrack')

class Thread(threading.Thread):
    def __init__(self, interface):
        super(Thread, self).__init__()
        self.interface = interface

    def run(self):
        self.interface.ready.wait()
        self.target_network = select_target_network(self.interface)
        while self.target_network is None:
            logger.warning('No suitable network found for an attack, waiting %s before scanning again', settings.AIRODUMP_SCAN_WAIT_BETWEEN_FAIL)
            time.sleep(settings.AIRODUMP_SCAN_WAIT_BETWEEN_FAIL)
            self.target_network = select_target_network(self.interface)
        logger.info('Starting attack on %s. I will try for %s seconds before giving up', self.target_network['essid'], settings.MAX_ATTACK_LENGTH)
        self.attack_begin = time.time()
