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

# @author Adrian Cowan (othrayte), Ralph-Gordon Paul (Manromen)
def showFriends():

    options = []
    friends = []
    data = getFriendsFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py
    
    for friend in data:
        try:
            if friend['full_name'] != None:
                options.append(friend['full_name']+" ("+friend['username']+")")
                friends.append(friend)
            else:
                options.append(friend['username'])
                friends.append(friend)
        except KeyError:
            pass # Error ? skip this friend
    
    if len(options) == 0:
        xbmcgui.Dialog().ok("Trakt Utilities", "you have not added any friends on Trakt")
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1211).encode( "utf-8", "ignore" ), options) # Friends
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        showFriendSubmenu(friends[select])

# @author Adrian Cowan (othrayte), Ralph-Gordon Paul (Manromen)
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
                if watchdata['type'] == "movie":
                    # if movie - display movie information
                    import windows
                    ui = windows.MovieWindow("movie.xml", __settings__.getAddonInfo('path'), "Default")
                    ui.initWindow(watchdata['movie'])
                    ui.doModal()
                    del ui
                elif watchdata['type'] == "episode":
                    # if episode - display tvshow information
                    import windows
                    ui = windows.TVShowWindow("tvshow.xml", __settings__.getAddonInfo('path'), "Default")
                    ui.initWindow(watchdata['show'])
                    ui.doModal()
                    del ui
                    
            elif select == 1: # Friends watchlist
                showFriendsWatchlist(user)
            elif select == 2: # Friends watched
                showFriendsWatched(user)
            elif select == 3: # Friends library
                showFriendsLibrary(user)
            elif select == 4: # Friends profile
                showFriendsProfile(user)

# displays the friends watchlist
def showFriendsWatchlist(user):
    options = [__language__(1252).encode( "utf-8", "ignore" ), __language__(1253).encode( "utf-8", "ignore" )]
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1210).encode( "utf-8", "ignore" ), options)
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        if select == 0: # Watchlist Movies
            movies = getWatchlistMoviesFromTrakt(user['username'])
            
            if movies == None: # movies = None => there was an error
                return # error already displayed in utilities.py
    
            if len(movies) == 0:
                xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1165).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies in the watchlist
                return
                
            # display watchlist movie list
            import windows
            ui = windows.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
            ui.initWindow(movies)
            ui.doModal()
            del ui
            
        elif select == 1: # Watchlist TV Shows
            tvshows = getWatchlistTVShowsFromTrakt(user['username'])
    
            if tvshows == None: # tvshows = None => there was an error
                return # error already displayed in utilities.py
            
            if len(tvshows) == 0:
                xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1166).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows in the watchlist
                return
            
            # display watchlist tv shows
            import windows
            ui = windows.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
            ui.initWindow(tvshows)
            ui.doModal()
            del ui

# @author Adrian Cowan (othrayte)
def showFriendsWatched(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")

# @author Adrian Cowan (othrayte)
def showFriendsLibrary(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")

# @author Adrian Cowan (othrayte)
def showFriendsProfile(user):
    xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")