import logging, os, sys, threading
from importlib import import_module
from time import sleep

from storm.locals import create_database, Store


sys.path.insert(0, os.path.dirname(__file__))
settings = import_module(os.environ.get('AW_SETTINGS', 'settings.my'))
local_db = lambda: Store(create_database(settings.LOCAL_DB))
remote_db = lambda: Store(create_database(settings.REMOTE_DB))
logging.basicConfig(level=logging.DEBUG)

class LoopThread(threading.Thread):
    LOOP_SLEEP = -1
    def __init__(self):
        super(LoopThread, self).__init__()
        self._terminated = False
    def _run(self):
        return True
    def _once(self):
        pass
    def run(self):
        if self.LOOP_SLEEP < 0:
            self._run()
            self._once()
            return
        once = False
        while not self._terminated:
            b = self._run()
            if not once:
                self._once()
                once = True
            if b:
                sleep(self.LOOP_SLEEP)
    def terminate(self):
        self._terminated = True
