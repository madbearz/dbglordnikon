import socket
from logger import getLogger
from time import time
from message import Message

IRC_MAX_MSG_LEN = 512

log = getLogger("irc")


class Bot:
  def __init__(self, nick, host = None, port = 6667):
    self.nick = nick
    self.host = host
    log.debug("nick:{}".format(nick))
    self.port = port
    self.state = 0
    self.sock = None
    self.server = None
    self.messages = ""
    self.handlers = {Message.CONNECTED: Bot.messageConnected,
                     Message.NICK_IN_USE: Bot.messageNickInUse,
                     Message.PING : Bot.messagePing,  Message.NOTICE : Bot.messageNotice}
    self.channels = []
    self.lastSend = 0

  def connect(self, host = None, port = None):
    if self.server:
      raise Exception('Already connected to ' + self.server)
    if host:
      self.host = host
    elif not self.host:
      raise Exception('No host specified')
    if port:
      self.port = port
    log.info("Connecting...")
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((self.host, self.port))
    line = self.getRawMessage()
    log.info("Contact!")
    while ":*** Looking up your hostname..." in line:
      log.info("MEPP: " +line)
      line = self.getRawMessage()
    log.info("Greeting and awating response...")
    self.sock.send("NICK {}\r\nUSER {} I IS BOT\r\n".format(self.nick,
                                                            self.nick).encode('utf-8'))
    self.state = 1

  def disconnect(self):
    self.sock.close()
    self.sock = None
    self.server = None
    self.state = 0

  def decode(self,text):
    for enc in ('utf-8','iso-8859-1', 'cp1252'):
        try:
            return text.decode(enc)
        except UnicodeDecodeError:
            continue

  def getRawMessage(self):
    while self.messages.find("\r\n") == -1:
      if len(self.messages) > 4096:
        raise Exception('Too long message!')
      self.messages = self.messages + self.decode(self.sock.recv(4096))
    ret, self.messages = self.messages.split("\r\n", 1)
    return ret

  def createMessage(self, data):
    return Message(data)

  def getMessage(self):
    return self.createMessage(self.getRawMessage())

  def send(self, msg):
    self.lastSend = time()
    line = ""
    if msg.type == Message.MESSAGE:
        line = "PRIVMSG {} :{}\r\n".format(msg.channel, msg.line)
    elif msg.type == Message.JOIN:
        line = "JOIN {}{}".format(msg.channel,"\r\n")
    elif msg.type == Message.PONG:
        line = "PONG {}{}".format(msg.line,"\r\n")

    line = line[:IRC_MAX_MSG_LEN]
    self.sock.send(line.encode('utf-8'))

  def addMessageHandler(self, msgType, handler):
    log.info("New message handler for: {}".format(msgType))
    self.handlers[msgType] = handler

  def handleMessage(self, msg):
    try:
      self.handlers[msg.type](self, msg)
    except KeyError:
      pass

  def messageConnected(self, msg):
    self.server = msg.sender
    self.state = 2
    for ch in self.channels:
      self.send(Message(data=None,channel=ch, m_type=Message.JOIN))

  def messageNotice(self, msg):
    pass

  def messageNickInUse(self, msg):
    self.nick = self.nick + "_"
    self.send(Message(nick=self.nick, m_type=Message.NICK))

  def addChannel(self, channel):
    self.channels.append(channel)
    if self.state == 2:
      self.send(Message(channel=channel, m_type=Message.JOIN))

  def messagePing(self, msg):
    self.send(Message(m_type=Message.PONG, text=msg.args[0]))

