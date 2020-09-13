"""
networking core
"""
from pylokimq import LokiMQ
import socket
import os

DEFAULT_PORT = 6600

class NetCore:

    def __init__(self, **kwargs):
        self._lmq = LokiMQ()
        host = socket.gethostbyname("localhost.loki")
        self.lokiaddr = socket.getnameinfo((host, DEFAULT_PORT), socket.AF_INET)[0]
        addr = "tcp://{}:{}/".format(host, DEFAULT_PORT)
        print("Binding network at {} as {}".format(addr, self.lokiaddr))
        self._lmq.listen_plain(addr)
        self._lmq.add_anonymous_category("direct")
        self._lmq.add_request_command_ex("direct", "chat", self._on_chat)
        self._lmq.add_request_command_ex("direct", "online", self._on_login)
        self._lmq.start()
        self._conns = dict()
        self._names = dict()
        self._writefd = None
        self.myname = (kwargs and 'name' in kwargs) and kwargs['name'] or 'anon'
        self._channel = "#chat"

    def set_writer(self, fd):
        self._writefd = fd

    def _on_login(self, data, remote, connid):
        name = data[0]
        lokiaddr = socket.getnameinfo((remote, DEFAULT_PORT), socket.AF_INET)[0]
        self._writeUI("[new connection] {} / {}".format(name, lokiaddr))
        self._conns[lokiaddr] = connid
        self._names[lokiaddr] = name
        return self.myname

    def _on_chat(self, data, remote, connid):
        for addr, c in self._conns.items():
            if c == connid:
                for d in data:
                    self._writeUI(d, src='{}!user@{}'.format(self._names[addr], addr), dst=self._channel)
        return "OK"

    def _getConn(self, to, port):
        if to in self._conns:
            return self._conns[to]
        host = socket.gethostbyname(to)
        conn = self._lmq.connect_remote("tcp://{}:{}".format(host, port))
        def send():
            self._writeUI("[connecting...]")
            name = self._lmq.request(conn, "direct.online", [self.myname.encode("utf-8")], timeout=5)
            name = name[0].decode('utf-8')
            self._names[to] = name
            self._writeUI(type="JOIN", src=name, dst=self._channel)
        self._lmq.call_soon(send, None)
        self._conns[to] = conn
        return conn

    def _writeUI(self, msg, src="system", dst="you", type="PRIVMSG"):
        self._writefd.write(":{} {} {} :{}\n".format(src, type, dst, msg))
        self._writefd.flush()

    def sendChatTo(self, to, data, port=DEFAULT_PORT, type="chat"):
        """
        send chat to remote
        """
        conn = self._getConn(to, port)
        def send():
            self._lmq.request(conn, "direct.{}".format(type), [data.encode('utf-8')], timeout=5)
        self._lmq.call_soon(send, None)
        