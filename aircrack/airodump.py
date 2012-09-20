import threading

from sh import airodump_ng

from networks import Network


class Thread(threading.Thread):
    def __init__(self, interface):
        super(Thread, self).__init__()
        self.interface = interface

    def run(self):
        self.interface.ready.wait()
        self.target_network = self.select_target_network()

    def select_target_network(self):
        for line in airodump_ng('--encrypt', 'wep', self.interface.dev, _iter=True):
            print repr(line)
        return Network(None, None)
