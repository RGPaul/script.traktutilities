# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '48dfcb4813134da82152984e8c4f329bc8b8b46a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

def showFriends():

    options = []
    data = getFriendsFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py
    
    for friend in data:
        try:
            if friend['full_name'] != None:
                options.append(friend['full_name']+" ("+friend['username']+")")
            else:
                options.append(friend['username'])
        except KeyError:
            pass # Error ? skip this movie
    
    if len(options) == 0:
        xbmcgui.Dialog().ok("Trakt Utilities", "you have not added any friends on Trakt")
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1211).encode( "utf-8", "ignore" ), options) # Friends
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        showFriendSubmenu(data[select])
 
def showFriendSubmenu(user):
    #check what (if anything) the user is watching
    watchdata = getWatchingFromTraktForUser(user['username'])
    currentitem = "Nothing"
    if len(watchdata) != 0:
        if watchdata['type'] == "movie":
            currentitem = watchdata['movie']['title']+" ["+str(watchdata['movie']['year'])+"]"
        elif watchdata['type'] == "episode":
            currentitem = watchdata['show']['title']+" "+str(watchdata['episode']['season'])+"x"+str(watchdata['episode']['number'])+" - "+watchdata['episode']['title']
    
    options = [(__language__(1280)+": "+currentitem).encode( "utf-8", "ignore" ), __language__(1281).encode( "utf-8", "ignore" ), __language__(1282).encode( "utf-8", "ignore" ), __language__(1283).encode( "utf-8", "ignore" ), __language__(1284).encode( "utf-8", "ignore" )]
    while True:
        select = xbmcgui.Dialog().select((__language__(1211)+" - "+user['username']).encode( "utf-8", "ignore" ), options)
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        else:
            if select == 0: # Select (friends) currenty playing
                xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")
            elif select == 1: # Friends watchlist
                showFriendsWatchlist(user)
            elif select == 2: # Friends watched
                showFriendsWatched(user)
            elif select == 3: # Friends library
                showFriendsLibrary(user)
            elif select == 4: # Friends profile
                showFriendsProfile(user)

def showFriendsWatchlist(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")

def showFriendsWatched(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")

def showFriendsLibrary(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")

def showFriendsProfile(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")