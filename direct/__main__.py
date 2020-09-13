#!/usr/bin/env python3.8

from direct.core import config, contacts, network
from direct.ui.irc import UI
import signal

cfg = config.Load()
netcore = network.NetCore(config=cfg)
db = contacts.DB(config=cfg)

ui = UI()
ui.addNet(netcore)
ui.loadFriends(db)

signal.signal(signal.SIGINT, lambda x : ui.quit())
signal.signal(signal.SIGTERM, lambda x : ui.quit())

ui.run()