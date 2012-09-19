from sh import airodump_ng

from helpers import shared

def _process(line):
    print repr(line)

def select_target_network():
    shared.interfaces['monitor'].ready.wait()
    airodump_ng('--encrypt wep', shared.interfaces['monitor'].dev, _out=_process)
