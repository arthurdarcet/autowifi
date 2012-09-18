from Storm import Bool, Int, Unicode

from bootstrap import local_db, remote_db, settings


class Network(object):
    __storm_table__ = networks
    pk = Int(primary=True)
    ap_mac = Unicode()
    essid = Unicode()
    key = Unicode()
    on_remote = Bool()


def update_local():
    for net in remote_db.find(Network):
        print net
