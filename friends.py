# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul, Adrian Cowan (othrayte)
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

# list reccomended movies
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
        
        xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")
    
