

from .base import UIBase

import os
import socket 
import binascii

# i don't like regular expressions
import re

# -- begin lameass regexp block

_RE_CHARS = 'a-zA-Z0-9\.\\|\\-_~\\[\\]'
_CHAN_PREFIX = '&#+'
_RE_CHAN_PREFIX = '[%s]' % _CHAN_PREFIX
_RE_CHAN = '%s+[%s]+' % (_RE_CHAN_PREFIX, _RE_CHARS)
_RE_NICK = '[%s]+' % _RE_CHARS
_RE_SRC = '[%s]+![~%s]+@[%s]+' % ( (_RE_CHARS, ) * 3)
_RE_CMD = '[A-Z]+'
_RE_URCLINE = '^:(%s) (%s) ?(%s|%s)? ?:(.+)$' % (_RE_SRC, _RE_CMD, _RE_CHAN, _RE_NICK)

_RE_SRC_CMD = '([%s]+)!([~%s]+)@([%s]+)' % ( ( _RE_CHARS, ) * 3 )
_RE_NICK_CMD = '^NICK :?(%s)' % _RE_NICK
_RE_USER_CMD = '^USER (%s) [%s\\*]+ [%s\\*]+\s:?%s' % ( _RE_NICK, _RE_CHARS, _RE_CHARS, _RE_NICK )
_RE_PRIVMSG_CMD = '^PRIVMSG (%s|%s) :?(.+)$' % (_RE_NICK, _RE_CHAN)
_RE_JOIN_CMD = '^JOIN (%s)' % _RE_CHAN
_RE_JOIN_MULTI_CMD = '^JOIN :?(.+)'
_RE_PART_CMD = '^PART (%s) :?(.+)$' % _RE_CHAN
_RE_PART_SIMPLE_CMD = '^PART (%s)$' % _RE_CHAN
_RE_TOPIC_CMD = '^TOPIC (%s) :?(.+)$' % _RE_CHAN
_RE_QUIT_CMD = '^QUIT (.+)$'
_RE_LIST_CMD = '^(LIST)'
_RE_PING_CMD = '^PING (.*)$'
_RE_PONG_CMD = '^PONG (.*)$'
_RE_MODE_CMD = '^MODE (%s)?\\s(\\w+)$' % _RE_CHAN
_RE_WHO_CMD = '^WHO (%s)$' % _RE_CHAN
_RE_AWAY_ON_CMD = '^AWAY (.+)$'
_RE_AWAY_OFF_CMD = '^(AWAY) ?$'
# -- end lameass regexp block

def irc_greet(serv, nick, user, motd):
    """
    generate an irc greeting for a new user
    yield lines to send
    """
    for num , msg in (
            ('001', ':{}'.format(serv)),
            ('002', ':{}!{}@{}'.format(nick,user,serv)),
            ('003', ':{}'.format(serv)),
            ('004', '{} 0.0 :+'.format(serv)),
            ('005', 'NETWORK={} CHANTYPES=#&!+ CASEMAPPING=utf-8 '.format(serv)+
             'CHANLIMIT=25 NICKLEN=25 TOPICLEN=128 CHANNELLEN=16 COLOUR=1 UNICODE=1 PRESENCE=0:')):
        yield ':{} {} {} {}\n'.format(serv, num, nick, msg)
    yield ':{} 254 {} 25 :CHANNEL(s)\n'.format(serv, nick)
    yield ':{}!{}@{} MODE {} +i\n'.format(nick, user, serv, nick)
    yield ':{} 376 {} :- {} MOTD -\n'.format(serv, nick, serv)
    for line in motd:
        yield ':{} 372 {} :- {}\n'.format(serv, nick, line)
    yield ':{} 376 {} :RPL_ENDOFMOTD\n'.format(serv, nick)

def _irc_re_parse(regex, line, upper=True):
    if upper:
        line = line.upper()
    m = re.match(regex, line)
    if m:
        return m.groups()

