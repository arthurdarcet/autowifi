from sh import iwconfig


class If(object):
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


class NeedInterface(Exception):
    pass

def select_if(use_if=None):
    ifs = []
    for i in iwconfig().split('\n\n'):
        if 'IEEE 802' in i:
            dev = i.split('IEEE 802', 1)[0].strip()
            if not use_if or dev in use_if:
                ifs.append(If(dev))
    master_if = None
    for i in ifs:
        if i.mode('master'):
            master_if = i
            ifs.remove(i)
            break
    monitor_if = None
    for i in ifs:
        if i.mode('monitor'):
            monitor_if = i
            break
    if not monitor_if and master_if:
        if master_if.mode('monitor'):
            monitor_if = master_if
            master_if = None
    if not monitor_if:
        raise NeedInterface

    return (monitor_if, master_if)
