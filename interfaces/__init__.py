import logging, threading

from sh import ifconfig, iwconfig

from helpers import settings, shared, LoopThread
from interfaces.master import Thread as MasterThread
from interfaces.managed import Thread as ManagedThread


class Interface(object):
    thread = None
    dummy = False

    def __init__(self, dev=None):
        self.dev = dev
        self.ready = threading.Event()

    def __str__(self):
        return str(self.dev)

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

    _interfaces = {
        'master': None,
        'monitor': None,
        'managed': None,
    }
    def __init__(self):
        super(InterfacesSelection, self).__init__()
        self['master'] = Interface()
        self['monitor'] = Interface()
        self['managed'] = Interface()

    def _run(self):
        for i in self._available_ifs():
            for label in ('master', 'monitor', 'managed'):
                if self[label].dev is None and Interface(i).mode(label):
                    self[label].dev = i
                    break

        if not self['monitor'].dev and self['master'].dev:
            if self['master'].mode('monitor'):
                logging.info('%s is supporting mode master, but no other interface support the mode monitor', self['master'])
                self['monitor'].dev = self['master'].dev
                self['master'].dev = None

        if self['managed'].dev is None and settings.DUMMY_MANAGED_IF is not None:
            self['managed'].dev = settings.DUMMY_MANAGED_IF
            self['managed'].dummy = True


        for label in ('master', 'monitor', 'managed'):
            if self[label].dev is not None and not self[label].ready.is_set():
                logging.info('Using %s as the %s interface', self[label], label)
                if label in InterfacesSelection.THREADS:
                    self[label].thread = InterfacesSelection.THREADS[label](self[label])
                    self[label].thread.start()
                else:
                    self[label].ready.set()

        if not self['monitor'].dev:
            logging.critical('No monitor-able interface were found. Trying again in %s seconds', self.LOOP_SLEEP)

        return True

    def _available_ifs(self):
        for i in iwconfig().split('\n\n'):
            if 'IEEE 802' in i:
                dev = i.split('IEEE 802', 1)[0].strip()
                if (not self.TO_USE_IF or dev in self.TO_USE_IF) and dev not in self.USED_IF and dev != settings.DUMMY_MANAGED_IF:
                    self.USED_IF.append(dev)
                    yield dev

    def __str__(self):
        return ', '.join('{}: {}'.format(l,i) for l,i in self._interfaces.items())

    def __getitem__(self, item):
        return self._interfaces[item]

    def __setitem__(self, item, val):
        self._interfaces[item] = val


if not hasattr(shared, 'interfaces'):
    shared.interfaces = InterfacesSelection()
