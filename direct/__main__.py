#!/usr/bin/env python3.8

from direct.core import config, contacts, network
from direct.ui import panes

cfg = config.Load()
netcore = network.NetCore(config=cfg)
db = contacts.DB(config=cfg)

ui = panes.UI()
ui.addNet(netcore)
ui.loadFriends(db)

ui.run()