
import curses
import sys
import traceback
import os

from .base import UIBase

class UI(UIBase):

    def __init__(self):
        self.win = None
        self.net = None
        self.db = None
        self._run = True
        self._chats = []
        self.line = ""
        self.chatwin = None
        self._currentPeer = None
        UIBase.__init__(self)

    def _setCurrentPeer(self, line):
        self.inform("using peer {}".format(line))
        self._currentPeer = line

    def process_line(self, line):
        command = False
        if line.startswith(":"):
            line = line[1:]
            command = True
        if command:
            if line == 'q':
                self.quit()
            elif line.startswith('a'):
                line = line[1:].strip()
                self._setCurrentPeer(line)
            else:
                self.inform("no such command")
        else:
            if self._currentPeer:
                try:
                    self.net.sendChatTo(self._currentPeer, line)
                    self.inform("")
                except Exception as ex:
                    self.inform("error: {}".format(ex))
            else:
                self.inform("no current peer selected, use :p pubkeygoeshere")


   

    def _displayChats(self):
        self.chatwin.clear()
        self.chatwin.move(1,1)
        for chat in self._chats:
            self.chatwin.addstr(chat.strip())
            self.chatwin.addstr("\n")
        self.chatwin.refresh()

    def _showBanner(self):
        self.inform("your address is {}".format(self.net.lokiaddr))

    def run(self):
        self.win = curses.initscr()
        self.chatwin = self.win.subwin(3, 1)
        curses.raw()
        curses.noecho()
        self.register_fd(sys.stdin.fileno())
        try:
            self._showBanner()
            self.loop()
        except:
            self.win = None
            curses.endwin()
            traceback.print_exc()

    def afterLoop(self):
        self._displayChats()
        self.win.refresh()

    def println(self, line):
        self._chats.append(line.strip())
            
    def reload(self, *args):
        curses.update_lines_cols()
        curses.resizeterm(curses.LINES, curses.COLS)

    def handle_read(self, fd):
        k = self.win.getkey(1,1)
        if k == '\n':
            self.process_line(self.line)
            self.line = ""
            self.win.deleteln()
            self.win.move(1,1)
            self.win.refresh()
        elif ord(k) == 127:
            l = len(self.line)
            if l:
                self.line = self.line[:l-1]
                self.win.delch()
        else:
            self.line += k
            self.win.addstr(self.line)

    def __del__(self):
        if self.win:
            curses.endwin()