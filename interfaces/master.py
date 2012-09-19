from helpers import LoopThread

class Thread(object):
    LOOP_SLEEP = 60
    def __init__(self, interface):
        super(Thread, self).__init__()
        self.interface = interface

    def _run(self):
        return True