irc_parse_away_on = lambda line : _irc_re_parse(_RE_AWAY_ON_CMD, line)
irc_parse_away_off = lambda line : _irc_re_parse(_RE_AWAY_OFF_CMD, line)
irc_parse_nick_user_serv = lambda line : _irc_re_parse(_RE_SRC_CMD, line)
irc_parse_channel_name = lambda line : _irc_re_parse(_RE_CHAN, line)
irc_parse_nick = lambda line : _irc_re_parse(_RE_NICK_CMD, line)
irc_parse_user = lambda line : _irc_re_parse(_RE_USER_CMD, line)
irc_parse_privmsg = lambda line : _irc_re_parse(_RE_PRIVMSG_CMD, line, False)
irc_parse_join = lambda line : _irc_re_parse(_RE_JOIN_CMD, line)
irc_parse_multi_join = lambda line : _irc_re_parse(_RE_JOIN_MULTI_CMD, line)
irc_parse_part = lambda line : _irc_re_parse(_RE_PART_CMD, line)
irc_parse_part_simple = lambda line : _irc_re_parse(_RE_PART_SIMPLE_CMD, line)
irc_parse_quit = lambda line : _irc_re_parse(_RE_QUIT_CMD, line)
irc_parse_ping = lambda line : _irc_re_parse(_RE_PING_CMD, line, False)
irc_parse_pong = lambda line : _irc_re_parse(_RE_PONG_CMD, line, False)
irc_parse_list = lambda line : _irc_re_parse(_RE_LIST_CMD, line)
irc_parse_mode = lambda line : _irc_re_parse(_RE_MODE_CMD, line)
irc_parse_who = lambda line : _irc_re_parse(_RE_WHO_CMD, line)
irc_parse_topic = lambda line : _irc_re_parse(_RE_TOPIC_CMD, line)

class UI(UIBase):

    def __init__(self):
        UIBase.__init__(self)
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 6667))
        self._server.listen(5)
        self._sockets = dict()
        self._irc_sockets = list()
        self.register_fd(self._server)

    def run(self):
        self.loop()

    def myname(self):
        return self.net.name()

    def handle_read(self, fd):
        if fd == self._server.fileno():
            sock, _ = self._server.accept()
            self.register_fd(sock)
            self._sockets[sock.fileno()] = {"socket": sock}
        else:
            sock = self._sockets[fd]['socket']
            if 'file' not in self._sockets[fd]:
                self._sockets[fd]['file'] = sock.makefile()
            line = self._sockets[fd]['file'].readline()
            print(fd, line)
            ping = irc_parse_ping(line)
            if ping:
                sock.send(':lokinet PONG :{}\n'.format(ping[0]).encode('utf-8'))
            if irc_parse_quit(line):
                sock.close()
                self.unregister_fd(fd)
                if fd in self._irc_sockets:
                    self._irc_sockets.remove(fd)
            if fd in self._irc_sockets:
                to, msg = irc_parse_privmsg(line) or (None, None)
                print(to, msg)
                if to:
                    if to == self.net.channel:
                        if msg.startswith(":a"):
                            dst = msg[3:]
                            self.net.sendChatTo(dst, "online")
                            self.inform(":lokinet NOTICE {} :connecting to {}".format(self.net.channel, dst))
                        return
                    toaddr = self.net.getAddrForName(to)
                    if toaddr:
                        self.net.sendChatTo(toaddr, msg)
                    else:
                        self.inform(':lokinet PRIVMSG {} :name not found'.format(self.net.channel))
            elif fd in self._sockets:
                state = self._sockets[fd]
                if 'nick' not in state:
                    state['nick'] = irc_parse_nick(line)
                if 'user' not in state:
                    state['user'] = irc_parse_user(line)
                if 'nick' in state and 'user' in state:
                    for line in irc_greet("lokinet", state['nick'], state['user'], ["lol"]):
                        sock.send(line.encode('ascii'))
                    sock.send(':{}!{}@localhost NICK :{}\n'.format(state['nick'], state['user'], self.myname().split("!")[0]).encode('utf-8'))
                    sock.send(':{} JOIN :{}\n'.format(self.myname(), self.net.channel).encode('utf-8'))
                    self._irc_sockets.append(fd)

    def println(self, line):
        for fd in self._irc_sockets:
            sock = self._sockets[fd]['socket']
            sock.send(line.encode('utf-8'))
