    # -*- coding: utf-8 -*-
# 

import os, sys
import xbmc,xbmcaddon,xbmcgui
import time, socket

try: import simplejson as json
except ImportError: import json

from nbhttpconnection import *

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

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

def Debug(msg, force=False):
    if (debug == 'true' or force):
        try:
            print "Trakt Utilities: " + unicode(msg)
        except UnicodeEncodeError:
            print "Trakt Utilities: " + msg.encode( "utf-8", "ignore" )

def notification( header, message, time=5000, icon=__settings__.getAddonInfo( "icon" ) ):
    xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( header, message, time, icon ) )

from trakt import Trakt

def checkSettings(daemon=False):
    if username == "":
        if daemon:
            notification("Trakt Utilities", __language__(1106).encode( "utf-8", "ignore" )) # please enter your Username and Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1106).encode( "utf-8", "ignore" )) # please enter your Username and Password in settings
            __settings__.openSettings()
        return False
    elif __settings__.getSetting("password") == "":
        if daemon:
            notification("Trakt Utilities", __language__(1107).encode( "utf-8", "ignore" )) # please enter your Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1107).encode( "utf-8", "ignore" )) # please enter your Password in settings
            __settings__.openSettings()
        return False
    
    data = Trakt.jsonRequest('POST', '/account/test/%%API_KEY%%', daemon=True)
    if data == None: #Incorrect trakt login details
        if daemon:
            notification("Trakt Utilities", __language__(1110).encode( "utf-8", "ignore" )) # please enter your Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1110).encode( "utf-8", "ignore" )) # please enter your Password in settings
            __settings__.openSettings()
        return False
        
    return True

# SQL string quote escaper
def xcp(s):
    return re.sub('''(['])''', r"''", str(s))

# make a httpapi based XBMC db query (get data)
def xbmcHttpapiQuery(query):
    Debug("[httpapi-sql] query: "+query)
    
    xml_data = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % urllib.quote_plus(query), )
    match = re.findall( "<field>((?:[^<]|<(?!/))*)</field>", xml_data,)
    
    Debug("[httpapi-sql] responce: "+xml_data)
    Debug("[httpapi-sql] matches: "+str(match))
    
    return match

# execute a httpapi based XBMC db query (set data)
def xbmcHttpapiExec(query):
    xml_data = xbmc.executehttpapi( "ExecVideoDatabase(%s)" % urllib.quote_plus(query), )
    return xml_data
   
# get movies from trakt server
def getMoviesFromTrakt(*args, **argd):
    return Trakt.userLibraryMoviesAll(username, *args, **argd)

# get movie that are listed as in the users collection from trakt server
def getMovieCollectionFromTrakt(*args, **argd):
    return Trakt.userLibraryMoviesCollection(username, *args, **argd)

# add movies to the users collection on trakt
def addMoviesToTraktCollection(movies, *args, **argd):
    return Trakt.movieLibrary(movies, *args, **argd)

# remove movies from the users collection on trakt
def removeMoviesFromTraktCollection(movies, *args, **argd):
    return Trakt.movieUnlibrary(movies, *args, **argd)
    
# get easy access to movie by imdb_id
def traktMovieListByImdbID(data):
    trakt_movies = {}

    for i in range(0, len(data)):
        if data[i]['imdb_id'] == "": continue
        trakt_movies[data[i]['imdb_id']] = data[i]
        
    return trakt_movies
    
# get easy access to show by remoteId
def traktShowListByRemoteId(data):
    trakt_shows = {}

    for show in data:
        if 'tvdb_id' in show and show['tvdb_id'] not in ("", None):
            trakt_shows[show['tvdb_id']] = show
        elif 'imdb_id' in show and show['imdb_id'] not in ("", None):
            trakt_shows[show['imdb_id']] = show
        
    return trakt_shows
    
