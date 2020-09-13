
import curses
import sys
import traceback
import os
from select import poll, POLLIN

class UI:

    def __init__(self):
        self.win = None
        self.net = None
        self.db = None
        self._run = True
        self._chats = []
        self._chat = b''
        self.chatwin = None
        self._currentPeer = None
        self._chat_read, self._chat_write = os.pipe()
        self._chat_reader = os.fdopen(self._chat_read, mode='r')
        self._chat_writer = os.fdopen(self._chat_write, mode='w')


    def addNet(self, net):
        self.net = net
        self.net.set_writer(self._chat_writer)

    def loadFriends(self, db):
        self.db = db


    def quit(self):
        self._run = False

    def _setCurrentPeer(self, line):
        self._inform("using peer {}".format(line))
        self._currentPeer = line

    def process_line(self, line):
        command = False
        if line.startswith(":"):
            line = line[1:]
            command = True
        if command:
            if line == 'q':
                self.quit()
            elif line.startswith('c'):
                line = line[1:].strip()
                self.net.sendChatTo(line, "", type="online")
            elif line.startswith('p'):
                line = line[1:].strip()
                self._setCurrentPeer(line)
            else:
                self._inform("no such command")
        else:
            if self._currentPeer:
                try:
                    self.net.sendChatTo(self._currentPeer, line)
                    self._inform("")
                except Exception as ex:
                    self._inform("error: {}".format(ex))
            else:
                self._inform("no current peer selected, use :p pubkeygoeshere")


    def _inform(self, msg):
        msg += "\n"
        self._chat_writer.write(msg)
        self._chat_writer.flush()

    def _displayChats(self):
        self.chatwin.clear()
        for chat in self._chats:
            self.chatwin.addstr(chat.strip())
            self.chatwin.addstr("\n")
        self.chatwin.refresh()

    def _showBanner(self):
        self._inform("your address is {}".format(self.net.lokiaddr))

    def run(self):
        curses.initscr()
        self.win = curses.newwin(3, 80)
        self.chatwin = curses.newwin(24, 80, 4, 0)
        try:
            self.repl()
        except:
            self.win = None
            curses.endwin()
            traceback.print_exc()

    def _updateChats(self):
        chat = self._chat_reader.readline()
        self._chats.append(chat.strip())
            

    def repl(self):
        line = ""
        stdin = sys.stdin.fileno()
        p = poll()
        p.register(stdin, POLLIN)
        p.register(self._chat_read, POLLIN)
        self.win.clear()
        self._showBanner()
        self.win.refresh()
        while self._run:
            evs = p.poll(100)
            for fd, ev in evs:
                if ev != POLLIN:
                    raise Exception()
                if fd == self._chat_read:
                    self._updateChats()
                elif fd == stdin:
                    k = self.win.getkey(1, 0)
                    if k == '\n':
                        self.process_line(line)
                        line = ""
                        self.win.refresh()
                    elif ord(k) == 127:
                        l = len(line)
                        if l:
                            line = line[:l-1]
                        self.win.deleteln()
                        self.win.addstr(line)
                    else:
                        line += k
                        self.win.deleteln()
                        self.win.addstr(line)
            
            self._displayChats()
            self.win.refresh()

    def __del__(self):
        if self.win:
            curses.endwin()