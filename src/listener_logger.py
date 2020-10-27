import listeners
from listeners import *
import comm
from datetime import *
import sqlite3
import sys
import logger
from message import Message
log = logger.getLogger("logger_listener")

import cmds

class LoggerListener(Listener):
    def __init__(self):
        Listener.__init__(self,"dblogger")
        self.sendTo = comm.getHandler().sendTo

        self._db = 'test.db'
        self._connection = sqlite3.connect(self._db)
        self._cursor = self._connection.cursor()

        self._cursor.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY AUTOINCREMENT, nick varchar(255));')
        self._cursor.execute('CREATE TABLE IF NOT EXISTS channels(channel_id INTEGER PRIMARY KEY AUTOINCREMENT, channel varchar(255));')
        self._cursor.execute('CREATE TABLE IF NOT EXISTS lines(line_id INTEGER PRIMARY KEY AUTOINCREMENT , text VARCHAR(1024), time DATETIME , channel_id, user_id , FOREIGN KEY (channel_id) REFERENCES channels(channel_id), FOREIGN KEY (user_id) REFERENCES users(user_id));')
        self._connection.commit()

    def compare(self, msg):
        if msg.type == Message.MESSAGE:
            return True
        return False

    def has_table(self, table):
        r = self._cursor.execute("select 1 from sqlite_master where type='table' and name='"+ table + "';");
        if self._cursor.fetchone() == None:
            return False
        return True

    def has_val(self,table,field,val):
        self._cursor.execute('SELECT * FROM ' + table +' WHERE ' + field + ' = ?', [val])
        if self._cursor.fetchone()  == None:
            return False
        return True

    def insert_line(self, msg):
        if msg.type != Message.MESSAGE:
            return
        if not self.has_val('channels', 'channel', msg.channel):
            self._cursor.execute('INSERT INTO channels values (?,?)', (None, msg.channel))
            self._connection.commit()
        if not self.has_val('users', 'nick', msg.nick):
            self._cursor.execute('INSERT INTO users values (?,?)', (None, msg.nick))
            self._connection.commit()
        text = msg.line

        self._cursor.execute('SELECT user_id FROM users WHERE nick = ?;', [msg.nick])
        uid = self._cursor.fetchone()[0]
        self._cursor.execute('SELECT channel_id FROM channels WHERE channel = ?;', [msg.channel])
        cid = self._cursor.fetchone()[0]

        self._cursor.execute("INSERT INTO lines VALUES (?,?,?,?,?)", (None,text, datetime.now(),  cid, uid, ))

        self._connection.commit()

    def execute(self, msg):
        if msg.channel != None: # jsut feck
            if not self.has_table('lines'):
                pass
            self.insert_line(msg)

listeners.getHandler().add(LoggerListener())

if __name__ == "__main__":
    l = LoggerListener()
