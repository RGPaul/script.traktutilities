# -*- coding: utf-8 -*-
# 

import os
import xbmc,xbmcaddon,xbmcgui
import time, socket
import simplejson as json
import urllib, re

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

def Debug(msg, force=False):
    if (debug == 'true' or force):
        print "Trakt Utilities: " + msg

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

# make a httpapi based XBMC db query (get data)
def xbmcHttpapiQuery(query):
    Debug("[httpapi-sql] query: "+query)
    xml_data = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % urllib.quote_plus(query), )
    match = re.findall( "<field>((?:[^<]|<(?!/))*)</field>", xml_data,)
    Debug("[httpapi-sql] responce: "+xml_data)
    Debug("[httpapi-sql] matches: "+str(match))
    if len(match) <= 0:
        return None
    return match

# execute a httpapi based XBMC db query (set data)
def xbmcHttpapiExec(query):
    xml_data = xbmc.executehttpapi( "ExecVideoDatabase(%s)" % urllib.quote_plus(query), )
    return xml_data

# get movies from trakt server
def getMoviesFromTrakt(daemon=False):

    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/library/movies/all.json/' + apikey + "/" + username, jdata)
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
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/library/shows/watched.json/' + apikey + "/" + username, jdata)
    except socket.error:
        Debug("getWatchedTVShowsFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getWatchedTVShowsFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data
    
# get tvshow collection from trakt server
def getTVShowCollectionFromTrakt(daemon=False):
    
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/library/shows/collection.json/' + apikey + "/" + username, jdata)
    except socket.error:
        Debug("getTVShowCollectionFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getTVShowCollectionFromTrakt: Error: " + str(data['error']))
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
    
    # check for error
    try:
        error = result['error']
        Debug("getTVShowsFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error
    
    try:
        return result['result']
    except KeyError:
        Debug("getTVShowsFromXBMC: KeyError: result['result']")
        return None
    
# get seasons for a given tvshow from XBMC
def getSeasonsFromXBMC(tvshow):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetSeasons','params':{'tvshowid': tvshow['tvshowid']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    # check for error
    try:
        error = result['error']
        Debug("getSeasonsFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error

    try:
        return result['result']
    except KeyError:
        Debug("getSeasonsFromXBMC: KeyError: result['result']")
        return None
    
# get episodes for a given tvshow / season from XBMC
def getEpisodesFromXBMC(tvshow, season):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetEpisodes','params':{'tvshowid': tvshow['tvshowid'], 'season': season, 'fields': ['playcount', 'episode']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    # check for error
    try:
        error = result['error']
        Debug("getEpisodesFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error

    try:
        return result['result']
    except KeyError:
        Debug("getEpisodesFromXBMC: KeyError: result['result']")
        return None

# get movies from XBMC
def getMoviesFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies','params':{'fields': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed']}, 'id': 1})

    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    # check for error
    try:
        error = result['error']
        Debug("getMoviesFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error
    
    try:
        return result['result']['movies']
        Debug("getMoviesFromXBMC: KeyError: result['result']['movies']")
    except KeyError:
        return None

# sets the playcount of a given movie by imdbid
def setXBMCMoviePlaycount(imdb_id, playcount):

    # httpapi till jsonrpc supports playcount update
    # c09 => IMDB ID
    match = xbmcHttpapiQuery(
    "SELECT movie.idFile FROM movie"+
    " WHERE movie.c09='%(imdb_id)s'" % {'imdb_id':str(imdb_id)})
    
    if match == None:
        #add error message here
        return
    
    result = xbmcHttpapiExec(
    "UPDATE files"+
    " SET playcount=%(playcount)d" % {'playcount':playcount}+
    " WHERE idFile=%(idFile)s" % {'idFile':match[0]})
    
    Debug("xml answer: " + str(result))

# sets the playcount of a given episode by tvdb_id
def setXBMCEpisodePlaycount(tvdb_id, seasonid, episodeid, playcount):
    # httpapi till jsonrpc supports playcount update
    # select tvshow by tvdb_id # c12 => TVDB ID # c00 = title
    match = xbmcHttpapiQuery(
    "SELECT tvshow.idShow, tvshow.c00 FROM tvshow"+
    " WHERE tvshow.c12='%(tvdb_id)s'" % {'tvdb_id':str(tvdb_id)})
    
    if len(match) >= 1:
        Debug("TV Show: " + match[1] + " idShow: " + str(match[0]) + " season: " + str(seasonid) + " episode: " + str(episodeid))

        # select episode table by idShow
        match = xbmcHttpapiQuery(
        "SELECT tvshowlinkepisode.idEpisode FROM tvshowlinkepisode"+
        " WHERE tvshowlinkepisode.idShow=%(idShow)s" % {'idShow':str(match[0])})
        
        for idEpisode in match:
            # get idfile from episode table # c12 = season, c13 = episode
            match2 = xbmcHttpapiQuery(
            "SELECT episode.idFile FROM episode"+
            " WHERE episode.idEpisode=%(idEpisode)d" % {'idEpisode':int(idEpisode)}+
            " AND episode.c12='%(seasonid)s'" % {'seasonid':str(seasonid)}+
            " AND episode.c13='%(episodeid)s'" % {'episodeid':str(episodeid)})
            
            if match2 != None:
                for idFile in match2:
                    Debug("idFile: " + str(idFile) + " setting playcount...")
                    responce = xbmcHttpapiExec(
                    "UPDATE files"+
                    " SET playcount=%(playcount)s" % {'playcount':str(playcount)}+
                    " WHERE idFile=%(idFile)s" % {'idFile':str(idFile)})
                    
                    Debug("xml answer: " + str(responce))
    else:
        Debug("setXBMCEpisodePlaycount: no tv show found for tvdb id: " + str(tvdb_id))
    
# get current video being played from XBMC
def getCurrentPlayingVideoFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoPlaylist.GetItems','params':{}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    # check for error
    try:
        error = result['error']
        Debug("getCurrentPlayingVideoFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error
    
    try:
        current = result['result']['state']['current']
        typ = result['result']['items'][current]['type']
        if typ in ("movie","episode"):
            return result['result']['items'][current]
        return None
    except KeyError:
        Debug("getCurrentPlayingVideoFromXBMC: KeyError")
        return None

def getMovieIdFromXBMC(imdb_id, title):
    # httpapi till jsonrpc supports selecting a single movie
    # Get id of movie by movies IMDB
    Debug("Searching for movie: "+imdb_id+", "+title)
    
    match = xbmcHttpapiQuery(
    " SELECT idMovie FROM movie"+
    "  WHERE c09='%(imdb_id)s'" % {'imdb_id':imdb_id}+
    " UNION"+
    " SELECT idMovie FROM movie"+
    "  WHERE upper(c00)='%(title)s'" % {'title':title.upper()}+
    " LIMIT 1")
    
    if match == None:
        Debug("getMovieIdFromXBMC: cannot find movie in database")
        return -1
        
    return match[0]
   
# returns list of movies from watchlist
def getWatchlistMoviesFromTrakt(friend=None):
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        if friend == None:
            conn.request('POST', '/user/watchlist/movies.json/' + apikey + "/" + username, jdata)
        else:
            conn.request('POST', '/user/watchlist/movies.json/' + apikey + "/" + friend, jdata)
    except socket.error:
        Debug("getWatchlistMoviesFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getWatchlistMoviesFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

# returns list of tv shows from watchlist
def getWatchlistTVShowsFromTrakt(friend=None):
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        if friend == None:
            conn.request('POST', '/user/watchlist/shows.json/' + apikey + "/" + username, jdata)
        else:
            conn.request('POST', '/user/watchlist/shows.json/' + apikey + "/" + friend, jdata)
    except socket.error:
        Debug("getWatchlistTVShowsFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getWatchlistTVShowsFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

# add an array of movies to the watch-list
def addMoviesToWatchlist(data):
    # This function has not been tested, please test it before using it
    movies = []
    for item in data:
        if "imdb_id" in item:
            movie["imdb_id"] = item["imdb_id"]
        if "tmdb_id" in item:
            movie["tmdb_id"] = item["tmdb_id"]
        if "title" in item:
            movie["title"] = item["title"]
        if "year" in item:
            movie["year"] = item["year"]
        movies.append(movie)
    try:
        jdata = json.dumps({'username': username, 'password': pwd, "movies":movies})
        conn.request('POST', '/movie/watchlist/'+apikey, jdata)
    except socket.error:
        Debug("addMoviesToWatchlist: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None
    
    # I dont know if we need the rest of this???
    response = conn.getresponse()
    data = json.loads(response.read())
    Debug("addMoviesToWatchlist responce:" + data)
    try:
        if data['status'] == 'failure':
            Debug("getFriendsFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

#Set the rating for a movie on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateMovieOnTrakt(imdbid, title, year, rating):
    if not (rating in ("love", "hate")):
        #add error message
        return
    
    Debug("Rating movie:" + rating)
    try:
        jdata = json.dumps({'username': username, 'password': pwd, 'imdb_id': imdbid, 'title': title, 'year': year, 'rating': rating})
        conn.request('POST', '/rate/movie/' + apikey, jdata)
    except socket.error:
        Debug("rateMovieOnTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("rateMovieOnTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1168).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error submitting rating
            return None
    except TypeError:
        pass
    
    notification("Trakt Utilities", __language__(1167).encode( "utf-8", "ignore" )) # Rating submitted successfully
    
    return data

#Set the rating for a tv episode on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateEpisodeOnTrakt(tvdbid, title, year, season, episode, rating):
    if not (rating in ("love", "hate")):
        #add error message
        return
    
    Debug("Rating episode:" + rating)
    try:
        jdata = json.dumps({'username': username, 'password': pwd, 'tvdb_id': tvdbid, 'title': title, 'year': year, 'season': season, 'episode': episode, 'rating': rating})
        conn.request('POST', '/rate/episode/' + apikey, jdata)
    except socket.error:
        Debug("rateEpisodeOnTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("rateEpisodeOnTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1168).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error submitting rating
            return None
    except TypeError:
        pass
    
    notification("Trakt Utilities", __language__(1167).encode( "utf-8", "ignore" )) # Rating submitted successfully
    
    return data

def getRecommendedMoviesFromTrakt():
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/recommendations/movies/' + apikey, jdata)
    except socket.error:
        Debug("getRecommendedMoviesFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getRecommendedMoviesFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

def getRecommendedTVShowsFromTrakt():
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/recommendations/shows/' + apikey, jdata)
    except socket.error:
        Debug("getRecommendedTVShowsFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getRecommendedTVShowsFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

def getTrendingMoviesFromTrakt():
    try:
        conn.request('GET', '/movies/trending.json/' + apikey)
    except socket.error:
        Debug("getTrendingMoviesFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getTrendingMoviesFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

def getTrendingTVShowsFromTrakt():
    try:
        conn.request('GET', '/shows/trending.json/' + apikey)
    except socket.error:
        Debug("getTrendingTVShowsFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getTrendingTVShowsFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

def getFriendsFromTrakt():
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/friends.json/'+apikey+'/'+username, jdata)
    except socket.error:
        Debug("getFriendsFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getFriendsFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

def getWatchingFromTraktForUser(name):
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        conn.request('POST', '/user/watching.json/'+apikey+'/'+name, jdata)
    except socket.error:
        Debug("getWatchingFromTraktForUser: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())
    
    return data

def playMovieById(idMovie):
    # httpapi till jsonrpc supports selecting a single movie
    Debug("Play Movie requested for id: "+str(idMovie))
    if idMovie == -1:
        return # invalid movie id
    else:
        # get file reference id from movie reference id
        match = xbmcHttpapiQuery(
        "SELECT movie.idFile FROM movie"+
        " WHERE movie.idMovie=%(idMovie)s" % {'idMovie':str(idMovie)})
        
        if match == None:
            Debug("playMovieById: Error getting idFile")
            return
        
        idFile = match[0]
        
        # Get path and filename of file by fileid
        match = xbmcHttpapiQuery(
        "SELECT files.idPath, files.strFilename FROM files"+
        " WHERE files.idFile=%(idFile)s" % {'idFile':str(idFile)})
        
        if match == None:
            Debug("playMovieById: Error getting filename")
            return
        
        idPath = match[0]
        strFilename = match[1]
        if strFilename.startswith("stack://"): # if the file is a stack, dont bother getting the path, stack include the path
            xbmc.Player().play(strFilename)
        else :
            # Get the path of the file by fileid
            match = xbmcHttpapiQuery(
            "SELECT path.strPath FROM path"+
            " WHERE path.idPath=%(idPath)s" % {'idPath':idPath})
            
            if match == None:
                Debug("playMovieById: Error getting path")
                return
            
            strPath = match[0]
            xbmc.Player().play(strPath+strFilename)

def getWatchedFromTrakt(friend=None):
    try:
        jdata = json.dumps({'username': username, 'password': pwd})
        if friend == None:
            conn.request('POST', '/user/watched.json/' + apikey + "/" + username, jdata)
        else:
            conn.request('POST', '/user/watched.json/' + apikey + "/" + friend, jdata)
    except socket.error:
        Debug("getWatchedFromTrakt: can't connect to trakt")
        notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
        return None

    response = conn.getresponse()
    data = json.loads(response.read())

    try:
        if data['status'] == 'failure':
            Debug("getWatchedFromTrakt: Error: " + str(data['error']))
            notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
            return None
    except TypeError:
        pass
    
    return data

"""
ToDo:


"""


"""
for later:
First call "Player.GetActivePlayers" to determine the currently active player (audio, video or picture).
If it is audio or video call Audio/VideoPlaylist.GetItems and read the "current" field to get the position of the
currently playling item in the playlist. The "items" field contains an array of all items in the playlist and "items[current]" is
the currently playing file. You can also tell jsonrpc which fields to return for every item in the playlist and therefore you'll have all the information you need.

"""
