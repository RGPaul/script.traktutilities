# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import os
import xbmc,xbmcaddon,xbmcgui
import time, socket
import simplejson as json

try:
    # Python 3.0 +
    import http.client as httplib
except ImportError:
    # Python 2.7 and earlier
    import httplib

try:
  # Python 2.6 +
  from hashlib import sha as sha
except ImportError:
  # Python 2.5 and earlier
  import sha
  
try:
    # Python 2.4
    import pysqlite2.dbapi2 as sqlite3
except:
    # Python 2.6 +
    import sqlite3 

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

def Debug(msg, force=False):
    if (debug == 'true' or force):
        print "Trakt Utilities: " + msg.encode( "utf-8", "ignore" )

def notification( header, message, time=5000, icon=__settings__.getAddonInfo( "icon" ) ):
    xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( header, message, time, icon ) )

def checkSettings(daemon=False):
    if username == "":
        if daemon:
            notification("Trakt Utilities", __language__(1106).encode( "utf-8", "ignore" )) # please enter your Username and Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1106).encode( "utf-8", "ignore" )) # please enter your Username and Password in settings
        return False
    elif __settings__.getSetting("password") == "":
        if daemon:
            notification("Trakt Utilities", __language__(1107).encode( "utf-8", "ignore" )) # please enter your Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1107).encode( "utf-8", "ignore" )) # please enter your Password in settings
        return False
    
    return True

# get database path
def getDBPath():
    datapath = xbmc.translatePath("special://database")
    myVideosList = []
    dirList=os.listdir(datapath)
    for fname in dirList:
        if fname.startswith('MyVideos'):
            c1 = 8; c2 = 9
            for i in range(9, len(fname)):
                if fname[i] == '.':
                    c2 = i
                    break
            try:
                number = int(fname[c1:c2])
                myVideosList.append((fname, number))
            except ValueError:
                pass
    
    # sort list by database number
    myVideosList.sort(key=lambda file: file[1])

    # return last in list (highest number should be current database)
    path = os.path.join(datapath, myVideosList[len(myVideosList)-1][0])
    if os.path.isfile(path):
        return path
    else:
        # no file? try the second highest database
        path = os.path.join(datapath, myVideosList[len(myVideosList)-2][0])
        if os.path.isfile(path):
            return path
    return None
    

# get movies from trakt server
def getMoviesFromTrakt(daemon=False):

    try:
        conn.request('GET', '/user/library/movies/all.json/' + apikey + "/" + username)
    except socket.error:
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass

    return data

# get easy access to movie by imdb_id
def traktMovieListByImdbID(data):
    trakt_movies = {}

    for i in range(0, len(data)):
        trakt_movies[data[i]['imdb_id']] = data[i]
        
    return trakt_movies

# get seen tvshows from trakt server
def getWatchedTVShowsFromTrakt(daemon=False):
    
    try:
        conn.request('GET', '/user/library/shows/watched.json/' + apikey + "/" + username)
    except socket.error:
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data
    
# get tvshow collection from trakt server
def getTVShowCollectionFromTrakt(daemon=False):
    
    try:
        conn.request('GET', '/user/library/shows/collection.json/' + apikey + "/" + username)
    except socket.error:
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data
    
# get tvshows from XBMC
def getTVShowsFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows','params':{'fields': ['title', 'year', 'imdbnumber', 'playcount']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    return result['result']

    
# get seasons for a given tvshow from XBMC
def getSeasonsFromXBMC(tvshow):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetSeasons','params':{'tvshowid': tvshow['tvshowid']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    return result['result']
    
# get episodes for a given tvshow / season from XBMC
def getEpisodesFromXBMC(tvshow, season):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetEpisodes','params':{'tvshowid': tvshow['tvshowid'], 'season': season, 'fields': ['playcount', 'episode']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    Debug ("RESULT: " + str(result))

    return result['result']

# get movies from XBMC
def getMoviesFromXBMC():
    # ToDo: this is outdated - if Eden releases: update
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies','params':{'fields': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastPlayed']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    # for backward compatibility - ToDo: clean with Eden stable release
    try:
        return result['result']['movies']
    except KeyError:
        rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies','params':{'fields': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed']}, 'id': 1})
    
        result = xbmc.executeJSONRPC(rpccmd)
        result = json.loads(result)
        
        return result['result']['movies']

# sets the playcount of a given movie by imdbid
def setXBMCMoviePlaycount(imdb_id, playcount, cursor):
    # sqlite till jsonrpc supports playcount update
    # c09 => IMDB ID
    cursor.execute('select idFile from movie where c09=?', (imdb_id,))
    idfile = cursor.fetchall()[0][0]
    cursor.execute('update files set playCount=? where idFile=?',(playcount, idfile))    

# sets the playcount of a given episode by tvdb_id
def setXBMCEpisodePlaycount(tvdb_id, seasonid, episodeid, playcount, cursor):
    # sqlite till jsonrpc supports playcount update
    idshow = None
    # select tvshow by tvdb_id # c12 => TVDB ID
    cursor.execute('select idShow, c00 from tvshow where c12=?', (tvdb_id,))
    for row in cursor.fetchall():
        Debug("Serie: " + row[1] + " idShow: " + str(row[0]) + " season: " + str(seasonid) + " episode: " + str(episodeid))
        idshow = row[0]
    # select episode table by idShow
    if idshow != None:
        cursor.execute('select idEpisode from tvshowlinkepisode where idShow=?', (idshow,))
        for row in cursor.fetchall():
            idepisode = row[0]
            # get idfile from episode table # c12 = season, c13 = episode
            cursor.execute('select idFile from episode where idEpisode=? and c12=? and c13=?', (idepisode, seasonid, episodeid))
            for row2 in cursor.fetchall():
                idfile = row2[0]
                Debug("idFile: " + str(idfile) + " setting playcount...")
                cursor.execute('update files set playCount=? where idFile=?',(playcount, idfile))

# returns list of movies from watchlist
def getWatchlistMoviesFromTrakt():
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/watchlist/movies.json/' + apikey + "/" + username, jdata)
    except socket.error:
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

# returns list of tv shows from watchlist
def getWatchlistTVShowsFromTrakt():
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/watchlist/shows.json/' + apikey + "/" + username, jdata)
    except socket.error:
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

"""
for later:
First call "Player.GetActivePlayers" to determine the currently active player (audio, video or picture).
If it is audio or video call Audio/VideoPlaylist.GetItems and read the "current" field to get the position of the
currently playling item in the playlist. The "items" field contains an array of all items in the playlist and "items[current]" is
the currently playing file. You can also tell jsonrpc which fields to return for every item in the playlist and therefore you'll have all the information you need.

"""
