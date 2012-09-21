import logging

from storm.locals import Bool, Int, Unicode

from helpers import local_db, remote_db, settings

local = local_db()
local.execute("""
CREATE TABLE IF NOT EXISTS `networks` (
  `bssid` varchar(255),
  `essid` varchar(255) NOT NULL,
  `key` varchar(255) NOT NULL,
  `location` varchar(255),
  `on_remote` tinyint(1) NOT NULL,
  PRIMARY KEY (`bssid`, `essid`)
);
""")
local.commit()
del local

class Network(object):
    __storm_table__ = 'networks'
    bssid = Unicode(primary=True)
    essid = Unicode()
    key = Unicode()
    on_remote = Bool()

    def __init__(self, bssid, essid, key=None, on_remote=False):
        self.bssid = bssid
        self.essid = essid
        self.key = key
        self.on_remote = on_remote
    def __str__(self):
        return u'{}::{}::{}'.format(self.bssid, self.essid, self.key)
    def __eq__(self, n):
        return self.bssid == n.bssid and self.essid == n.essid and self.key == n.key and self.on_remote == n.on_remote
    def __ne__(self, n):
        return not self == n


def update_local():
    logging.info(u'Updating local database')
    remote = remote_db()
    local = local_db()
    for remote_net in remote.find(Network):
        if remote_net.bssid.startswith('_'):
            local_net = local.find(Network, essid=remote_net.essid, key=remote_net.key).one()
            if local_net and not local_net.bssid.startswith('_'):
                logging.info(u'Updating MAC address of %s with local data', local_net)
                remote_net.bssid = local_net.bssid
                remote.commit()

        local_net = local.get(Network, remote_net.bssid)
        if local_net and local_net != remote_net:
            logging.warn(u'Overriding local %s with remote data', local_net)
            local_net.bssid = remote_net.bssid
            local_net.essid = remote_net.essid
            local_net.key = remote_net.key
            local_net.on_remote = True
        elif not local_net:
            logging.info(u'Retrieved %s from remote database', remote_net)
            local_net = Network(remote_net.bssid, remote_net.essid, remote_net.key, True)
            local.add(local_net)
    local.commit()

def update_remote():
    logging.info(u'Updating remote database')

def update_db():
    update_local()
    update_remote()
