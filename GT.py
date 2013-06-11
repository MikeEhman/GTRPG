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

## --- CONSTANTS --- ##
DEFAULT_AREA = "라페도 광장"

## --- SQLAlchemy Setup --- ##
def sqlalchemy_init():
    """
    Initialize the SQLAlchemy Database using SQLAlchemy's methods.
    """
    global Base, engine
    Base = declarative_base()
    engine = create_engine('sqlite:///test.db', echo=True)
    
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

    # Parent: Game
    # Child: Character

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    nick = Column(Unicode)
    host = Column(Unicode)
    game_id = Column(Integer, ForeignKey('games.id'))

    characters = relationship('Character', backref='users')
    
    def __init__(self, nick, host):
        self.nick = nick
        self.host = host
        self.game_id = 0

    def __repr__(self):
        return "<User('%s','%s','%s')>" % (self.id, self.nick, self.host)

class Game(Base):

    # Parent: None (Root)
    # Child: User

    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    hardcore = Column(Unicode)
    
    masters = relationship("User")
    players = relationship("User", backref="games")
    characters = relationship("Character", backref="game")

    def __init__(self, title, masters, players, hardcore):
        self.title = title
        self.masters = masters
        self.hardcore = hardcore
        self.players = players

        session.add(self)

        characters_list = []
        
        for each_player in players:
            new_character = Character()
            new_character.name = unicode(each_player.nick)
            new_character.games = [self]
            session.add(new_character)
            characters_list.append(new_character)

        self.characters = characters_list
        session.commit()

        players_string = ""
        for each_player in self.players:
            if players.index(each_player) < len(players)-1:
                players_string += each_player.nick + ", "
            else:
                players_string += each_player.nick

        context = xchat.get_context()
        say(context, '[' +self.title + '] ' + '게임이 시작되었습니다. (마스터: ' + self.masters[0].nick + ', ' + '플레이어: ' + players_string + ')') 

class Character(Base):

    # Parent: User, Game
    # Has to look at user's game_id to see which game it belongs to

    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(Unicode)
    hp = Column(Integer)
    cash = Column(Integer)
    area_id = Column(Integer, ForeignKey('areas.id'))
    STR = Column(Integer)
    DEX = Column(Integer)
    INT = Column(Integer)
    game_id = Column(Integer, ForeignKey('games.id'))

    def __init__(self):
        """
        Initializes the character with default settings.
        """
        self.hp = 100
        self.cash = 0

    def __repr__(self):
        return "<Character " + self.name + ": HP=%s, Cash=%s>" % (self.hp,self.cash)

    def delta(self,param,num):
        """
        Change the given parameter by the given number

        param -- string, changing parameter
        """
        exec "self." + param + " += num"
        session.commit()

    def display_status(self):
        """
        displays self's parameters
        """
        context = xchat.get_context()
        say(context, "["+self.name+"] HP: " + str(self.hp) + ", 소지금: " + str(self.cash) + " 해시캐시")

class Area(Base):
    """
    Parent: None
    Children: Characters, Sub-areas...
    """

    __tablename__ = 'areas'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    east_id = Column(Integer, ForeignKey('areas.id'))
    north_id = Column(Integer, ForeignKey('areas.id'))
    west_id = Column(Integer, ForeignKey('areas.id'))
    south_id = Column(Integer, ForeignKey('areas.id'))

    characters = relationship("Character", backref="area")

    east = relationship("Area", backref=backref("west", remote_side=[id]))
    north = relationship("Area", backref=backref("south", remote_side=[id]))
    west = relationship("Area", backref=backref("east", remote_side=[id]))
    south = relationship("Area", backref=backref("north", remote_side=[id]))

    def __init__(self):
        pass

sql_create_all_tables()

### --- Basic Interface Functions --- ###

def say(context, message):
    """
    "Says" the message onto the given context.
    """
    context.command("say " + str(message))

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

def get_user_row_named(nick):
    """
    Returns the user row object that has a matching nickname.
    Uses host name for querying though.
    """
    target_host = get_user_object_named(nick).host
    return session.query(User).filter_by(host=target_host).first()

def get_character_row_named(given_name):
    """
    Returns the character row object that has a matching nickname.
    """
    print session.query(Character).first()
    return session.query(Character).filter_by(name=unicode(given_name)).first()

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
    context = data["context"]
    nick = data["nick"]
    print context
    print nick
    say(context, "PONG, " + nick)

# - Session Relative - #

game_on = False

def start_game(data):
    """
    Starts a game.
    First declares a new Game object,
    Second maps the users to new characters
    """
    if game_on:
        context = data["context"]
        say(context, "이미 게임이 진행중입니다.")
    else:
        # re-parse the parameters
        params = " ".join(data["params"])
        print params
        params = params.split('"')[1::2]
        for i in xrange(len(params)-1):
            print params[i]
        title = params[0]
        player_nicks = params[1].split(" ")
        if params[2]:
            hardcore = params[2]

        # declare a new game

        master_nick = unicode(data["nick"])
        master_host = unicode(get_user_object_named(master_nick).host)
        masters = [session.query(User).filter_by(host=master_host).first()]

        players_list = []            
        for each_player_nick in player_nicks:
            each_player_host = unicode(get_user_object_named(each_player_nick).host)
            each_player = session.query(User).filter_by(host=each_player_host).first()
            players_list.append(each_player)

        game = Game(title, masters, players_list, False)


def start_game_session(data):
    """
    Starts a session in the given game.
    """
    if game_on:
        context = data["context"]
        say(context, "이미 게임이 진행중입니다.")
    else:
        pass
    
# - Initialization and Designation - #
def init_game():
    """
    Initializing the game and mapping the variables.
    """
    pass


## --- Character Functions --- ##

def damage(data):
    """
    damages the given character in the data
    """
    char = data["char"]
    hp_delta = int(data["params"][0])
    char.delta("hp", -hp_delta)



## --- Mappers --- ##

func_map = {unicode("#$테스트"):test,
            unicode("#$핑"):ping,
            unicode("#$게임시작"):start_game}

master_func_map = {}

# only masters can operate character functions
char_func_map = {unicode("데미지"):damage}

starting_phase = [False, False, False]

def interpret_channel_message(nick, message):
    """
    Breaks down the message into parameters.
    The first word determines which function
    to execute. Other words are passed in as
    parameters.
    """

    if message.find("#$") != -1:        
        message_list = message.split(" ")
        func = message_list[0]
        data = {"nick":nick}
        data["context"] = xchat.get_context()
        if message_list[1:] != []:
            data["params"] = message_list[1:]
        try:
            func_map[func](data)
        except KeyError:
            # #$<Player> <function>
            message_list = message.partition("#$")[2].split(" ")
            char_nick = message_list[0]
            char = get_character_row_named(char_nick)
            if message_list[1:] != []:
                data = {}
                data["char"] = char
                char_func = message_list[1]
                if message_list[2:] != []:
                    data["params"] = message_list[2:]
                    try:
                        char_func_map[char_func](data)
                    except KeyError:
                        print "Not a Character Function"   
            else:
                char.display_status()
            
        # Starting game #
        if starting_phase[1]:
            pass
        elif starting_phase[2]:
            pass




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
