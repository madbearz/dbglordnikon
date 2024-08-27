# -*- coding: utf-8 -*-
#! /usr/bin/python
from message import Message
import logger
import irc
import re
import socket
import json
from time import time, sleep
from select import select
import cmds
import comm
import listeners
import datetime
import cmd_temp
import cmd_work

import listener_title
import listener_logger
import listener_first_last
from listener_first_last import get_date

log = logger.getLogger("dbglordnikon")
import config



class DbgLordNikon(irc.Bot):
    def __init__(self):
        self.conf = config.get_bot_config()
        irc.Bot.__init__(self, self.conf.get('bot', 'nick'))
        self.timeout = int(self.conf.get('bot', 'ping_timeout'))
        self.ignoreList = self.conf.get('bot', 'ignore')

        self.addMessageHandler(Message.MESSAGE, DbgLordNikon.handlePrivMsg)
        self.addMessageHandler(Message.JOIN, DbgLordNikon.handlePrivMsg)
        self.addMessageHandler("376", DbgLordNikon.handleConnected)
        self.addMessageHandler(Message.NOTICE, DbgLordNikon.handleNotice)
        self.connect(self.conf.get('bot', 'server'), int(self.conf.get('bot','port')))

        self.cmdHandler = cmds.getHandler()
        self.queue = comm.getHandler()
        self.listeners = listeners.getHandler()

        self.sendAuth()


    """ sendAuth
        sends auth to nickserv and will let handle notice
        call joinChannels, if there is configured auth joinChannels
        will be called immediately
    """
    def sendAuth(self):
        self.auth = None
        try:
            self.auth = self.conf.get('bot', 'auth')
        except:
            self.auth = None
        if self.auth is not None:
            m = Message()
            m.nick = 'NickServ'
            m.reply_private("identify {}".format(self.auth))

        else:
            self.joinChannels()

    def handleNotice(self, msg):
        try:
            log.critical(msg)
            if "You are now identi" in msg.line:
                self.joinChannels()
        except AttributeError:
            pass

    def joinChannels(self):
        try:
            for c in self.conf.get('bot', 'channels').split(','):
                self.addChannel(c)
        except AttributeError:
            pass


    def handleConnected(self, msg):
        pass
    def handleDayChange(self, msg):
        self.listeners.run(msg)

    def handlePrivMsg(self, msg):
        if msg.type == Message.MESSAGE and msg.nick not in self.ignoreList:
            if self.cmdHandler.isCommand(msg):
                self.cmdHandler.execute(msg)
        self.listeners.run(msg)

    def registerCommand(self, cmd):
        if cmd.name in self.commands:
            log.error("Multiple commands with same name(" + cmd.name + "). Skipping.")
            return

        self.commands[cmd.name] = cmd

    def run(self):

        nextTick = time() + self.timeout
        curr_date = get_date()

        while self.state > 0:
            tickTime = nextTick - time()
            if tickTime < 0:
                tickTime = 0
            r,w,x = select([self.sock],[],[self.sock], tickTime)

            if len(x):
                self.disconnect()
                self.connect(self.conf.get('bot','server'), self.conf.get('bot','port'))
                continue
            if len(r):
                try:
                    msg = self.getMessage()
                    self.handleMessage(msg)
                except socket.error as e:
                    log.error("Error essage handling: " + str(e))

            # messages to send
            msg = self.queue.get()
            if msg is not None:
                self.send(msg)
                msg = self.queue.get()
                while msg is not None:
                    sleep(1)
                    self.send(msg)
                    msg = self.queue.get()

            if time() > nextTick:
                if (time() - self.lastSend) > float(self.timeout):
                    if self.state != 1:
                        log.info("RECON")
                        self.disconnect()
                        sleep(30)
                        self.connect(self.conf.get('bot', 'server'), int(self.conf.get('bot','port')))
                        self.sendAuth()

                nextTick = nextTick + self.timeout

            now = get_date()
            if curr_date is not now:
                curr_date = now
                m = Message(m_type=Message.DAY_CHANGE)
                self.listeners.run(m)

if __name__ == "__main__":
    bot = DbgLordNikon()
    bot.run()
