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
        self.channel = "$control"

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
                    self._writeUI(d, src='{}!user@{}'.format(self._names[addr]+"|"+addr[:4], addr), dst=self.name())
        return "OK"


    def getAddrForName(self, name):
        """
        get loki address for an ircname
        """
        parts = name.split("|")
        if len(parts) != 2:
            return
        for addr, name in self._names.items():
            if addr.startswith(parts[1]) and name == parts[0]:
                return addr
    
    def name(self):
        addr = self.lokiaddr
        return '{}!user@{}'.format(self.myname+"|"+addr[:4], addr)

    def _getConn(self, to, port):
        def send():
            name = self._lmq.request(conn, "direct.online", [self.myname.encode("utf-8")], timeout=5)
            name = name[0].decode('utf-8')
            self._names[to] = name
        if to in self._conns:
            self._lmq.call_soon(send, None)
            return self._conns[to]
        host = socket.gethostbyname(to)
        conn = self._lmq.connect_remote("tcp://{}:{}".format(host, port))
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
        def send():
            conn = self._getConn(to, port)
            self._lmq.request(conn, "direct.{}".format(type), [data.encode('utf-8')], timeout=5)
        self._lmq.call_soon(send, None)
        