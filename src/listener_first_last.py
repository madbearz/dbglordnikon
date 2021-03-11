import listeners
import cmds
import sqlite3
import logger
import comm
from datetime import datetime, timedelta
from message import Message
import config
from enum import Enum, unique
log = logger.getLogger("firstlast")

# everybody who said last for each channel
# store all lasts, u may only use it once per channel and user.
lasts = {}
firsts = []
send = comm.getHandler().sendRaw

conf = config.get_bot_config()


score_fn = conf.get('bot', 'scorefunction', fallback='std')


def sinceMidnight(date):
    midnight = datetime.now().replace(hour=0, minute=0, second = 0)
    return date - midnight

def toMidnight(date):
    midnight = date.replace(hour=0, minute=0, second = 0)
    return midnight - date

@unique
class ScoreType(Enum):
    LAST = 0
    FIRST = 1


def scoreFunction(date, scoreType):
    if score_fn == "std":
        return 1

    if scoreType == ScoreType.LAST:
        delta = toMidnight(date)

    if scoreType == ScoreType.FIRST:
        delta = sinceMidnight(date)

    if score_fn == "seconds":
        return delta.seconds
    if score_fn == "minutes":
        return divmod(delta.seconds, 60)[0]
    if score_fn == "hours":
        return divmod(delta.seconds, 3600)[0]

    return 0


def get_date():
    if config.debug():
        return datetime.today().second
    return datetime.today().day

date = get_date()


def date_check():
    global date
    now = get_date()
    return date != now

def my_score(cmd):
    cmd.msg.reply_channel(cmd.msg.nick + ":  " + str(getScore(cmd.msg.channel, cmd.msg.nick)))

def high_score(cmd):
    scores = getHighScore(cmd.msg.channel)
    rep = ""
    if not scores:
        cmd.msg.reply_private('no score recorded... YET')
    for score in scores:
        if not score:
            continue
        if len(rep) > 0:
            rep = "{},".format(rep)
        rep = "{}{}".format(rep, str(score[0]) + ":" + str(score[1]))
    cmd.msg.reply_private(rep)

def midnightRun():
    global lasts, firsts, date
    for k,v in lasts.items():
        log.critical("k:{} v:{}".format(k, v))
        if len(k) == 0:
            continue
        score = scoreFunction(v[-1].date, ScoreType.LAST)
        addScore(k,v[-1].nick,score)
        t = "and the winner is... {}, you scored: {}".format(v[-1].nick, score)

        msg = Message(data=None,channel=k, text=t,
                      nick="bot",m_type=Message.MESSAGE)
        msg.send()
        render_high_score(k)

    lasts = {}
    firsts = []
    date = get_date()

class MidnightRunListener(listeners.DayChangeListener):
    def __init__(self):
        listeners.DayChangeListener.__init__(self, "midnightrun")
    def execute(self, msg):
        global lasts, send, firsts, date

        if date_check():
            midnightRun()
            date = get_date()
        else:
            pass


class LastListener(listeners.RegexListener):
    def __init__(self):
        listeners.RegexListener.__init__(self, "lastlistener",
                                         u"(?:^|\s)(last|sist)(?:(?=(\?|\.|!|,|\s|$)))")
    def execute(self, msg):
        global lasts

        if date_check():
            midnightRun()

        if not msg.channel in lasts:
            lasts[msg.channel] = []

        if msg.nick in [x.nick for x in lasts[msg.channel]]:
            msg.reply_channel("oh no you didn't...")
        else:
            insert_last(msg)
            lasts[msg.channel].append(msg)


class FirstListener(listeners.RegexListener):
    def __init__(self):
        listeners.RegexListener.__init__(self, "firstlistener",
                                         u"(?:^|\s)(first|1st|först)(?:(?=(\?|\.|!|,|\s|$)))")
    def execute(self, msg):
        global firsts

        if date_check():
            midnightRun()

        if msg.channel in firsts: #has_channel(firsts, msg.channel):
            msg.reply_channel("not")
        else:
            score = scoreFunction(datetime.now(), ScoreType.FIRST)
            msg.reply_channel("C O N G R A T U L A T I O N S {}, you scored:{}".format(msg.nick, score))
            insert_first(msg)
            firsts.append(msg.channel)

            addScore(msg.channel, msg.nick, score)


db = 'test.db'
connection = sqlite3.connect(db)
cur = connection.cursor()

def getScore(channel, user):
    global cur
    cur.execute('SELECT score FROM score WHERE channel_id IN(SELECT channel_id FROM channels WHERE channel = ?) AND user_id IN (SELECT user_id FROM users WHERE nick = ?)', (channel,user))
    r = cur.fetchone()
    if r:
        return r[0]
    return 0

def getChannelId(channel):
    global cur
    cur.execute('SELECT channel_id FROM channels WHERE channel = ?', (channel,))
    r = cur.fetchone()
    if r:
        return r[0]
    return False

def getChannelName(channel_id):
    global cur
    cur.execute('SELECT name FROM channels WHERE channel_id = ?', (channel_id,))
    r = cur.fetchone()
    if r:
        return r[0]
    return None

def getUserId(user):
    global cur
    cur.execute('SELECT user_id FROM users WHERE nick = ?', (user,))
    r = cur.fetchone()
    if r:
        return r[0]
    return False

def getUserName(user_id):
    global cur
    cur.execute('SELECT nick FROM users WHERE user_id = ?', (user_id,))
    r = cur.fetchone()
    if r:
        return r[0]
    return False


