# -*- coding: utf-8 -*-
from logger import getLogger
from message import Message
log = getLogger("cmdhandler")

class Command(object):
    def __init__(self, msg):
        self.msg = msg
        args = msg.args
        args[0] = args[0][1:]
        if len(args) > 0:
            self.name = args[0].lower()
            self.args = args[1:]
        else:
            self.args = []
            self.name = ''

    def __str__(self):
        return "Command: {} args:{} ".format(self.name, self.args)

class CommandHandler(object):
    instance = None
    def __init__(self):
        if CommandHandler.instance is not None:
           raise Exception("Too many command handlers.")

        CommandHandler.instance = self
        self.cmds = {}

    def add(self, name, call):
        name = name.lower()
        if name in self.cmds:
            log.warn("Command(" + name + ")already exist. Ignoring.")
            return

        self.cmds[name] = call
        log.info("Added command: " + name)

    def remove(self, name):
        name = name.lower()
        try:
            del(self.cmds[name])
            log.info("Removed command: " + name)
        except KeyError:
            log.warn("Could not remove nonexisting command " + name + ".")

    def isCommand(self, msg):
        if len(msg.args) < 1 or len(msg.args[0]) < 1:
            return False
        return msg.args[0][0] == '@'

    def execute(self, msg):
        cmd = Command(msg)
        try:
            if cmd.name in self.cmds:
                self.cmds[cmd.name](cmd)
        except Exception as e:
            log.error("Command(" + cmd.name + ") threw an exception.")
            log.error("... " + repr(e))

def getHandler():
    if CommandHandler.instance is not None:
        return CommandHandler.instance
    else:
        return CommandHandler()
