
# read a freakin config
import configparser
import logger
log = logger.getLogger("conf")


class BotConf(configparser.ConfigParser):
    instance = None
    def __init__(self):
        if BotConf.instance is not None:
            raise Exception("To many configs around")
        BotConf.instance = self
        configparser.ConfigParser.__init__(self)
        self.read("bot.conf")


def get_bot_config():
    if BotConf.instance is not None:
        return BotConf.instance
    return BotConf()

def debug():
    try:
        return get_bot_config().getboolean("bot", "debug")
    except:
        return False

DEBUG = debug()