def addScore(channel, user, score):
    setScore(channel, user, int(getScore(channel, user)) + score)

def setScore(channel, user, score):
    global cur, connection
    user_id = getUserId(user)
    channel_id = getChannelId(channel)

    if not channel_id or not user_id:
        return False
    if hasUser(channel, user):
        cur.execute('UPDATE score SET score = ? WHERE channel_id = ? AND user_id = ?', (score, channel_id, user_id))
    else:
        cur.execute('INSERT INTO score VALUES (?, ?, ?)', (user_id, channel_id, score))
    connection.commit()
    return True

def hasUser(channel, user):
    global cur
    cur.execute('SELECT * FROM score WHERE channel_id IN(SELECT channel_id FROM channels WHERE channel = ?) AND user_id IN (SELECT user_id FROM users WHERE nick = ?)', (channel,user))
    r = cur.fetchone()
    if r is not None:
        return True
    return False

def getHighScore(channel):
    global cur
    channel_id = getChannelId(channel)
    if not channel_id:
        return False
    cur.execute('SELECT users.nick, score FROM score INNER JOIN users ON score.user_id = users.user_id WHERE channel_id = ? ORDER BY score DESC', (channel_id,))

    return cur.fetchall()

def insert_first_last(channel, user, type_name):
    global cur, connection
    user_id = getUserId(user)
    channel_id = getChannelId(channel)
    type_id = get_first_last_type(type_name)
    if not type_id:
        create_first_last_type(type_name)
    if user_id is not None and channel_id is not None:
        cur.execute('INSERT into first_lasts VALUES (?, ?, ?, ?)', (type_id, user_id, channel_id, datetime.now()))
    connection.commit()

def get_first_last_type(type_name):
    global cur, connection
    cur.execute('SELECT first_last_type_id FROM first_last_types WHERE name = ?', [type_name])
    r = cur.fetchone()
    if r is not None:
        return r[0]
    return False


def create_first_last_type(type_name):
    global cur, connection
    if get_first_last_type(type_name):
        return False

    cur.execute('INSERT INTO first_last_types VALUES (?, ?)' , (None, type_name))
    connection.commit()
    return True

def insert_first(msg):
    insert_first_last(msg.channel, msg.nick, "first")
def insert_last(msg):
    insert_first_last(msg.channel, msg.nick, "last")

def load_first_lasts():
    global lasts, firsts
    _db = 'test.db'
    _connection = sqlite3.connect(_db, detect_types=sqlite3.PARSE_DECLTYPES)
    _cursor = _connection.cursor()

    _cursor.execute("SELECT channel, nick, name, time FROM first_lasts INNER JOIN channels on first_lasts.channel_id = channels.channel_id INNER JOIN users ON users.user_id = first_lasts.user_id INNER JOIN first_last_types ON first_last_types.first_last_type_id = first_lasts.first_last_type_id WHERE date(time) = date('NOW', 'localtime') ORDER BY time")

    f = {}
    l = {}

    for row in _cursor:
        channel = row[0]
        user = row[1]
        fl_type = row[2]
        msg = Message(data=None, channel=channel, text=None, nick=user)
        msg.time = row[3]
        if fl_type == "last":
            if not channel in lasts:
                lasts[channel] = []
            """ The user already lasted"""
            if user in lasts[channel]:
                pass
            else:
                lasts[channel].append(msg)

        if fl_type == "first":
            """ add the channel to firsts """
            if not channel in firsts:
                firsts.append(channel)
            else:
                firsts.append(msg)
                pass


def create_tables():
    _db = 'test.db'
    _connection = sqlite3.connect(_db)
    _cursor = _connection.cursor()

    _cursor.execute('CREATE TABLE IF NOT EXISTS first_last_types(first_last_type_id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255))')
    _connection.commit()

    _cursor.execute('CREATE TABLE IF NOT EXISTS first_lasts(first_last_type_id INTEGER, user_id INTEGER ,channel_id INTEGER,time DATETIME, FOREIGN KEY (first_last_type_id) REFERENCES first_last_types(first_last_type_id), FOREIGN KEY (user_id) REFERENCES users(user_id), FOREIGN KEY (channel_id) REFERENCES channels(channel_id));')
    _connection.commit()


    _cursor.execute('CREATE TABLE IF NOT EXISTS score(user_id INTEGER ,channel_id INTEGER, score INTEGER ,FOREIGN KEY (user_id) REFERENCES users(user_id), FOREIGN KEY (channel_id) REFERENCES channels(channel_id));')

    _connection.commit()


class FirstLastJoinListener(listeners.SelfJoinListener):
    def __init__(self):
        listeners.SelfJoinListener.__init__(self, "firstlastselfjoin")
    def execute(self, msg):
        global firsts, lasts
        msg.reply_channel("Went down for a while...do")
        if msg.channel in firsts:
            # we do not have the nick yet
            msg.reply_channel("We had a first...")
        else:
            msg.reply_channel("The first is free")

        if msg.channel in lasts.keys():
            msg.reply_channel("lasts:" + ",".join([x.nick for x in
                                                   lasts[msg.channel]]))
        else:
            msg.reply_channel("no lasts for today")

listeners.getHandler().add(LastListener())
listeners.getHandler().add(MidnightRunListener())
listeners.getHandler().add(FirstListener())
listeners.getHandler().add(FirstLastJoinListener())
cmds.getHandler().add("highscore", high_score)
cmds.getHandler().add("score", my_score)

create_tables()
load_first_lasts()


if __name__  == '__main__':
    getHighScore('#dbglordnikon')

