#!/usr/bin/env python3.8

from direct.core import config, contacts, network
from direct.ui.panes import UI

cfg = config.Load()
netcore = network.NetCore(config=cfg)
db = contacts.DB(config=cfg)

ui = UI()
ui.addNet(netcore)
ui.loadFriends(db)

ui.run()