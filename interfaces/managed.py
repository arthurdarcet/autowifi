import logging, urllib2

from helpers import LoopThread, settings, shared
from networks import update_db

class Thread(LoopThread):
    LOOP_SLEEP = 30
    essid = None

    def __init__(self, interface):
        super(Thread, self).__init__()
        self.interface = interface

    def _run(self):
        if _check_connectivity():
            if not shared.has_internet.is_set():
                self.on_internet()
            shared.has_internet.set()
        elif not self.interface.dummy:
            pass
            # TODO initiate connexion
            # self.essid = 'blah'
        return shared.has_internet.is_set()

    def on_internet(self):
        logging.info('Internet connection found! (ESSID: %s)', self.interface.param('essid'))
        update_db()


def _check_connectivity():
    try:
        urllib2.urlopen(settings.HAS_INTERNET_REFERENCE, timeout=1)
        return True
    except urllib2.URLError:
        return False
