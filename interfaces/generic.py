import logging, threading

from sh import ifconfig, iwconfig

from helpers import LoopThread


class Interface(LoopThread):
    MASTER = 'Master'
    MONITOR = 'Monitor'
    MANAGED = 'Managed'

    LABEL = MONITOR
    dummy = False

    def __init__(self, dev=None, init_th=True):
        if init_th:
            super(Interface, self).__init__()
        self.dev = dev
        self.ready = threading.Event()

    def __str__(self):
        return str(self.dev)

    def param(self, param):
        params = [p.split(':',1) for p in iwconfig(self.dev).split('  ') if ':' in p]
        for a,b in params:
            if a.lower() == param:
                return b
        raise KeyError

    def mode(self, mode=None):
        if not mode:
            return self.param('mode')
        try:
            ifconfig(self.dev, 'down')
            iwconfig(self.dev, 'mode', mode)
            ifconfig(self.dev, 'up')
            return self.mode() == mode
        except:
            return False

    def _once(self):
        self.ready.set()
        logging.debug('%s interface is ready', self.LABEL)
