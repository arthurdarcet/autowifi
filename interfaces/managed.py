import logging, threading, urllib2

from helpers import settings
from interfaces.generic import Interface
from networks import update_db

class ManagedInterface(Interface):
    LOOP_SLEEP = 30
    LABEL = 'Managed'

    def __init__(self):
        super(ManagedInterface, self).__init__()
        self.has_internet = threading.Event()

    def _run(self):
        if _check_connectivity():
            if not self.has_internet.is_set():
                self.on_internet()
                self.has_internet.set()
        elif not self.dummy:
            self.has_internet.clear()
            sleep(200)
            # TODO initiate connexion
        return self.has_internet.is_set()

    def on_internet(self):
        logging.info('Internet connection found! (ESSID: %s)', self.param('essid'))
        update_db()


def _check_connectivity():
    try:
        urllib2.urlopen(settings.HAS_INTERNET_REFERENCE, timeout=1)
        return True
    except urllib2.URLError:
        return False
