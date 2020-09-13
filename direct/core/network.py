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
        self._lmq.add_request_command("direct", "chat", self._on_chat)

        self._lmq.start()
        self._conns = dict()
        self._writefd = None

    def set_writer(self, fd):
        self._writefd = fd



    def _on_chat(self, data):
        for d in data:
            self._writeUI("(them) {}".format(d))
        return "OK"

    def _getConn(self, to, port):
        if to in self._conns:
            return self._conns[to]
        host = socket.gethostbyname("{}.loki".format(to))
        conn = self._lmq.connect_remote("tcp://{}:{}".format(host, port))
        self._conns[to] = conn
        return conn

    def _writeUI(self, msg):
        self._writefd.write("{}\n".format(msg))
        self._writefd.flush()

    def sendChatTo(self, to, data, port=DEFAULT_PORT):
        """
        send chat to remote
        """
        self._writeUI("(you) {}".format(data))
        conn = self._getConn(to, port)
        def send():
            self._lmq.request(conn, "direct.chat", [data.encode('utf-8')], timeout=5)
        self._lmq.call_soon(send, None)
        