import logging, os, sys, threading
from importlib import import_module
from time import sleep

from storm.locals import create_database, Store


sys.path.insert(0, os.path.dirname(__file__))
settings = import_module(os.environ.get('AW_SETTINGS', 'settings.my'))
local_db = Store(create_database(settings.LOCAL_DB))
remote_db = lambda: Store(create_database(settings.REMOTE_DB))
logging.basicConfig(level=logging.DEBUG)

class shared(object):
    has_internet = threading.Event()

class LoopThread(threading.Thread):
    def run(self):
        while True:
            if self._run():
                sleep(self.LOOP_SLEEP)
