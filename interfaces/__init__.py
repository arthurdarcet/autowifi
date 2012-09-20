import logging

from sh import iwconfig

from helpers import settings, LoopThread
from interfaces.generic import Interface
from interfaces.managed import ManagedInterface
from interfaces.master import MasterInterface


class InterfacesSelection(LoopThread):
    LOOP_SLEEP = settings.INTERFACES_SELECTION_SLEEP

    def __init__(self, to_use_if):
        super(InterfacesSelection, self).__init__()
        self._to_use_if = to_use_if
        self._used_if = []
        self._interfaces = {}
        self['master'] = MasterInterface()
        self['monitor'] = Interface()
        self['managed'] = ManagedInterface()

    def _run(self):
        for i in self._available_ifs():
            for label in ('master', 'monitor', 'managed'):
                if self[label].dev is None and Interface(dev=i, init_th=False).mode(label):
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
                self[label].start()

        if not self['monitor'].dev:
            logging.critical('No monitor-able interface were found. Trying again in %s seconds', self.LOOP_SLEEP)

        return True

    def _available_ifs(self):
        for i in iwconfig().split('\n\n'):
            if 'IEEE 802' in i:
                dev = i.split('IEEE 802', 1)[0].strip()
                if (
                    (not self._to_use_if or dev in self._to_use_if)
                    and dev not in self._used_if
                    and dev != settings.DUMMY_MANAGED_IF
                ):
                    self._used_if.append(dev)
                    yield dev

    def __str__(self):
        return ', '.join('{}: {}'.format(l,i) for l,i in self._interfaces.items())

    def __getitem__(self, item):
        return self._interfaces[item]

    def __setitem__(self, item, val):
        self._interfaces[item] = val
