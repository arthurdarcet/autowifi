import logging, os.path, threading, time

from sh import aircrack_ng, glob

from helpers import settings


logger = logging.getLogger('aircrack')

class Aircrack(threading.Thread):
    def __init__(self, essid):
        self.essid = essid
        self.key = None
        self._terminated = False
        super(Aircrack, self).__init__()
        self.start()

    def run(self):
        key_file = 'data/key-{}'.format(self.essid)
        while not os.path.exists(key_file) and not self._terminated:
            self._process = aircrack_ng(
                '-q',
                '-l', key_file,
                '-e', self.essid,
                glob('data/*.cap'),
                _err=lambda l: 0
            )
            logger.debug('Not enough data to crack the key, trying again in %s seconds', settings.AIRCRACK_DELAY_BETWEEN_TRIES)
            time.sleep(settings.AIRCRACK_DELAY_BETWEEN_TRIES)

        with open(key_file, 'r') as f:
            self.key = f.read()

    def terminate(self):
        self._process.terminate()
        self._terminated = True
