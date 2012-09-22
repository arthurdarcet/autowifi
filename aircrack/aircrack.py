import logging, threading

from sh import aircrack_ng, glob


logger = logging.getLogger('aireplay')

class Aircrack(threading.Thread):
    def __init__(self, essid):
        self.essid = essid
        self.key = None
        super(Aircrack, self).__init__()
        self.start()

    def run(self):
        key_file = 'data/key-{}'.format(essid)
        self._process = aircrack_ng(
            '-q',
            '-l', key_file,
            '-e', essid,
            glob('data/*.cap'),
            _err=lambda l: 0
        )
        self._process.join()
        with open(key_file, 'r') as f:
            self.key = f.read()

    def terminate(self):
        self._process.terminate()
