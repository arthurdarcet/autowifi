import logging

from storm.locals import Bool, Int, Unicode

from bootstrap import local_db, remote_db, settings


local_db.execute("""
CREATE TABLE IF NOT EXISTS `networks` (
  `ap_mac` varchar(255),
  `essid` varchar(255) NOT NULL,
  `key` varchar(255) NOT NULL,
  `location` varchar(255),
  `on_remote` tinyint(1) NOT NULL,
  PRIMARY KEY (`ap_mac`, `essid`)
);
""")
local_db.commit()


class Network(object):
    __storm_table__ = 'networks'
    ap_mac = Unicode(primary=True)
    essid = Unicode()
    key = Unicode()
    on_remote = Bool()

    def __init__(self, ap_mac, essid, key=None, on_remote=False):
        self.ap_mac = ap_mac
        self.essid = essid
        self.key = key
        self.on_remote = on_remote
    def __str__(self):
        return u'{}::{}::{}'.format(self.ap_mac, self.essid, self.key)
    def __eq__(self, n):
        return self.ap_mac == n.ap_mac and self.essid == n.essid and self.key == n.key and self.on_remote == n.on_remote
    def __ne__(self, n):
        return not self == n


def update_local():
    remote = remote_db()
    for remote_net in remote.find(Network):
        if remote_net.ap_mac.startswith('_'):
            local_net = local_db.find(Network, essid=remote_net.essid, key=remote_net.key).one()
            if local_net and not local_net.ap_mac.startswith('_'):
                logging.info(u'Updating MAC address of %s with local data', local_net)
                remote_net.ap_mac = local_net.ap_mac
                remote.commit()

        local_net = local_db.get(Network, remote_net.ap_mac)
        if local_net and local_net != remote_net:
            logging.warn(u'Overriding local %s with remote data', local_net)
            local_net.ap_mac = remote_net.ap_mac
            local_net.essid = remote_net.essid
            local_net.key = remote_net.key
            local_net.on_remote = True
        elif not local_net:
            logging.info(u'Retrieved %s from remote database', remote_net)
            local_net = Network(remote_net.ap_mac, remote_net.essid, remote_net.key, True)
            local_db.add(local_net)
    local_db.commit()
    remote.close()