# search movies on trakt
def searchTraktForMovie(title, year=None):
    query = urllib.quote_plus(repr(unicode(title))[1:].strip('\'\"'))
    data = Trakt.searchMovies(query)
    if data is None:
        return None
    if year is not None:
        for item in data:
            if 'year' in item and item['year'] == year:
                return item
        
    options = ["Skip"]
    for item in data:
        options.append(unicode(item['title'])+" ["+unicode(item['year'])+"]")
    
    if len(data) == 0:
        return None
    
    if not xbmcgui.Dialog().yesno("Trakt Utilities", "Trakt Utilities is having trouble identifing a movie, do you want to manually choose from a list?"):
        return None
        
    while True:
        select = xbmcgui.Dialog().select("Which is correct - "+unicode(title)+" ["+unicode(year)+"]", options)
        Debug("Select: " + str(select))
        if select == -1 or select == 0:
            Debug ("menu quit by user")
            return None
        elif (select-1) <= len(data):
            return data[select-1]

# search imdb via google
def searchGoogleForImdbId(query):
    conn = httplib.HTTPConnection("ajax.googleapis.com")
    conn.request("GET", "/ajax/services/search/web?v=1.0&q=site:www.imdb.com+"+urllib.quote_plus(repr(unicode(query))[1:].strip('\'\"')))
    response = conn.getresponse()
    try:
        raw = response.read()
        data = json.loads(raw)
        for result in data['responseData']['results']:
            if (result['visibleUrl'] == "www.imdb.com"):
                if (re.match("http[:]//www[.]imdb[.]com/title/", result['url'])):
                    imdbid = re.search('/(tt[0-9]{7})/', result['url']).group(1)
                    Debug("[~] "+str(imdbid))
                    return imdbid;
    except ValueError:
        Debug("googleQuery: Bad JSON responce: "+raw)
        if not daemon: notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": Bad responce from google") # Error
        return None
    return None
    
# get movie summary from trakt server
# title: Either the slug (i.e. the-social-network-2010), IMDB ID, or TMDB ID.
def getMovieFromTrakt(title, *args, **argd):
    return Trakt.movieSummary(title, *args, **argd)

# get shows from trakt server
def getShowsFromTrakt(*args, **argd):
    return Trakt.userLibraryShowsAll(username, *args, **argd)
    
# get easy access to tvshow by tvdb_id
def traktShowListByTvdbID(data):
    trakt_tvshows = {}

    for i in range(0, len(data)):
        trakt_tvshows[data[i]['tvdb_id']] = data[i]
        
    return trakt_tvshows

# get seen tvshows from trakt server
def getWatchedTVShowsFromTrakt(*args, **argd):
    return Trakt.userLibraryShowsWatched(username, *args, **argd)

# set episodes seen on trakt
def setEpisodesSeenOnTrakt(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
    return Trakt.showEpisodeSeen(tvdbId, title, year, episodes, imdbId, *args, **argd)

# set episodes unseen on trakt
def setEpisodesUnseenOnTrakt(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
    return Trakt.showEpisodeUnseen(tvdbId, title, year, episodes, imdbId, *args, **argd)

# set movies seen on trakt
#  - movies, required fields are 'plays', 'last_played' and 'title', 'year' or optionally 'imdb_id'
def setMoviesSeenOnTrakt(movies, *args, **argd):
    return Trakt.movieSeen(movies, *args, **argd)

# set movies unseen on trakt
#  - movies, required fields are 'plays', 'last_played' and 'title', 'year' or optionally 'imdb_id'
def setMoviesUnseenOnTrakt(movies, *args, **argd):
    return Trakt.movieUnseen(movies, *args, **argd)

# get tvshow collection from trakt server
def getTVShowCollectionFromTrakt(*args, **argd):
    return Trakt.userLibraryShowsCollection(username, *args, **argd)

# add a whole tv show to the users collection
def addWholeTvShowToTraktCollection(tvdb_id, title, year, imdb_id=None, *args, **argd):
    return Trakt.showLibrary(tvdbId, title, year, imdbId, *args, **argd)

# add individual episodes of a tshow to the users trakt collection
def addEpisodesToTraktCollection(tvdb_id, title, year, episodes, imdb_id=None, *args, **argd):
    return Trakt.showEpisodeLibrary(tvdbId, title, year, imdbId, *args, **argd)

# remove a whole tv show from the users collection
def removeWholeTvShowFromTraktCollection(tvdb_id, title, year, imdb_id=None, *args, **argd):
    return Trakt.showUnlibrary(tvdbId, title, year, imdbId, *args, **argd)

# remove individual episodes of a tshow from the users trakt collection
def removeEpisodesFromTraktCollection(tvdb_id, title, year, episodes, imdb_id=None, *args, **argd):
    return Trakt.showUnlibrary(tvdbId, title, year, episodes, imdbId, *args, **argd)

# get tvshows from XBMC
def getTVShowsFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows','params':{'properties': ['title', 'year', 'imdbnumber', 'playcount']}, 'id': 1})
    
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
    Debug("getSeasonsFromXBMC: "+str(tvshow))
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetSeasons','params':{'tvshowid': tvshow['tvshowid'], 'fields': ['season']}, 'id': 1})
    
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
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetEpisodes','params':{'tvshowid': tvshow['tvshowid'], 'season': season, 'properties': ['playcount', 'episode']}, 'id': 1})
    
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

# get a single episode from xbmc given the id
def getEpisodeDetailsFromXbmc(libraryId, fields):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetEpisodeDetails','params':{'episodeid': libraryId, 'properties': fields}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    # check for error
    try:
        error = result['error']
        Debug("getEpisodeDetailsFromXbmc: " + str(error))
        return None
    except KeyError:
        pass # no error

    try:
        return result['result']['episodedetails']
    except KeyError:
        Debug("getEpisodeDetailsFromXbmc: KeyError: result['result']['episodedetails']")
        return None

# get movies from XBMC
def getMoviesFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies','params':{'properties': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']}, 'id': 1})

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

