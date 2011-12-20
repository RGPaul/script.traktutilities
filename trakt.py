    # -*- coding: utf-8 -*-
# 

import os, sys
import xbmc,xbmcaddon,xbmcgui
import time, socket

try: import simplejson as json
except ImportError: import json

from nbhttpconnection import *
from utilities import Debug, notification

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

class Trakt():

    # get a connection to trakt
    @staticmethod
    def getConnection():
        try:
            conn = NBHTTPConnection('api.trakt.tv')
        except socket.timeout:
            Debug("[Trakt] getConnection: can't connect to trakt - timeout")
            notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" ) + ": timeout") # can't connect to trakt
            return None
        return conn

    # make a JSON api request to trakt
    # method: http method (GET or POST)
    # req: REST request (ie '/user/library/movies/all.json/%%API_KEY%%/%%USERNAME%%')
    # args: arguments to be passed by POST JSON (only applicable to POST requests), default:{}
    # returnStatus: when unset or set to false the function returns None apon error and shows a notification,
    #   when set to true the function returns the status and errors in ['error'] as given to it and doesn't show the notification,
    #   use to customise error notifications
    # anon: anonymous (dont send username/password), default:False
    # connection: default it to make a new connection but if you want to keep the same one alive pass it here
    # daemon: default is False, when true it disable any error notifications (but not debug messages)
    # passVersions: default is False, when true it passes extra version information to trakt to help debug problems
    @staticmethod
    def jsonRequest(method, req, args={}, returnStatus=False, anon=False, conn=False, daemon=False, passVersions=False, **argd):
        closeConnection = False
        if conn == False:
            conn = Trakt.getConnection()
            closeConnection = True
        if conn == None:
            if returnStatus:
                data = {}
                data['status'] = 'failure'
                data['error'] = 'Unable to connect to trakt'
                return data
            return None

        args.update(argd)
        try:
            req = req.replace("%%API_KEY%%",apikey)
            req = req.replace("%%USERNAME%%",username)
            if method == 'POST':
                if not anon:
                    args['username'] = username
                    args['password'] = pwd
                if passVersions:
                    args['plugin_version'] = __settings__.getAddonInfo("version")
                    args['media_center'] = 'xbmc'
                    args['media_center_version'] = xbmc.getInfoLabel("system.buildversion")
                    args['media_center_date'] = xbmc.getInfoLabel("system.builddate")
                jdata = json.dumps(args)
                conn.request('POST', req, jdata)
            elif method == 'GET':
                conn.request('GET', req)
            else:
                return None
            Debug("trakt json url: "+req)
        except socket.error:
            Debug("traktQuery: can't connect to trakt")
            if not daemon: notification("Trakt Utilities", __language__(1108).encode( "utf-8", "ignore" )) # can't connect to trakt
            if returnStatus:
                data = {}
                data['status'] = 'failure'
                data['error'] = 'Socket error, unable to connect to trakt'
                return data;
            return None
         
        conn.go()
        
        while True:
            if xbmc.abortRequested:
                Debug("Broke loop due to abort")
                if returnStatus:
                    data = {}
                    data['status'] = 'failure'
                    data['error'] = 'Abort requested, not waiting for responce'
                    return data;
                return None
            if conn.hasResult():
                break
            time.sleep(0.1)
    
        response = conn.getResult()
        raw = response.read()
        if closeConnection:
            conn.close()
        
        try:
            data = json.loads(raw)
        except ValueError:
            Debug("traktQuery: Bad JSON responce: "+repr(raw))
            if returnStatus:
                data = {}
                data['status'] = 'failure'
                data['error'] = 'Bad responce from trakt'
                return data
            if not daemon: notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": Bad responce from trakt") # Error
            return None
        
        if 'status' in data:
            if data['status'] == 'failure':
                Debug("traktQuery: Error: " + str(data['error']))
                if returnStatus:
                    return data;
                if not daemon: notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": " + str(data['error'])) # Error
                return None
        
        return data
    
    @staticmethod
    def accountCreate(email, *args, **argd):
        data = Trakt.jsonRequest('POST', '/account/create/%%API_KEY%%', {'email': email}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountCreate()'")
        return data
        
    @staticmethod
    def accountTest(*args, **argd):
        data = Trakt.jsonRequest('POST', '/account/test/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activityCommunity(types='all', actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/community.json/%%API_KEY%%/'+str(types)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activityEpisodes(title, season, episode, actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/episodes.json/%%API_KEY%%/'+str(title)+'/'+str(season)+'/'+str(episode)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activityFriends(types='all', actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/friends/%%API_KEY%%/'+str(types)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activityMovies(title, actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/movies.json/%%API_KEY%%/'+str(title)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activitySeasons(title, season, actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/seasons.json/%%API_KEY%%/'+str(title)+'/'+str(season)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activityShows(title, actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/shows.json/%%API_KEY%%/'+str(title)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def activityUsers(username, types='all', actions='all', timestamp=None, *args, **argd):
        if timestamp is None:
            timestamp = ""
        else: 
            timestamp = '/'+str(timestamp)
        data = Trakt.jsonRequest('POST', '/activity/user.json/%%API_KEY%%/'+str(username)+'/'+str(types)+'/'+str(actions)+timestamp, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'accountTest()'")
        return data
        
    @staticmethod
    def calendarPremieres(date=None, days=None, *args, **argd):
        ext = ""
        if date is not None:
            ext = "/"+str(date) #YYYYMMDD
            if days is not None:
                ext += "/"+str(days)
        data = Trakt.jsonRequest('POST', '/calendar/premieres.json/%%API_KEY%%'+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'calendarPremieres()'")
        return data
        
    @staticmethod
    def calendarShows(date=None, days=None, *args, **argd):
        ext = ""
        if date is not None:
            ext = "/"+str(date) #YYYYMMDD
            if days is not None:
                ext += "/"+str(days)
        data = Trakt.jsonRequest('POST', '/calendar/shows.json/%%API_KEY%%'+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'calendarShows()'")
        return data
        
    @staticmethod
    def friendsAdd(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/add/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsAdd()'")
        return data
        
    @staticmethod
    def friendsAll(*args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/all/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsAll()'")
        return data
        
    @staticmethod
    def friendsApprove(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/approve/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsApprove()'")
        return data
        
    @staticmethod
    def friendsDelete(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/delete/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsDelete()'")
        return data
        
    @staticmethod
    def friendsDeny(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/deny/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsDeny()'")
        return data
        
    @staticmethod
    def friendsRequests(*args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/requests/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsRequests()'")
        return data
        
    @staticmethod
    def genresMovies(*args, **argd):
        data = Trakt.jsonRequest('POST', '/genres/movies.json/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'genresMovies()'")
        return data
        
    @staticmethod
    def genresShows(*args, **argd):
        data = Trakt.jsonRequest('POST', '/genres/shows.json/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'genresShows()'")
        return data
        
    @staticmethod
    def listsAdd(name, description, privacy, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/add/%%API_KEY%%', {'name': name, 'description': description, 'privacy': privacy}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsAdd()'")
        return data
        
    @staticmethod
    def listsDelete(slug, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/delete/%%API_KEY%%', {'slug': slug}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsDelete()'")
        return data
        
    @staticmethod
    def listsItemsAdd(slug, items, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/items/add/%%API_KEY%%', {'slug': slug, 'items': items}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsItemsAdd()'")
        return data
        
    @staticmethod
    def listsItemsDelete(slug, items, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/items/delete/%%API_KEY%%', {'slug': slug, 'items': items}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsItemsDelete()'")
        return data
        
    @staticmethod
    def listsUpdate(slug, name=None, description=None, privacy=None, *args, **argd):
        data = {'slug': slug}
        if name is not None: data['name'] = name
        if description is not None: data['description'] = description
        if privacy is not None: data['privacy'] = privacy
        data = Trakt.jsonRequest('POST', '/lists/update/%%API_KEY%%', data, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsUpdate()'")
        return data
        
    @staticmethod
    def movieCancelWatching(*args, **argd):
        argd['passVersions'] = True
        data = Trakt.jsonRequest('POST', '/movie/cancelwatching/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieCancelWatching()'")
        return data
        
    @staticmethod
    def movieScrobble(imdbId, title, year, duration, progress, tmdbId=None, *args, **argd):
        argd['passVersions'] = True
        data = Trakt.jsonRequest('POST', '/movie/scrobble/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'duration': duration, 'progress': progress, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieScrobble()'")
        return data
        
    @staticmethod
    def movieSeen(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/seen/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieSeen()'")
        return data
        
    @staticmethod
    def movieLibrary(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/library/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieLibrary()'")
        return data
        
    @staticmethod
    def movieShouts(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/shouts.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieShouts()'")
        return data
        
    @staticmethod
    def movieSummary(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/summary.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieSummary()'")
        return data
        
    @staticmethod
    def movieUnlibrary(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/unlibrary/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieUnlibrary()'")
        return data
        
    @staticmethod
    def movieUnseen(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/unseen/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieUnseen()'")
        return data
        
    @staticmethod
    def movieUnwatchlist(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/unwatchlist/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieUnwatchlist()'")
        return data
        
    @staticmethod
    def movieWatching(imdbId, title, year, duration, progress, tmdbId=None, *args, **argd):
        argd['passVersions'] = True
        data = Trakt.jsonRequest('POST', '/movie/watching/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'duration': duration, 'progress': progress, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieWatching()'")
        return data
        
    @staticmethod
    def movieWatchingNow(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/watchingnow.json/%%API_KEY%%', {'title': title}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieWatchingNow()'")
        return data
        
    @staticmethod
    def movieWatchlist(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/watchlist/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieWatchlist()'")
        return data
        
    @staticmethod
    def moviesTrending(*args, **argd):
        data = Trakt.jsonRequest('POST', '/movies/trending.json/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'moviesTrending()'")
        return data
        
    @staticmethod
    def rateEpisode(tvdbId, title, year, season, episode, rating, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/rate/episode/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'rating': rating, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'rateEpisode()'")
        return data
        
    @staticmethod
    def rateMovie(imdbId, title, year, rating, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/rate/movie/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'rating': rating, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'rateMovie()'")
        return data
        
    @staticmethod
    def rateShow(tvdbId, title, year, rating, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/rate/show/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'rating': rating, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'rateShow()'")
        return data
        
    @staticmethod
    def recommendationsMovies(genre=None, startYear=None, endYear=None, *args, **argd):
        data = {}
        if genre is not None: data['genre'] = genre
        if startYear is not None: data['startYear'] = startYear
        if endYear is not None: data['endYear'] = endYear
        data = Trakt.jsonRequest('POST', '/recommendations/movies/%%API_KEY%%', data, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsMovies()'")
        return data
        
    @staticmethod
    def recommendationsMoviesDismiss(imdbId, title, year, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/recommendations/movies/dismiss/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsMoviesDismiss()'")
        return data
        
    @staticmethod
    def recommendationsShows(genre=None, startYear=None, endYear=None, *args, **argd):
        data = {}
        if genre is not None: data['genre'] = genre
        if startYear is not None: data['startYear'] = startYear
        if endYear is not None: data['endYear'] = endYear
        data = Trakt.jsonRequest('POST', '/recommendations/shows/%%API_KEY%%', data, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsShows()'")
        return data
        
    @staticmethod
    def recommendationsShowsDismiss(tvdbId, title, year, *args, **argd):
        data = Trakt.jsonRequest('POST', '/recommendations/shows/dismiss/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsShowsDismiss()'")
        return data
        
    @staticmethod
    def searchEpisodes(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/episodes.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchEpisodes()'")
        return data
        
    @staticmethod
    def searchMovies(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/movies.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchMovies()'")
        return data
        
    @staticmethod
    def searchPeople(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/people.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchPeople()'")
        return data
        
    @staticmethod
    def searchShows(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/shows.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchShows()'")
        return data
        
    @staticmethod
    def searchUsers(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/users.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchUsers()'")
        return data
        
    @staticmethod
    def shoutEpisode(tvdbId, title, year, season, episode, shout, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/shout/episode/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'shout': shout, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'shoutEpisode()'")
        return data
        
    @staticmethod
    def shoutMovie(imdbId, title, year, shout, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/shout/movie/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'shout': shout, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'shoutMovie()'")
        return data
        
    @staticmethod
    def shoutShow(tvdbId, title, year, shout, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/shout/show/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'shout': shout, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'shoutShow()'")
        return data
        
    @staticmethod
    def showCancelWatching(*args, **argd):
        argd['passVersions'] = True
        data = Trakt.jsonRequest('POST', '/show/cancelwatching/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showCancelWatching()'")
        return data
        
    @staticmethod
    def showEpisodeLibrary(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/library/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeLibrary()'")
        return data
        
    @staticmethod
    def showEpisodeSeen(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/seen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeSeen()'")
        return data
        
    @staticmethod
    def showEpisodeShouts(title, season, episode, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/shouts.json/%%API_KEY%%/'+str(title)+"/"+str(season)+"/"+str(episode), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeShouts()'")
        return data
        
    @staticmethod
    def showEpisodeSummary(title, season, episode, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/summary.json/%%API_KEY%%/'+str(title)+"/"+str(season)+"/"+str(episode), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeSummary()'")
        return data
        
    @staticmethod
    def showEpisodeUnlibrary(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/unlibrary/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeUnlibrary()'")
        return data
        
    @staticmethod
    def showEpisodeUnseen(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/unseen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeUnseen()'")
        return data
        
    @staticmethod
    def showEpisodeUnwatchlist(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/unwatchlist/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeUnwatchlist()'")
        return data
        
    @staticmethod
    def showEpisodeWatchingNow(title, season, episode, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/watchingnow/%%API_KEY%%/'+str(title)+"/"+str(season)+"/"+str(episode), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeWatchingNow()'")
        return data
        
    @staticmethod
    def showEpisodeWatchlist(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/watchlist/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeWatchlist()'")
        return data
        
    @staticmethod
    def showLibrary(tvdbId, title, year, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/library/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showLibrary()'")
        return data
        
    @staticmethod
    def showScrobble(tvdbId, title, year, season, episode, duration, progess, imdbId=None, *args, **argd):
        argd['passVersions'] = True
        data = Trakt.jsonRequest('POST', '/show/scrobble/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progess': progess, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showScrobble()'")
        return data
        
    @staticmethod
    def showSeason(title, season, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/season.json/%%API_KEY%%/'+str(title)+"/"+str(season), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeason()'")
        return data
        
    @staticmethod
    def showSeasonLibrary(tvdbId, title, year, season, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/season/library/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeasonLibrary()'")
        return data
        
    @staticmethod
    def showSeasonSeen(tvdbId, title, year, season, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/season/seen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeasonSeen()'")
        return data
        
    @staticmethod
    def showSeasons(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/seasons.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeasons()'")
        return data
        
    @staticmethod
    def showSeen(tvdbId, title, year, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/seen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeen()'")
        return data
        
    @staticmethod
    def showShouts(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/shouts.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showShouts()'")
        return data
        
    @staticmethod
    def showSummary(title, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/show/summary.json/%%API_KEY%%/'+str(title)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSummary()'")
        return data
        
    @staticmethod
    def showUnlibrary(tvdbId, title, year, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/unlibrary/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showUnlibrary()'")
        return data
        
    @staticmethod
    def showUnwatchlist(shows, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/unwatchlist/%%API_KEY%%', {'shows': shows}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showUnwatchlist()'")
        return data
        
    @staticmethod
    def showWatching(tvdbId, title, year, season, episode, duration, progess, imdbId=None, *args, **argd):
        argd['passVersions'] = True
        data = Trakt.jsonRequest('POST', '/show/watching/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progess': progess, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showWatching()'")
        return data
        
    @staticmethod
    def showWatchingNow(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/watchingnow.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showWatchingNow()'")
        return data
        
    @staticmethod
    def showWatchlist(shows, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/watchlist/%%API_KEY%%', {'shows': shows}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showWatchlist()'")
        return data
        
    @staticmethod
    def showsTrending(*args, **argd):
        data = Trakt.jsonRequest('POST', '/shows/trending/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showsTrending()'")
        return data
        
    @staticmethod
    def userCalendarShows(username, date=None, days=None, *args, **argd):
        ext = ""
        if date is not None:
            ext = "/"+str(date) #YYYYMMDD
            if days is not None:
                ext += "/"+str(days)
        data = Trakt.jsonRequest('POST', '/user/calendar/shows.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userCalendarShows()'")
        return data
        
    @staticmethod
    def userFriends(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/friends.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userFriends()'")
        return data
        
    @staticmethod
    def userLibraryMoviesAll(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/all.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesAll()'")
        return data
        
    @staticmethod
    def userLibraryMoviesCollection(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/collection.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesCollection()'")
        return data
        
    @staticmethod
    def userLibraryMoviesHated(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/hated.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesHated()'")
        return data
        
    @staticmethod
    def userLibraryMoviesLoved(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/loved.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesLoved()'")
        return data
        
    @staticmethod
    def userLibraryShowsAll(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/all.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsAll()'")
        return data
        
    @staticmethod
    def userLibraryShowsCollection(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/collection.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsCollection()'")
        return data
        
    @staticmethod
    def userLibraryShowsHated(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/hated.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsHated()'")
        return data
        
    @staticmethod
    def userLibraryShowsLoved(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/loved.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsLoved()'")
        return data
        
    @staticmethod
    def userLibraryShowsWatched(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/watched.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsWatched()'")
        return data
        
    @staticmethod
    def userList(username, slug, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/list.json/%%API_KEY%%/'+str(username)+"/"+str(slug), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userList()'")
        return data
        
    @staticmethod
    def userLists(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/lists.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLists()'")
        return data
        
    @staticmethod
    def userProfile(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/profile.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userProfile()'")
        return data
        
    @staticmethod
    def userWatched(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watched.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatched()'")
        return data
        
    @staticmethod
    def userWatchedEpisodes(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watched/episodes.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchedEpisodes()'")
        return data
        
    @staticmethod
    def userWatchedMovies(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watched/movies.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchedMovies()'")
        return data
        
    @staticmethod
    def userWatching(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watching.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatching()'")
        return data
        
    @staticmethod
    def userWatchlistEpisodes(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watchlist/episodes.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchlistEpisodes()'")
        return data
        
    @staticmethod
    def userWatchlistMovies(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watchlist/movies.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchlistMovies()'")
        return data
        
    @staticmethod
    def userWatchlistShows(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watchlist/shows.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchlistShows()'")
        return data
        
    @staticmethod
    def testAll():
        tests = [
            {'f': Trakt.accountCreate, 'args': ["test@example.com"], 'argd': {'anon': True, 'username': "tester123456789", 'password': "password"}},
            {'f': Trakt.accountTest, 'args': [], 'argd': {}},
            {'f': Trakt.calendarPremieres, 'args': [], 'argd': {}},
            {'f': Trakt.calendarPremieres, 'args': ["20110421"], 'argd': {}},
            {'f': Trakt.calendarPremieres, 'args': ["20110421", 3], 'argd': {}},
            {'f': Trakt.calendarShows, 'args': [], 'argd': {}},
            {'f': Trakt.calendarShows, 'args': ["20110421"], 'argd': {}},
            {'f': Trakt.calendarShows, 'args': ["20110421", 3], 'argd': {}},
            {'f': Trakt.friendsAdd, 'args': ["justin"], 'argd': {}},
            {'f': Trakt.friendsAll, 'args': [], 'argd': {}},
        ]
        failsBasic = []
        failsWithStatus = []
        for test in tests:
            if not Trakt.testBasic(test['f'], *test['args'], **test['argd']):
                failsBasic.append(test)
            if not Trakt.testWithStatus(test['f'], *test['args'], **test['argd']):
                failsWithStatus.append(test)
                
        Debug("[Test] Testing trakt api call (basic), these failed: "+repr(failsBasic))
        Debug("[Test] Testing trakt api call (with status), these failed: "+repr(failsWithStatus))
                
        if len(failsBasic) == 0 and len(failsWithStatus) == 0:
            return True
        return False
        
    @staticmethod
    def testBasic(function, *args, **argd):
        Debug("[Test] Testing trakt api call (basic), function: " + repr(function))
        argd['daemon'] = True
        responce = function(*args, **argd)
        if responce is None:
            Debug("[Test] trakt api call "+repr(function)+" failed, NoneType returned")
            return False
        Debug("[Test] trakt api call "+repr(function)+" passed")
        return True
    
    @staticmethod
    def testWithStatus(function, *args, **argd):
        Debug("[Test] Testing trakt api call (with status), function: " + repr(function))
        argd['returnStatus'] = True
        argd['daemon'] = True
        responce = function(*args, **argd)
        if responce is None:
            Debug("[Test] trakt api call "+repr(function)+" failed, NoneType returned")
            return False
        if 'status' in responce and responce['status'] == 'failure':
            if 'error' not in responce:
                Debug("[Test] trakt api call "+repr(function)+" failed, error message ommitted")
                return False
            Debug("[Test] trakt api call "+repr(function)+" failed, error: "+repr(responce['error']))
            return False
        Debug("[Test] trakt api call "+repr(function)+" passed, responce")
        return True
        
        """
    @staticmethod
    def friendsAll(*args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/all/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsAll()'")
        return data
        
    @staticmethod
    def friendsApprove(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/approve/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsApprove()'")
        return data
        
    @staticmethod
    def friendsDelete(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/delete/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsDelete()'")
        return data
        
    @staticmethod
    def friendsDeny(friend, *args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/deny/%%API_KEY%%', {'friend': friend}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsDeny()'")
        return data
        
    @staticmethod
    def friendsRequests(*args, **argd):
        data = Trakt.jsonRequest('POST', '/friends/requests/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'friendsRequests()'")
        return data
        
    @staticmethod
    def genresMovies(*args, **argd):
        data = Trakt.jsonRequest('POST', '/genres/movies.json/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'genresMovies()'")
        return data
        
    @staticmethod
    def genresShows(*args, **argd):
        data = Trakt.jsonRequest('POST', '/genres/shows.json/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'genresShows()'")
        return data
        
    @staticmethod
    def listsAdd(name, description, privacy, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/add/%%API_KEY%%', {'name': name, 'description': description, 'privacy': privacy}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsAdd()'")
        return data
        
    @staticmethod
    def listsDelete(slug, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/delete/%%API_KEY%%', {'slug': slug}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsDelete()'")
        return data
        
    @staticmethod
    def listsItemsAdd(slug, items, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/items/add/%%API_KEY%%', {'slug': slug, 'items': items}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsItemsAdd()'")
        return data
        
    @staticmethod
    def listsItemsDelete(slug, items, *args, **argd):
        data = Trakt.jsonRequest('POST', '/lists/items/delete/%%API_KEY%%', {'slug': slug, 'items': items}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsItemsDelete()'")
        return data
        
    @staticmethod
    def listsUpdate(slug, name=None, description=None, privacy=None, *args, **argd):
        data = {'slug': slug}
        if name is not None: data['name'] = name
        if description is not None: data['description'] = description
        if privacy is not None: data['privacy'] = privacy
        data = Trakt.jsonRequest('POST', '/lists/update/%%API_KEY%%', data, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'listsUpdate()'")
        return data
        
    @staticmethod
    def movieCancelWatching(*args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/cancelwatching/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieCancelWatching()'")
        return data
        
    @staticmethod
    def movieScrobble(imdbId, title, year, duration, progress, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/scrobble/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'duration': duration, 'progress': progress, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieScrobble()'")
        return data
        
    @staticmethod
    def movieSeen(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/seen/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieSeen()'")
        return data
        
    @staticmethod
    def movieLibrary(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/library/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieLibrary()'")
        return data
        
    @staticmethod
    def movieShouts(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/shouts.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieShouts()'")
        return data
        
    @staticmethod
    def movieSummary(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/summary.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieSummary()'")
        return data
        
    @staticmethod
    def movieUnlibrary(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/unlibrary/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieUnlibrary()'")
        return data
        
    @staticmethod
    def movieUnseen(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/unseen/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieUnseen()'")
        return data
        
    @staticmethod
    def movieUnwatchlist(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/unwatchlist/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieUnwatchlist()'")
        return data
        
    @staticmethod
    def movieWatching(imdbId, title, year, duration, progress, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/watching/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'duration': duration, 'progress': progress, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieWatching()'")
        return data
        
    @staticmethod
    def movieWatchingNow(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/watchingnow.json/%%API_KEY%%', {'title': title}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieWatchingNow()'")
        return data
        
    @staticmethod
    def movieWatchlist(movies, *args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/watchlist/%%API_KEY%%', {'movies': movies}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'movieWatchlist()'")
        return data
        
    @staticmethod
    def moviesTrending(*args, **argd):
        data = Trakt.jsonRequest('POST', '/movie/trending.json/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'moviesTrending()'")
        return data
        
    @staticmethod
    def rateEpisode(tvdbId, title, year, season, episode, rating, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/rate/episode/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'rating': rating, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'rateEpisode()'")
        return data
        
    @staticmethod
    def rateMovie(imdbId, title, year, rating, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/rate/movie/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'rating': rating, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'rateMovie()'")
        return data
        
    @staticmethod
    def rateShow(tvdbId, title, year, rating, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/rate/show/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'rating': rating, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'rateShow()'")
        return data
        
    @staticmethod
    def recommendationsMovies(genre=None, startYear=None, endYear=None, *args, **argd):
        data = {}
        if genre is not None: data['genre'] = genre
        if startYear is not None: data['startYear'] = startYear
        if endYear is not None: data['endYear'] = endYear
        data = Trakt.jsonRequest('POST', '/recommendations/movies/%%API_KEY%%', data, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsMovies()'")
        return data
        
    @staticmethod
    def recommendationsMoviesDismiss(imdbId, title, year, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/recommendations/movies/dismiss/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsMoviesDismiss()'")
        return data
        
    @staticmethod
    def recommendationsShows(genre=None, startYear=None, endYear=None, *args, **argd):
        data = {}
        if genre is not None: data['genre'] = genre
        if startYear is not None: data['startYear'] = startYear
        if endYear is not None: data['endYear'] = endYear
        data = Trakt.jsonRequest('POST', '/recommendations/shows/%%API_KEY%%', data, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsShows()'")
        return data
        
    @staticmethod
    def recommendationsShowsDismiss(tvdbId, title, year, *args, **argd):
        data = Trakt.jsonRequest('POST', '/recommendations/shows/dismiss/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'recommendationsShowsDismiss()'")
        return data
        
    @staticmethod
    def searchEpisodes(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/episodes.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchEpisodes()'")
        return data
        
    @staticmethod
    def searchMovies(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/movies.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchMovies()'")
        return data
        
    @staticmethod
    def searchPeople(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/people.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchPeople()'")
        return data
        
    @staticmethod
    def searchShows(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/shows.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchShows()'")
        return data
        
    @staticmethod
    def searchUsers(query, *args, **argd):
        data = Trakt.jsonRequest('POST', '/search/users.json/%%API_KEY%%/'+str(query), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'searchUsers()'")
        return data
        
    @staticmethod
    def shoutEpisode(tvdbId, title, year, season, episode, shout, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/shout/episode/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'shout': shout, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'shoutEpisode()'")
        return data
        
    @staticmethod
    def shoutMovie(imdbId, title, year, shout, tmdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/shout/movie/%%API_KEY%%', {'imdb_id': imdbId, 'title': title, 'year': year, 'shout': shout, 'tmdb_id': tmdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'shoutMovie()'")
        return data
        
    @staticmethod
    def shoutShow(tvdbId, title, year, shout, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/shout/show/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'shout': shout, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'shoutShow()'")
        return data
        
    @staticmethod
    def showCancelWatching(*args, **argd):
        data = Trakt.jsonRequest('POST', '/show/cancelwatching/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showCancelWatching()'")
        return data
        
    @staticmethod
    def showEpisodeLibrary(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/library/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeLibrary()'")
        return data
        
    @staticmethod
    def showEpisodeSeen(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/seen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeSeen()'")
        return data
        
    @staticmethod
    def showEpisodeShouts(title, season, episode, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/shouts.json/%%API_KEY%%/'+str(title)+"/"+str(season)+"/"+str(episode), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeShouts()'")
        return data
        
    @staticmethod
    def showEpisodeSummary(title, season, episode, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/summary.json/%%API_KEY%%/'+str(title)+"/"+str(season)+"/"+str(episode), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeSummary()'")
        return data
        
    @staticmethod
    def showEpisodeUnlibrary(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/unlibrary/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeUnlibrary()'")
        return data
        
    @staticmethod
    def showEpisodeUnseen(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/unseen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeUnseen()'")
        return data
        
    @staticmethod
    def showEpisodeUnwatchlist(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/unwatchlist/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeUnwatchlist()'")
        return data
        
    @staticmethod
    def showEpisodeWatchingNow(title, season, episode, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/watchingnow/%%API_KEY%%/'+str(title)+"/"+str(season)+"/"+str(episode), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeWatchingNow()'")
        return data
        
    @staticmethod
    def showEpisodeWatchlist(tvdbId, title, year, episodes, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/episode/watchlist/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'episodes': episodes, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showEpisodeWatchlist()'")
        return data
        
    @staticmethod
    def showLibrary(tvdbId, title, year, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/library/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showLibrary()'")
        return data
        
    @staticmethod
    def showScrobble(tvdbId, title, year, season, episode, duration, progess, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/scrobble/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progess': progess, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showScrobble()'")
        return data
        
    @staticmethod
    def showSeason(title, season, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/season.json/%%API_KEY%%/'+str(title)+"/"+str(season), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeason()'")
        return data
        
    @staticmethod
    def showSeasonLibrary(tvdbId, title, year, season, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/season/library/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeasonLibrary()'")
        return data
        
    @staticmethod
    def showSeasonSeen(tvdbId, title, year, season, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/season/seen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeasonSeen()'")
        return data
        
    @staticmethod
    def showSeasons(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/seasons.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeasons()'")
        return data
        
    @staticmethod
    def showSeen(tvdbId, title, year, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/seen/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSeen()'")
        return data
        
    @staticmethod
    def showShouts(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/shouts.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showShouts()'")
        return data
        
    @staticmethod
    def showSummary(title, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/show/summary.json/%%API_KEY%%/'+str(title)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showSummary()'")
        return data
        
    @staticmethod
    def showUnlibrary(tvdbId, title, year, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/unlibrary/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showUnlibrary()'")
        return data
        
    @staticmethod
    def showUnwatchlist(shows, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/unwatchlist/%%API_KEY%%', {'shows': shows}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showUnwatchlist()'")
        return data
        
    @staticmethod
    def showWatching(tvdbId, title, year, season, episode, duration, progess, imdbId=None, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/watching/%%API_KEY%%', {'tvdb_id': tvdbId, 'title': title, 'year': year, 'season': season, 'episode': episode, 'duration': duration, 'progess': progess, 'imdb_id': imdbId}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showWatching()'")
        return data
        
    @staticmethod
    def showWatchingNow(title, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/watchingnow.json/%%API_KEY%%/'+str(title), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showWatchingNow()'")
        return data
        
    @staticmethod
    def showWatchlist(shows, *args, **argd):
        data = Trakt.jsonRequest('POST', '/show/watchlist/%%API_KEY%%', {'shows': shows}, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showWatchlist()'")
        return data
        
    @staticmethod
    def showsTrending(*args, **argd):
        data = Trakt.jsonRequest('POST', '/shows/trending/%%API_KEY%%', *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'showsTrending()'")
        return data
        
    @staticmethod
    def userCalendarShows(username, date=None, days=None, *args, **argd):
        ext = ""
        if date is not None:
            ext = "/"+str(date) #YYYYMMDD
            if days is not None:
                ext += "/"+str(days)
        data = Trakt.jsonRequest('POST', '/user/calendar/shows.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userCalendarShows()'")
        return data
        
    @staticmethod
    def userFriends(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/friends.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userFriends()'")
        return data
        
    @staticmethod
    def userLibraryMoviesAll(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/all.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesAll()'")
        return data
        
    @staticmethod
    def userLibraryMoviesCollection(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/collection.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesCollection()'")
        return data
        
    @staticmethod
    def userLibraryMoviesHated(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/hated.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesHated()'")
        return data
        
    @staticmethod
    def userLibraryMoviesLoved(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/movies/loved.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryMoviesLoved()'")
        return data
        
    @staticmethod
    def userLibraryShowsAll(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/all.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsAll()'")
        return data
        
    @staticmethod
    def userLibraryShowsCollection(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/collection.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsCollection()'")
        return data
        
    @staticmethod
    def userLibraryShowsHated(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/hated.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsHated()'")
        return data
        
    @staticmethod
    def userLibraryShowsLoved(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/loved.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsLoved()'")
        return data
        
    @staticmethod
    def userLibraryShowsWatched(username, extended=None, *args, **argd):
        ext = ""
        if extended is not None: etx = "/"+str(extended)
        data = Trakt.jsonRequest('POST', '/user/library/shows/watched.json/%%API_KEY%%/'+str(username)+ext, *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLibraryShowsWatched()'")
        return data
        
    @staticmethod
    def userList(username, slug, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/list.json/%%API_KEY%%/'+str(username)+"/"+str(slug), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userList()'")
        return data
        
    @staticmethod
    def userLists(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/lists.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userLists()'")
        return data
        
    @staticmethod
    def userProfile(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/profile.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userProfile()'")
        return data
        
    @staticmethod
    def userWatched(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watched.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatched()'")
        return data
        
    @staticmethod
    def userWatchedEpisodes(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watched/episodes.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchedEpisodes()'")
        return data
        
    @staticmethod
    def userWatchedMovies(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watched/movies.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchedMovies()'")
        return data
        
    @staticmethod
    def userWatching(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watching.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatching()'")
        return data
        
    @staticmethod
    def userWatchlistEpisodes(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watchlist/episodes.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchlistEpisodes()'")
        return data
        
    @staticmethod
    def userWatchlistMovies(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watchlist/movies.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchlistMovies()'")
        return data
        
    @staticmethod
    def userWatchlistShows(username, *args, **argd):
        data = Trakt.jsonRequest('POST', '/user/watchlist/shows.json/%%API_KEY%%/'+str(username), *args, **argd)
        if data == None:
            Debug("[Trakt] Error in request from 'userWatchlistShows()'")
        return data
        """