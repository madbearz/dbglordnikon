# -*- coding: utf-8 -*- 
import cmds
import comm
from urllib.request import urlopen
import re
import json
import requests
from logger import getLogger
import config
defaults = []
log = getLogger("cmd_temp")

class TempUser:
    def __init__(self,nick):
        self.locations = {}
        self.nick = nick

    def add_location(self,location):
        if location in self.locations.keys():
            self.locations[location] = self.locations[location] + 1
        else:
            self.locations[location] = 1

    def get_top_location(self):
        loc = None
        val = 0

        if len(self.locations) == 0:
            return False

        for k,v in self.locations.items():
            if v > val:
                loc = k
                val = v
        return loc

def ftoc(cmd):
    if len(cmd.msg.args) > 0:
        f = float(cmd.msg.args[1])
        c = ((f-32.0)*5.0)/9.0
        res = "{}: {}F = {:.2f}C".format(cmd.msg.nick, f, c)
        cmd.msg.reply_channel(res)

def ctof(cmd):
    if len(cmd.msg.args) > 0:
        c = float(cmd.msg.args[1])
        f = ((c*9.0)/5.0)+32
        res = "{}: {}C = {:.2f}F".format(cmd.msg.nick, c, f)
        cmd.msg.reply_channel(res)

def k2c(k):
    return round(k-273.15, 1)

def get_openweather_temp(loc):
    try:
        key = "&appid=" + config.get_bot_config().get('bot', 'openweather_key')
    except:
        return

    code = ""
    if u'ö' in loc or u'ä' in loc or u'å' in loc:
        code = ',se'
    search = loc
    log.warn("IN GET OPEN:{}".format(search))
    url = "http://api.openweathermap.org/data/2.5/weather?q=" + search.lower() + code + key
    u = requests.get(url, timeout=3.0)
    data = u.json()
    try:
        return repr(k2c(data["main"]["temp"])) + ", " + data["weather"][0]["description"]  + ", humidity: " + repr(data["main"]["humidity"]) + "%, wind: " + repr(data["wind"]["speed"]) + "m/s (" + "{0:.2f}".format(data["wind"]["speed"]*3.6) + "km/h), pressure:" + repr(data["main"]["pressure"]) + "hPa"
    except:
        pass

def get_temp(loc):
    search = loc.strip().replace('ä','a').replace('ö','o').replace('å','a')
    u = urlopen("http://www.temperatur.nu/termo/" + search.lower() + "/temp.txt")
    return u.read().strip().decode("utf-8")

def get_user(nick):
    for n in defaults:
        if n.nick == nick:
            return n
    return False

def get_default(nick):
    u = get_user(nick)
    if not u:
        return False
    return u.get_top_location()

def add_default(nick, loc):
    u = get_user(nick)
    if not u:
        u = TempUser(nick)
        u.add_location(loc)
        defaults.append(u)
    else:
        u.add_location(loc)

def temperature(cmd):
    send = comm.getHandler().sendRaw
    if cmd.name == "tempnu":
        temp_func = get_temp
    else:
        temp_func = get_openweather_temp
    loc = None
    ret = None
    if len(cmd.args) == 0:
        loc = get_default(cmd.msg.nick)
        if loc:
            ret = temp_func(loc)
        search = ""
    else:
        search = " ".join(cmd.args).strip()

    if loc or re.match('^[a-zA-ZåäöÅÖÄ0-9\s _,-]+$',search):

        if loc and ret:
            cmd.msg.reply_channel(cmd.msg.nick + ": Temperature in " + loc.strip() + ": " + ret)

        elif ret == "not found":
            cmd.msg.reply_channel(cmd.msg.nick + ": " + search.strip() + " not found.")
        else:
            ret = temp_func(search)
            cmd.msg.reply_channel(cmd.msg.nick + ": Temperature in " + search.strip() + ": " + ret)
            add_default(cmd.msg.nick, search)

cmds.getHandler().add("temp", temperature)
cmds.getHandler().add("weather", temperature)
cmds.getHandler().add("tempnu", temperature)
cmds.getHandler().add("ctof", ctof)
cmds.getHandler().add("ftoc", ftoc)

