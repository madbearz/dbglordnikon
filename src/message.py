# -*- coding: utf-8 -*- 
import comm
import config
import datetime
import logger
import copy
log = logger.getLogger("message")

def create_message(msg_type):
    m = Message("{} INTERNAL".format(msg_type))
    m.type = Message.DAY_CHANGE
    return m


class Message(object):
    MESSAGE = 0
    PRIVMESSAGE = 1
    MIDNIGHT = 2
    DAY_CHANGE = 3
    PING = 4
    JOIN = 5
    PONG = 6
    NICK = 7
    CONNECTED = 8
    NICK_IN_USE = 9
    NOTICE = 10
    MINUTE_CHANGE = 11

    def __init__(self, data=None, channel=None, text=None, nick=None,
                 m_type=MESSAGE):
        self.type = m_type
        self.date = datetime.datetime.now()
        self.nick = nick
        self.args = []
        if data is not None:
            self.initWithData(data)
        else:
            self.channel = channel
            self.line = text
            self.nick = nick
            self.server_date = datetime.datetime.today()


    def initWithData(self, data):
        self.raw = data
        if data[0] == ':':
            prefix, data = data[1:].split(' ', 1)
            self.sender = prefix
            try:
                self.nick, rest = prefix.split('!')
                self.full = rest
                self.user, self.host = rest.split('@')
            except ValueError:
                self.nick = self.user = self.host = ""
            data = data.strip()
        else:
            self.prefix = ""

        self.type, data = data.split(' ', 1)
        data = data.strip()
        self.channel = ""
        self.args = []
        self.line = ""
        self.server_date = datetime.datetime.today()

        if self.type == ".DAY_CHANGE":
            return

        if self.type == "JOIN":
            self.channel = data.split(' ', 0)[0].replace(":", "")
            args = ''
            trailing = ''
            self.type = Message.JOIN

        if self.type == "001":
            self.type = Message.CONNECTED
        if self.type == "433":
            self.type = Message.NICK_IN_USE
        if self.type == "PRIVMSG" or self.type == "PING" or self.type == "NOTICE":
            if self.type == "PRIVMSG":
                self.type = Message.MESSAGE
            elif self.type == "NOTICE":
                self.type = Message.NOTICE
            else:
                self.type = Message.PING
            try:
                self.channel, data = data.split(' ', 1)
                args = []

                if ':' in data[0]:
                    data = data.lstrip(':')
                self.line = data.lstrip()

                data = data.lstrip()
                self.args = data.split(' ')

            except ValueError:
                self.args = data.strip().split()


    def is_private(self):
        return self.channel == config.get_bot_config().get('bot','nick')

    def reply_private(self, text):
        msg = copy.copy(self)
        msg.line = text
        msg.type = Message.MESSAGE
        msg.channel = self.nick
        msg.send()


    def reply_channel(self, text):
        msg = copy.copy(self)
        msg.type = Message.MESSAGE
        msg.line = text
        msg.send()

    def send(self):
        comm.getHandler().sendRaw(self)

    def __str__(self):
        return "{}#{}#{}#{}#{}".format(self.channel, self.nick, self.line,
                                       self.type, self.args)

    def __repr__(self):
        return "<Message(" + "{}#{}#{}".format(self.channel, self.nick, self.line) + ")>"
