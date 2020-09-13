

from .base import UIBase

import socket 

class UI(UIBase):

    def __init__(self):
        UIBase.__init__(self)
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind(("127.0.0.1", 6667))
        self._server.listen(5)
