import logging, threading

from sh import ifconfig, iwconfig

from helpers import settings, shared, LoopThread
from interfaces.master import Thread as MasterThread
from interfaces.managed import Thread as ManagedThread


class If(object):
    thread = None

    def __init__(self, dev, dummy=False):
        self.dev = dev
        self.dummy = dummy

    def __str__(self):
        return self.dev

    def param(self, param):
        params = [p.split(':',1) for p in iwconfig(self.dev).split('  ') if ':' in p]
        for a,b in params:
            if a.lower() == param:
                return b.lower()
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


class InterfacesSelection(LoopThread):
    THREADS = {
        'master': MasterThread,
        'managed': ManagedThread,
    }

    LOOP_SLEEP = settings.INTERFACES_SELECTION_SLEEP
    TO_USE_IF = None
    USED_IF = []

    interfaces = {
        'master': None,
        'monitor': None,
        'managed': None,
    }
    has = {
        'master': threading.Event(),
        'monitor': threading.Event(),
        'managed': threading.Event(),
    }

    def _run(self):
        for i in self._available_ifs():
            for label in ('master', 'monitor', 'managed'):
                if self.interfaces[label] is None and i.mode(label):
                    self.interfaces[label] = i
                    break

        if not self.interfaces['monitor'] and self.interfaces['master']:
            if self.interfaces['master'].mode('monitor'):
                logging.info('%s is supporting mode master, but no other interface support the mode monitor', self.interfaces['master'])
                self.interfaces['monitor'] = self.interfaces['master']
                self.interfaces['master'] = None

        if self.interfaces['managed'] is None and settings.DUMMY_MANAGED_IF is not None:
            self.interfaces['managed'] = If(settings.DUMMY_MANAGED_IF, dummy=True)


        for label in ('master', 'monitor', 'managed'):
            if not self.has[label].is_set() and self.interfaces[label] is not None:
                logging.info('Using %s as the %s interface', self.interfaces[label], label)
                if label in InterfacesSelection.THREADS:
                    self.interfaces[label].thread = InterfacesSelection.THREADS[label](self.interfaces[label])
                    self.interfaces[label].thread.start()
                self.has[label].set()

        if not self.has['monitor'].is_set():
            logging.critical('No monitor-able interface were found. Trying again in %s seconds', self.LOOP_SLEEP)

        return True

    def _available_ifs(self):
        for i in iwconfig().split('\n\n'):
            if 'IEEE 802' in i:
                dev = i.split('IEEE 802', 1)[0].strip()
                if (not self.TO_USE_IF or dev in self.TO_USE_IF) and dev not in self.USED_IF and dev != settings.DUMMY_MANAGED_IF:
                    self.USED_IF.append(dev)
                    yield If(dev)

    def __str__(self):
        return ', '.join('{}: {}'.format(l,i) for l,i in self.interfaces.items())


if not hasattr(shared, 'interfaces'):
    shared.interfaces = InterfacesSelection()