# get a single movie from xbmc given the id
def getMovieDetailsFromXbmc(libraryId, fields):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovieDetails','params':{'movieid': libraryId, 'properties': fields}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    # check for error
    try:
        error = result['error']
        Debug("getMovieDetailsFromXbmc: " + str(error))
        return None
    except KeyError:
        pass # no error

    try:
        return result['result']['moviedetails']
    except KeyError:
        Debug("getMovieDetailsFromXbmc: KeyError: result['result']['moviedetails']")
        return None

# sets the playcount of a given movie by imdbid
def setXBMCMoviePlaycount(imdb_id, playcount):

    # httpapi till jsonrpc supports playcount update
    # c09 => IMDB ID
    matches = xbmcHttpapiQuery(
    "SELECT movie.idFile FROM movie"+
    " WHERE movie.c09='%(imdb_id)s'" % {'imdb_id':xcp(imdb_id)})
    
    if not matches:
        #add error message here
        return
    for match in matches:
        result = xbmcHttpapiExec(
        "UPDATE files"+
        " SET playcount=%(playcount)d" % {'playcount':int(playcount)}+
        " WHERE idFile=%(idFile)s" % {'idFile':xcp(match)})
        
        Debug("xml answer: " + str(result))

# sets the playcount of a given episode by tvdb_id
def setXBMCEpisodePlaycount(tvdb_id, seasonid, episodeid, playcount):
    # httpapi till jsonrpc supports playcount update
    # select tvshow by tvdb_id # c12 => TVDB ID # c00 = title
    match = xbmcHttpapiQuery(
    "SELECT tvshow.idShow, tvshow.c00 FROM tvshow"+
    " WHERE tvshow.c12='%(tvdb_id)s'" % {'tvdb_id':xcp(tvdb_id)})
    
    if match:
        Debug("TV Show: " + match[1] + " idShow: " + str(match[0]) + " season: " + str(seasonid) + " episode: " + str(episodeid))

        # select episode table by idShow
        match = xbmcHttpapiQuery(
        "SELECT tvshowlinkepisode.idEpisode FROM tvshowlinkepisode"+
        " WHERE tvshowlinkepisode.idShow=%(idShow)s" % {'idShow':xcp(match[0])})
        
        for idEpisode in match:
            # get idfile from episode table # c12 = season, c13 = episode
            match2 = xbmcHttpapiQuery(
            "SELECT episode.idFile FROM episode"+
            " WHERE episode.idEpisode=%(idEpisode)d" % {'idEpisode':int(idEpisode)}+
            " AND episode.c12='%(seasonid)s'" % {'seasonid':xcp(seasonid)}+
            " AND episode.c13='%(episodeid)s'" % {'episodeid':xcp(episodeid)})
            
            if match2:
                for idFile in match2:
                    Debug("idFile: " + str(idFile) + " setting playcount...")
                    responce = xbmcHttpapiExec(
                    "UPDATE files"+
                    " SET playcount=%(playcount)s" % {'playcount':xcp(playcount)}+
                    " WHERE idFile=%(idFile)s" % {'idFile':xcp(idFile)})
                    
                    Debug("xml answer: " + str(responce))
    else:
        Debug("setXBMCEpisodePlaycount: no tv show found for tvdb id: " + str(tvdb_id))
    
