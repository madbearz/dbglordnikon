import re
import config
from message import Message
from logger import getLogger

log = getLogger("listener")
self_nick = config.get_bot_config().get('bot', 'nick')

class Listener(object):
  log = log
  def __init__(self, name):
    self.name = name

  def compare(self, msg):
    return False

  def execute(self, msg):
    pass

class ChannelListener(Listener):
    def __init__(self, name, channel):
        Listener.__init(self, name)
        self.channel = channel
    def compare(self, msg):
        if msg.channel == self.channel:
            return True
        return False

class JoinListener(Listener):
    def __init__(self,name):
        Listener.__init__(self, name)
    def compare(self, msg):
        if msg.type == Message.JOIN:
            return True
        return False
    def execute(self, msg):
        pass

class SelfJoinListener(JoinListener):
    def __init__(self, name):
        Listener.__init__(self, name)

    def compare(self, msg):
        global self_nick
        if super(SelfJoinListener, self).compare(msg) and msg.nick == self_nick:
            return True

class TickListener(Listener):
    def __init__(self, name):
        Listener.__init__(self, name)

    def compare(self, msg):
        return False

class MinuteChangeListener(Listener):
    def __init__(self, name):
        Listener.__init__(self, name)
    def compare(self, msg):
        if msg.type == Message.MINUTE_CHANGE:
            return True
        return False
    def execute(self, msg):
        pass

class DayChangeListener(Listener):
    def __init__(self, name):
        Listener.__init__(self, name)
    def compare(self, msg):
        if msg.type == Message.DAY_CHANGE:
            return True
        return False
    def execute(self, msg):
        pass

class RegexListener(Listener):
  def __init__(self, name, regex):
    Listener.__init__(self, name)
    self.regex = re.compile(regex, re.IGNORECASE)
    self.match = None

  def compare(self, msg):
    if msg.type == Message.JOIN or msg.type == Message.DAY_CHANGE or msg.type == Message.PING:
      return False

    s = msg.line
    self.match = self.regex.search(s)
    if self.match:
      return True
    return False

  def execute(self, msg):
    pass

class ListenerHandler(object):
  instance = None
  def __init__(self):
    if ListenerHandler.instance is not None:
      raise Exception("Too many listener handlers")

    self.listeners = {}
    ListenerHandler.instance = self

  def add(self, l):
    if l.name in self.listeners:
      log.warn("Listener " + l.name + " does already exist.")
      return

    self.listeners[l.name] = l
    log.info("Added listener: " + l.name)

  def run(self, msg):
    for l in self.listeners.values():
        if l.compare(msg):
            l.execute(msg)

def getHandler():
  if ListenerHandler.instance is not None:
    return ListenerHandler.instance
  else:
    return ListenerHandler()

