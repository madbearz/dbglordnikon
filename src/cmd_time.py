# -*- coding: utf-8 -*- 
import cmds
import comm

from logger import getLogger
log = getLogger("cmd_work")

from datetime import datetime, timedelta
from geopy import geocoders
from tzwhere import tzwhere
from pytz import timezone

def time_from_string(location):
    loc, (lat, lng) = geocoders.Nominatim(user_agent='dbglordnikon').geocode(location)
    tz_s = tzwhere.tzwhere().tzNameAt(lat, lng)
    tz = timezone(tz_s)
    return datetime.now(tz)

def delta_hour_minute_str(d):
    h, remainder = divmod(d.total_seconds(), 3600)
    m, s = divmod(remainder, 60)
    return "%s:%s" % (h, m)

def hour_minute_str(t):
    return "{}:{}".format(t.hour, t.minute)


def time_in(cmd):
    if len(cmd.args) == 0:
        return
    loc = cmd.args[0]
    time = hour_minute_str(time_from_string(loc))
    cmd.msg.reply_channel("time in {}: {}".format(cmd.args[0], time))