# get current video being played from XBMC
def getCurrentPlayingVideoFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.GetActivePlayers','params':{}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    # check for error
    try:
        error = result['error']
        Debug("[Util] getCurrentPlayingVideoFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error
    
    try:
        for player in result['result']:
            if player['type'] == 'video':
                rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.GetProperties','params':{'playerid': player['playerid'], 'properties':['playlistid', 'position']}, 'id': 1})
                result2 = xbmc.executeJSONRPC(rpccmd)
                result2 = json.loads(result2)
                # check for error
                try:
                    error = result2['error']
                    Debug("[Util] getCurrentPlayingVideoFromXBMC, Player.GetProperties: " + str(error))
                    return None
                except KeyError:
                    pass # no error
                playlistid = result2['result']['playlistid']
                position = result2['result']['position']
                
                rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Playlist.GetItems','params':{'playlistid': playlistid}, 'id': 1})
                result2 = xbmc.executeJSONRPC(rpccmd)
                result2 = json.loads(result2)
                # check for error
                try:
                    error = result2['error']
                    Debug("[Util] getCurrentPlayingVideoFromXBMC, Playlist.GetItems: " + str(error))
                    return None
                except KeyError:
                    pass # no error
                Debug("Current playlist: "+str(result2['result']))
                
                return result2['result'][position]
        Debug("[Util] getCurrentPlayingVideoFromXBMC: No current video player")
        return None
    except KeyError:
        Debug("[Util] getCurrentPlayingVideoFromXBMC: KeyError")
        return None
        
# get the length of the current video playlist being played from XBMC
def getPlaylistLengthFromXBMCPlayer(playerid):
    if playerid == -1:
        return 1 #Default player (-1) can't be checked properly
    if playerid < 0 or playerid > 2:
        Debug("[Util] getPlaylistLengthFromXBMCPlayer, invalid playerid: "+str(playerid))
        return 0
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.GetProperties','params':{'playerid': playerid, 'properties':['playlistid']}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    # check for error
    try:
        error = result['error']
        Debug("[Util] getPlaylistLengthFromXBMCPlayer, Player.GetProperties: " + str(error))
        return 0
    except KeyError:
        pass # no error
    playlistid = result['result']['playlistid']
    
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Playlist.GetProperties','params':{'playlistid': playlistid, 'properties': ['size']}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    # check for error
    try:
        error = result['error']
        Debug("[Util] getPlaylistLengthFromXBMCPlayer, Playlist.GetProperties: " + str(error))
        return 0
    except KeyError:
        pass # no error
    
    return result['result']['size']

def getMovieIdFromXBMC(imdb_id, title):
    # httpapi till jsonrpc supports searching for a single movie
    # Get id of movie by movies IMDB
    Debug("Searching for movie: "+imdb_id+", "+title)
    
    match = xbmcHttpapiQuery(
    " SELECT idMovie FROM movie"+
    "  WHERE c09='%(imdb_id)s'" % {'imdb_id':imdb_id}+
    " UNION"+
    " SELECT idMovie FROM movie"+
    "  WHERE upper(c00)='%(title)s'" % {'title':xcp(title.upper())}+
    " LIMIT 1")
    
    if not match:
        Debug("getMovieIdFromXBMC: cannot find movie in database")
        return -1
        
    return match[0]

def getShowIdFromXBMC(tvdb_id, title):
    # httpapi till jsonrpc supports searching for a single show
    # Get id of show by shows tvdb id
    
    Debug("Searching for show: "+str(tvdb_id)+", "+title)
    
    match = xbmcHttpapiQuery(
    " SELECT idShow FROM tvshow"+
    "  WHERE c12='%(tvdb_id)s'" % {'tvdb_id':xcp(tvdb_id)}+
    " UNION"+
    " SELECT idShow FROM tvshow"+
    "  WHERE upper(c00)='%(title)s'" % {'title':xcp(title.upper())}+
    " LIMIT 1")
    
    if not match:
        Debug("getShowIdFromXBMC: cannot find movie in database")
        return -1
        
    return match[0]

# returns list of movies from watchlist
def getWatchlistMoviesFromTrakt(*args, **argd):
    return Trakt.userWatchlistMovies(username, *args, **argd)

# returns list of tv shows from watchlist
def getWatchlistTVShowsFromTrakt(*args, **argd):
    return Trakt.userWatchlistShows(username, *args, **argd)

# add an array of movies to the watch-list
def addMoviesToWatchlist(movies, *args, **argd):
    return Trakt.movieWatchlist(movies, *args, **argd)

# remove an array of movies from the watch-list
def removeMoviesFromWatchlist(movies, *args, **argd):
    return Trakt.movieUnwatchlist(movies, *args, **argd)

# add an array of tv shows to the watch-list
def addTVShowsToWatchlist(shows, *args, **argd):
    return Trakt.showWatchlist(shows, *args, **argd)

# remove an array of tv shows from the watch-list
def removeTVShowsFromWatchlist(shows, *args, **argd):
    return Trakt.showUnwatchlist(shows, *args, **argd)

#Set the rating for a movie on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateMovieOnTrakt(movie, rating, *args, **argd):
    return Trakt.rateMovie(movie['imdb_id'], movie['title'], movie['year'], rating, movie['tmdb_id'], *args, **argd)

#Get the rating for a movie from trakt
def getMovieRatingFromTrakt(imdbid, title, year, *args, **argd):
    if imdbid is None or imdbid == "":
        data = Trakt.movieSummary(title, *args, **argd)
    else:
        data = Trakt.movieSummary(imdbid, *args, **argd)
    
    if data == None:
        return None
        
    if 'rating' in data:
        return data['rating']
        
    Debug("Error in request from 'getMovieRatingFromTrakt()'")
    return None

#Set the rating for a tv episode on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateEpisodeOnTrakt(tvdbId, title, year, season, episode, rating, imdbId=None, *args, **argd):
    return Trakt.rateEpisode(tvdbId, title, year, season, episode, rating, imdbId, *args, **argd)
    
#Get the rating for a tv episode from trakt
def getEpisodeRatingFromTrakt(tvdbid, title, year, season, episode, *args, **argd):
    if tvdbid is None or tvdbid == "":
        data = Trakt.showEpisodeSummary(title, season, episode, *args, **argd)
    else:
        data = Trakt.showEpisodeSummary(tvdbid, season, episode, *args, **argd)
        
    if data == None:
        return None
        
    if 'rating' in data:
        return data['rating']
        
    Debug("Error in request from 'getEpisodeRatingFromTrakt()'")
    return None

#Set the rating for a tv show on trakt, rating: "hate" = Weak sauce, "love" = Totaly ninja
def rateShowOnTrakt(tvdbid, title, year, rating, imdbId=None, *args, **argd):
    return Trakt.rateShow(tvdbId, title, year, rating, imdbId, *args, **argd)

#Get the rating for a tv show from trakt
def getShowRatingFromTrakt(tvdbid, title, year):
    if imdbid is None or imdbid == "":
        data = Trakt.showSummary(title, extended=None, *args, **argd)
    else:
        data = Trakt.showSummary(tvdbid, extended=None, *args, **argd)
        
    if data == None:
        return None
        
    if 'rating' in data:
        return data['rating']
        
    Debug("Error in request from 'getShowRatingFromTrakt()'")
    return None

def getRecommendedMoviesFromTrakt(*args, **argd):
    return Trakt.recommendationsMovies(*args, **argd)

def getRecommendedTVShowsFromTrakt(*args, **argd):
    return Trakt.recommendationsShows(*args, **argd)

def getTrendingMoviesFromTrakt(*args, **argd):
    return Trakt.moviesTrending(*args, **argd)

def getTrendingTVShowsFromTrakt(*args, **argd):
    return Trakt.showsTrending(*args, **argd)

def getFriendsFromTrakt(*args, **argd):
    return Trakt.userFriends(username, *args, **argd)

def getWatchingFromTraktForUser(name, *args, **argd):
    return Trakt.userWatching(name, *args, **argd)
    
def playMovieById(idMovie = None, options = None):
    if (idMovie is None and options is None): return
    if (idMovie is None):
        if len(options) == 1:
            idMovie = options[0]
        else:
            choices = []
            for item in options:
                rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovieDetails', 'params': {'movieid': item, 'properties': ['file', 'streamdetails', 'runtime']}, 'id': 1})
                result = xbmc.executeJSONRPC(rpccmd)
                result = json.loads(result)
                if result is None or 'error' in result:
                    del options[item]
                    continue
                details = result['result']['moviedetails']
                choices.append(unicode("("+str(details['runtime'])+" Minutes) "+repr(details['streamdetails']))+" - "+unicode(details['file']))
            
            if len(options) == 1:
                idMovie = options[0]
            else:
                while True:
                    select = xbmcgui.Dialog().select("Which one do you want to play ?", choices)
                    Debug("Select: " + str(select))
                    if select == -1:
                        Debug ("menu quit by user")
                        return
                    elif select <= len(choices):
                        idMovie = options[select]
                        break
        
    Debug("Play Movie requested for id: "+str(idMovie))
    if idMovie == -1:
        return # invalid movie id
    else:
        rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.Open', 'params': {'item': {'movieid': int(idMovie)}}, 'id': 1})
        result = xbmc.executeJSONRPC(rpccmd)
        result = json.loads(result)
        
        # check for error
        try:
            error = result['error']
            Debug("playMovieById, Player.Open: " + str(error))
            return None
        except KeyError:
            pass # no error
            
        try:
            if result['result'] == "OK":
                if xbmc.Player().isPlayingVideo():
                    return True
            notification("Trakt Utilities", __language__(1302).encode( "utf-8", "ignore" )) # Unable to play movie
        except KeyError:
            Debug("playMovieById, VideoPlaylist.Play: KeyError")
            return None

###############################
##### Scrobbling to trakt #####
###############################

#tell trakt that the user is watching a movie
def watchingMovieOnTrakt(movie, progress, *args, **argd):
    duration = 90
    if 'runtime' in movie: duration = movie['runtime']
    return Trakt.movieWatching(movie['imdb_id'], movie['title'], movie['year'], duration, progress, *args, **argd)

#tell trakt that the user is watching an episode
def watchingEpisodeOnTrakt(tvdbId, title, year, season, episode, duration, progess, imdbId=None, *args, **argd):
    return Trakt.showWatching(tvdbId, title, year, season, episode, duration, progess, imdbId, *args, **argd)

#tell trakt that the user has stopped watching a movie
def cancelWatchingMovieOnTrakt(*args, **argd):
    return Trakt.movieCancelWatching(*args, **argd)

#tell trakt that the user has stopped an episode
def cancelWatchingEpisodeOnTrakt(*args, **argd):
    return Trakt.showCancelWatching(*args, **argd)

#tell trakt that the user has finished watching an movie
def scrobbleMovieOnTrakt(movie, progress, *args, **argd):
    duration = 90
    if 'runtime' in movie: duration = movie['runtime']
    return Trakt.movieScrobble(movie['imdb_id'], movie['title'], movie['year'], duration, progress, *args, **argd)

#tell trakt that the user has finished watching an episode
def scrobbleEpisodeOnTrakt(tvdbId, title, year, season, episode, duration, progess, imdbId=None, *args, **argd):
    return Trakt.showScrobble(tvdbId, title, year, season, episode, duration, progess, imdbId, *args, **argd)

            
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
