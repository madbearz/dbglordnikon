#-*- coding: utf-8 -*-
import listeners
import comm
import urllib
from bs4 import BeautifulSoup
import logger
import re
import requests
import cmds
import subprocess
import random
import html

log = logger.getLogger("TitleListener")
AUTOTITLE = True

send = comm.getHandler().sendRaw

MAX_LENGTH = 1024*1024*4

autotitles= {}

def autotitle(cmd):
    if 'off' in cmd.msg.line:
        autotitles[cmd.msg.channel] = False
    else:
        autotitles[cmd.msg.channel] = True
    cmd.msg.reply_channel("autotitle:{}".format(autotitles[cmd.msg.channel]))


cmds.getHandler().add("autotitle", autotitle)

def check_len(url):
    response = requests.head(url, timeout=10)
    try:
        cl = response.headers['content-length']
        if int(cl) < MAX_LENGTH:
            return True

    except Exception as e:
        pass

    try:
        if 'html' in response.headers['Content-Type']:
            return True
    except:
        pass
    return False

def get_title(url):
    agent = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
    if not check_len(url):
        return None
    req = requests.get(url,headers=agent, stream=True, timeout=10)
    regex = re.compile("(.*?<title(.*?)>)(.+?)(</title>.*?)")
    single = re.compile("(.*?<title(.*?)>.*?)|(.+?</title>)")
    i = 0
    had_title = False
    title_line = ""
    for line in req.iter_lines():
        if line:
            try:
                line = line.decode("utf-8").strip()
                if not had_title:
                    m = regex.match(line)
                    if m:
                        return html.unescape(m.group(3))

                sm = single.match(line)
                if sm and not had_title:
                    had_title = True
                    title_line = "{} {}".format(title_line, line)
                    continue

                if had_title:
                    title_line = "{} {}".format(title_line, line)

                if sm and had_title: # had title
                    m = regex.match(title_line.strip())
                    if m:
                        return html.unescape(m.group(2).strip())
                    return None

            except:
                pass
        if i > 300:
            return None
        i = i + 1

    return None

class TitleListener(listeners.RegexListener):
    def __init__(self):
        listeners.RegexListener.__init__(self, "title","http.?:([^\s]+)\.([a-z]{1,3})(\/?[^\s]+)")
        self.sendTo = comm.getHandler().sendTo
        self.send = comm.getHandler().sendRaw

    def execute(self,msg):
        global AUTOTITLE
        if msg.channel in autotitles:
            if not autotitles[msg.channel]:
                return

        if "localhost" in msg.line or "127.0" in msg.line:
            return

        for arg in msg.args:
            match = self.regex.match(arg)
            if match:
                u = match.group(0)
                try:
                    r = get_title(u)
                    if AUTOTITLE and r:
                        msg.reply_channel("title: " + r)

                except Exception as e:
                    print(e)


listeners.getHandler().add(TitleListener())
