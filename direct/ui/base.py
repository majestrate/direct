

from select import poll, POLLIN
import os

class UIBase:

    def __init__(self):
        self._chat_read, self._chat_write = os.pipe()
        self._chat_reader = os.fdopen(self._chat_read, mode='r')
        self._chat_writer = os.fdopen(self._chat_write, mode='w')
        self._poll = poll()
        self._run = True
        self.register_fd(self._chat_read)
        self.db = None

    def quit(self):
        self.inform("quitting...")
        self._run = False

    def register_fd(self, fd):
        self._poll.register(fd, POLLIN)

    def addNet(self, net):
        self.net = net
        self.net.set_writer(self._chat_writer)

    def inform(self, msg):
        msg += "\n"
        self._chat_writer.write(msg)
        self._chat_writer.flush()

    def println(self, msg):
        raise NotImplementedError()

    def handle_read(self, fd):
        raise NotImplementedError()

    def loadFriends(self, db):
        self.db = db

    def afterLoop(self):
        pass

    def run(self):
        raise NotImplementedError()

    def loop(self):
        while self._run:
            evs = self._poll.poll()
            for fd, _ in evs:
                if fd == self._chat_read:
                    line = self._chat_reader.readline()
                    self.println(line)
                else:
                    self.handle_read(fd)
            self.afterLoop()