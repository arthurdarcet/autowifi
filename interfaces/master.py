from helpers import LoopThread

class Thread(object):
    LOOP_SLEEP = 60
    def __init__(self, interface):
        self.interface = interface

    def _run(self):
        return True
