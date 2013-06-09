# -*- coding: utf-8 -*-
"""
## --- All Rights Reserved to Nam Hee Kim, Rice University --- ##
## --- 모든 저작권은 김남희(nk17@rice.edu)에게 있으며 상업적/비상업적 용도를 불문
## --- 무단배포를 엄금합니다.
"""
__module_name__ = 'Genero IRC TRPG'
__module_description__ = '제네로지엄 IRC TRPG'
__module_version__ = '0.1'

print "*****Compiling Started*****"

## --- Import --- ##

import xchat
print "Import Successful: xchat module"
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
print "Import Successful: sqlalchemy module"


## --- SQLAlchemy Setup --- ##
def sqlalchemy_init():
    """
    Initialize the SQLAlchemy Database using SQLAlchemy's methods.
    """
    global Base, engine
    Base = declarative_base()
    engine = create_engine('sqlite:///test.db',echo=True)
    
sqlalchemy_init()

def sql_start_session():
    """
    Starts a session bound with SQLite to manipulate entries
    """
    global engine, session
    Session = sessionmaker(bind=engine)
    session = Session()

sql_start_session()

def sql_close_session():
    """
    Closes the active sessioin.
    """
    global session
    session.close()

def sql_create_all_tables():
    """
    Within the SQLAlchemy metadata, creates a table to contain user information
    """
    global Base, engine
    Base.metadata.create_all(engine)

def sql_get_user_by_host(given_host):
    """
    Returns the entry matching the given host. None otherwise.
    """
    result = session.query(User).filter_by(host=given_host).first()  
    return result
    
def sql_insert_user(given_nick, given_host):
    """
    If the user's entry does not exist, insert the user to the database
    If the user exists but has a different nick, then change the nickname    
    """
    global session
    existing_user = sql_get_user_by_host(given_host)
    if not existing_user:
        new_user = User(given_nick, given_host)
        session.add(new_user)
        session.commit()
    else:
        if existing_user.nick != given_nick:
            existing_user.nick = given_nick
            session.commit()
        
### --- Global Variables --- ###
channels_list = xchat.get_list("channels")

### --- Defining Classes --- ###

class User(Base):

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    nick = Column(Unicode)
    host = Column(Unicode)
    
    def __init__(self, nick, host):
        self.nick = nick
        self.host = host

    def __repr__(self):
        return "<User('%s','%s','%s')>" % (self.id, self.name, self.host)

sql_create_all_tables()

### --- Basic Interface Functions --- ###

def say(context, message):
    """
    "Says" the message onto the given context.
    """
    xchat.command("say " + str(message))

def notice(target, message):
    """
    "Notices" the message onto the given target.
    """
    xchat.command("notice " + str(target) + " " + str(message))

def whois(nick):
    """
    Sends a whois query to the target nickname 
    """
    xchat.command("whois " + str(nick))

def all_channels_notice(message):
    """
    Sends a notice to every channel the bot is on
    """
    global channels_list
    for channel in channels_list:
        notice(channel.channel, message)

def all_channels_say(message):
    """
    Says the given message to every channel the bot is on
    """
    global channels_list
    for channel in channels_list:
        context = channel.context
        say(context, message)

## --- Getters --- ##

def get_user_object_named(nick):
    """
    Returns the user object that has a matching nickname
    """
    for user in xchat.get_list("users"):
        if user.nick == nick:
            return user
    print "No such user..."

## === GAME FUNCTIONS === ##


def test(data):
    """
    Test function
    """
    print "Success"

def ping(data):
    """
    Pongs back to the target nick
    """
    nick = data["nick"]
    xchat.command("say PONG, " + nick)

## --- Mappers --- ##

func_map = {unicode("#$테스트"):test,
            unicode("#$핑"):ping}

def interpret_channel_message(nick, message):
    """
    Breaks down the message into parameters.
    The first word determines which function
    to execute. Other words are passed in as
    parameters.
    """
    
    message_list = message.split(" ")
    func = message_list[0]
    data = {"nick":nick}
    if message_list[1:] != []:
        data[params] = message_list[1:]
    func_map[func](data)

## --- Event Handlers --- ##

def on_channel_message(word, word_eol, userdata):
    """
    Parses the channel messages and breaks them down into variables
    """
    nick = unicode(word[0])
    message = unicode(word[1])
    message_eol = word_eol
    host = unicode(get_user_object_named(nick).host)
    sql_insert_user(nick, host)
    interpret_channel_message(nick,message)
    
def on_whois(word, word_eol, userdata):
    """
    Parses the whois messages and breaks them into variables
    """
    nick = str(word[0])
    username = str(word[1])
    ip = str(word[2])
    fullname = str(word[3])
    channel = str(xchat.get_info("channel"))

def on_my_join(word, word_eol, userdata):
    """
    Parses the bot's own join messages and breaks them into variables
    """
    global channels_list
    channels_list = xchat.get_list("channels")

def on_join(word, word_eol, userdata):
    """
    Parses other users' join messages
    """
    nick = unicode(word[0])
    host = unicode(word[2])
    sql_insert_user(nick,host)

def on_nick_change(word, word_eol, userdata):
    old_nick = unicode(word[0])
    new_nick = unicode(word[1])
    host = unicode(get_user_object_named(new_nick).host)
    sql_insert_user(new_nick, host)

xchat.hook_print("Channel Message", on_channel_message)
xchat.hook_print("Channel Msg Hilight", on_channel_message)
xchat.hook_print("WhoIs Name Line", on_whois)
xchat.hook_print("You Join", on_my_join)
xchat.hook_print("Change Nick", on_nick_change)
xchat.hook_print("Join", on_join)

print "*****Compiling Finished*****"
