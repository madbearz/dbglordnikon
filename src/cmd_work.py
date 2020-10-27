# -*- coding: utf-8 -*- 
import cmds
import comm
from urllib.request import urlopen
import re
import json
import requests
from logger import getLogger
defaults = {}
log = getLogger("cmd_work")

from datetime import datetime, timedelta
from cmd_time import delta_hour_minute_str

def work(cmd):
    time = None
    try:
        time = defaults[cmd.msg.nick]
        delta = datetime.now() - time
        cmd.msg.reply_channel("Timer stopped:{}".format(delta_hour_minute_str(delta)))
        del defaults[cmd.msg.nick]
    except:
        pass

    if cmd.name == "offwork":
        return

    defaults[cmd.msg.nick] = datetime.now()
    cmd.msg.reply_channel("Timer started")

cmds.getHandler().add("work", work)
cmds.getHandler().add("offwork", work)

