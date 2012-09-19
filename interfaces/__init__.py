import logging, threading

from sh import iwconfig

from helpers import settings, shared, LoopThread
from interfaces.master import Thread as MasterThread
from interfaces.managed import Thread as ManagedThread


class If(object):
    thread = None
    def __init__(self, dev):
        self.dev = dev

    def __unicode__(self):
        return self.dev

    def param(self, p):
        params = [p.split(':',1) for p in iwconfig(self.dev).split('  ') if ':' in p]
        for a,b in params:
            if a.lower() == p:
                return b.lower()
        raise KeyError

    def mode(self, mode=None):
        if not mode:
            return self.param('mode')
        iwconfig(self.dev, 'mode', mode)
        return self.mode() == mode


class InterfacesSelection(LoopThread):
    LOOP_SLEEP = settings.INTERFACES_SELECTION_SLEEP
    TO_USE_IF = None
    USED_IF = []

    master_if = None
    monitor_if = None
    managed_if = None

    has_monitor = threading.Event()

    def _run(self):
        ifs = []
        for i in iwconfig().split('\n\n'):
            if 'IEEE 802' in i:
                dev = i.split('IEEE 802', 1)[0].strip()
                if (not self.TO_USE_IF or dev in self.TO_USE_IF) and dev not in self.USED_IF:
                    ifs.append(If(dev))
                    self.USED_IF.append(dev)

        if self.master_if is None:
            for i in ifs:
                if i.mode('master'):
                    shared.master_if = i
                    ifs.remove(i)
                    break
        if self.monitor_if is None:
            for i in ifs:
                if i.mode('monitor'):
                    shared.monitor_if = i
                    ifs.remove(i)
                    break
        if self.managed_if is None:
            shared.managed_if = ifs[0] if ifs else None

        if not self.monitor_if and self.master_if:
            if self.master_if.mode('monitor'):
                self.monitor_if = self.master_if
                self.master_if = None

        if self.master_if is not None:
            logging.info('Using {} as the master interface', self.master_if.dev)
            self.master_if.thread = MasterThread(self.master_if)
            self.master_if.thread.start()
        if self.managed_if is not None:
            logging.info('Using {} as the managed interface', self.managed_if.dev)
            self.managed_if.thread = ManagedThread(self.managed_if)
            self.managed_if.start()

        if self.monitor_if is not None:
            logging.info('Using {} as the monitor interface', self.monitor_if.dev)
            self.has_monitor.set()
        else:
            logging.critical('No monitor-able interface were found. Trying again in {} seconds'.format(self.LOOP_SLEEP))

        return True


if not hasattr(shared, 'interfaces'):
    shared.interfaces = InterfacesSelection()
