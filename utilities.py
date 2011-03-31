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
    if (debug or force):
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
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows','params':{'fields': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastPlayed']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    
    return result['result']
    
# get seasons for a given tvshow from XBMC
def getSeasonsFromXBMC(tvshow):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetSeasons','params':{'tvshowid': tvshow['tvshowid'], 'fields': ['originaltitle']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    return result['result']
    
# get episodes for a given tvshow / season from XBMC
def getEpisodesFromXBMC(tvshow, season):
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetEpisodes','params':{'tvshowid': tvshow['tvshowid'], 'season': season, 'fields': ['playcount', 'year', 'episode']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    return result['result']

# get movies from XBMC
def getMoviesFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies','params':{'fields': ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastPlayed']}, 'id': 1})
    
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)

    return result['result']['movies']

# updates movie collection entries on trakt (don't unlibrary)
def updateMovieCollection(daemon=False):

    # get the required informations
    trakt_movies = traktMovieListByImdbID(getMoviesFromTrakt())
    xbmc_movies = getMoviesFromXBMC()

    movie_collection = []
    
    if not daemon:
        progress = xbmcgui.DialogProgress()
        progress.create("Trakt Utilities", __language__(1132).encode( "utf-8", "ignore" )) # Checking Database for new Episodes
    
    for i in range(0, len(xbmc_movies)):
        if not daemon:
            progress.update(100 / len(xbmc_movies) * i)
            if progress.iscanceled():
                notification ("Trakt Utilities", __language__(1134).encode( "utf-8", "ignore" )) # Progress Aborted
                return
        try:
            imdbid = xbmc_movies[i]['imdbnumber']
        except KeyError:
            Debug("skipping " + xbmc_movies[i]['title'] + " - no IMDbID found")
            continue
        
        try:
            trakt_movie = trakt_movies[imdbid]
        except KeyError: # movie not on trakt right now
            if xbmc_movies[i]['year'] > 0:
                try:
                    movie_collection.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['originaltitle'], 'year': xbmc_movies[i]['year']})
                except KeyError:
                    movie_collection.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['title'], 'year': xbmc_movies[i]['year']})
            else:
                Debug("skipping " + xbmc_movies[i]['title'] + " - unknown year")
                
    if not daemon:
        progress.close()
    
    movies_string = ""
    for i in range(0, len(movie_collection)):
        if i == 0:
            movies_string += movie_collection[i]['title']
        elif i > 5:
            break
        else:
            movies_string += ", " + movie_collection[i]['title']

    # add movies to trakt library (collection):
    if len(movie_collection) > 0:
    
        choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(len(movie_collection)) + " " + __language__(1125).encode( "utf-8", "ignore" ), movies_string) # Movies will be added to Trakt Collection
        if choice == False:
            return
        
        jdata = json.dumps({'username': username, 'password': pwd, 'movies': movie_collection})
        
        # refresh connection (don't want to get tcp timeout)
        conn = httplib.HTTPConnection('api.trakt.tv')
        conn.request('POST', '/movie/library/' + apikey, jdata, headers)
        response = conn.getresponse()
        
        data = json.loads(response.read())
        
        if data['status'] == 'success':
            Debug ("successfully uploaded collection: ")
            Debug ("inserted: " + str(data['inserted']) + " already_exist: " + str(data['already_exist']) + " skipped: " + str(data['skipped']))
            if data['skipped'] > 0:
                Debug ("skipped movies: " + str(data['skipped_movies']))
            if not daemon:
                xbmcgui.Dialog().ok("Trakt Utilities", str(len(movie_collection) - data['skipped']) + " " + __language__(1126).encode( "utf-8", "ignore" ), str(data['skipped']) + " " + __language__(1126).encode( "utf-8", "ignore" )) # Movies updated on Trakt / Movies skipped
        elif data['status'] == 'failure':
            Debug ("Error uploading movie collection: " + str(data['error']))
            if not daemon:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1121).encode( "utf-8", "ignore" ), str(data['error'])) # Error uploading movie collection
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1122).encode( "utf-8", "ignore" )) # No new movies in XBMC library to update

# updates seen movies on trakt
def syncSeenMovies(daemon=False):
    
    # get the required informations
    trakt_movies = traktMovieListByImdbID(getMoviesFromTrakt())
    xbmc_movies = getMoviesFromXBMC()
        
    movies_seen = []

    for i in range(0, len(xbmc_movies)):
        try:
            imdbid = xbmc_movies[i]['imdbnumber']
        except KeyError:
            try:
                Debug("skipping " + xbmc_movies[i]['title'] + " - no IMDbID found")
            except KeyError:
                try:
                    Debug("skipping " + xbmc_movies[i]['label'] + " - no IMDbID found")
                except KeyError:
                    Debug("skipping a movie - no IMDbID, title, or label found")
            continue
            
        try:
            trakt_movie = trakt_movies[imdbid]
        except KeyError: # movie not on trakt right now
            # if seen, add it
            if xbmc_movies[i]['playcount'] > 0:
                if xbmc_movies[i]['year'] > 0:
                    try:
                        movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['originaltitle'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount'], 'last_played': int(time.mktime(time.strptime(xbmc_movies[i]['lastPlayed'], '%Y-%m-%d %H:%M:%S')))})
                    except KeyError:
                        movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['title'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount'], 'last_played': int(time.mktime(time.strptime(xbmc_movies[i]['lastPlayed'], '%Y-%m-%d %H:%M:%S')))})
                else:
                    Debug("skipping " + xbmc_movies[i]['title'] + " - unknown year")
            continue
            
        if xbmc_movies[i]['playcount'] > 0 and trakt_movie['plays'] == 0:
            if xbmc_movies[i]['year'] > 0:
                try:
                    movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['originaltitle'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount'], 'last_played': int(time.mktime(time.strptime(xbmc_movies[i]['lastPlayed'], '%Y-%m-%d %H:%M:%S')))})
                except KeyError:
                    movies_seen.append({'imdb_id': imdbid, 'title': xbmc_movies[i]['title'], 'year': xbmc_movies[i]['year'], 'plays': xbmc_movies[i]['playcount'], 'last_played': int(time.mktime(time.strptime(xbmc_movies[i]['lastPlayed'], '%Y-%m-%d %H:%M:%S')))})
            else:
                Debug("skipping " + xbmc_movies[i]['title'] + " - unknown year")
    
    movies_string = ""
    for i in range(0, len(movies_seen)):
        if i == 0:
            movies_string += movies_seen[i]['title']
        elif i > 5:
            break
        else:
            movies_string += ", " + movies_seen[i]['title']

    # set movies as seen on trakt:
    if len(movies_seen) > 0:
        
        if not daemon:
            choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(len(movies_seen)) + " " + __language__(1127).encode( "utf-8", "ignore" ), movies_string) # Movies will be added as seen on Trakt
            if choice == False:
                return
    
        jdata = json.dumps({'username': username, 'password': pwd, 'movies': movies_seen})
        
        # refresh connection (don't want to get tcp timeout)
        conn = httplib.HTTPConnection('api.trakt.tv')
        conn.request('POST', '/movie/seen/' + apikey, jdata, headers)
        response = conn.getresponse()

        data = json.loads(response.read())

        if data['status'] == 'success':
            Debug ("successfully uploaded seen movies: ")
            Debug ("inserted: " + str(data['inserted']) + " already_exist: " + str(data['already_exist']) + " skipped: " + str(data['skipped']))
            if data['skipped'] > 0:
                Debug ("skipped movies: " + str(data['skipped_movies']))
            notification ("Trakt Utilities", str(len(movies_seen) - data['skipped']) + " " + __language__(1126).encode( "utf-8", "ignore" )) # Movies updated
        elif data['status'] == 'failure':
            Debug ("Error uploading seen movies: " + str(data['error']))
            if not daemon:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1123).encode( "utf-8", "ignore" ), str(data['error'])) # Error uploading seen movies
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1124).encode( "utf-8", "ignore" )) # no new seen movies to update for trakt
    
    xbmc_movies_imdbid = {}
    for i in range(0, len(xbmc_movies)):
        try:
            xbmc_movies_imdbid[xbmc_movies[i]['imdbnumber']] = xbmc_movies[i]
        except KeyError:
            continue
    
    # set movies seen from trakt, that are unseen on xbmc:
    movies_seen = []
    Debug("searching local...")
    for movie in trakt_movies.items():
        if movie[1]['plays'] > 0:
            try:
                if xbmc_movies_imdbid[movie[1]['imdb_id']]['playcount'] == 0:
                    movies_seen.append(movie[1])
            except KeyError: # movie not in xbmc database
                continue
    
    dbpath = getDBPath()
    if dbpath == None:
        Debug ("dbpath = None")
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", str(len(movies_seen)) + " " + __language__(1152).encode( "utf-8", "ignore" )) # Error: can't open XBMC Movie Database
        return # dbpath not set
    
    # sqlite till jsonrpc supports playcount update
    db = sqlite3.connect(dbpath)
    cursor = db.cursor()
    
    movies_string = ""
    for i in range(0, len(movies_seen)):
        if i == 0:
            movies_string += movies_seen[i]['title']
        elif i > 5:
            break
        else:
            movies_string += ", " + movies_seen[i]['title']
    
    if len(movies_seen) > 0:
        if not daemon:
            choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(len(movies_seen)) + " " + __language__(1147).encode( "utf-8", "ignore" ), movies_string) # Movies will be added as seen on Trakt
            if choice == False:
                return
        
        for i in range(0, len(movies_seen)):
            setXBMCMoviePlaycount(movies_seen[i]['imdb_id'], movies_seen[i]['plays'], cursor) # set playcount on xbmc
        db.commit()
        cursor.close()
        if daemon:
            notification("Trakt Utilities", str(len(movies_seen)) + " " + __language__(1129).encode( "utf-8", "ignore" )) # Movies updated on XBMC
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", str(len(movies_seen)) + " " + __language__(1129).encode( "utf-8", "ignore" )) # Movies updated on XBMC
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1128).encode( "utf-8", "ignore" )) # no new seen movies to update for xbmc

# sets the playcount of a given movie by imdbid
def setXBMCMoviePlaycount(imdb_id, playcount, cursor):
    # sqlite till jsonrpc supports playcount update
    # c09 => IMDB ID
    cursor.execute('select idFile from movie where c09=?', (imdb_id,))
    idfile = cursor.fetchall()[0][0]
    cursor.execute('update files set playCount=? where idFile=?',(playcount, idfile))

# removes deleted movies from trakt collection
def cleanMovieCollection(daemon=False):

    # get the required informations
    trakt_movies = traktMovieListByImdbID(getMoviesFromTrakt())
    xbmc_movies = getMoviesFromXBMC()

    to_unlibrary = []
    
    # to get xbmc movies by imdbid
    xbmc_movies_imdbid = {}
    for i in range(0, len(xbmc_movies)):
        try:
            xbmc_movies_imdbid[xbmc_movies[i]['imdbnumber']] = xbmc_movies[i]
        except KeyError:
            continue
    
    for movie in trakt_movies.items():
        if movie[1]['in_collection']:
            try:
                xbmc_movies_imdbid[movie[1]['imdb_id']]
            except KeyError: # not on xbmc database
                to_unlibrary.append(movie[1])
                Debug (movie[1]['title'] + " not found in xbmc library")
    
    if len(to_unlibrary) > 0:
        jdata = json.dumps({'username': username, 'password': pwd, 'movies': to_unlibrary})
        
        # refresh connection (don't want to get tcp timeout)
        conn = httplib.HTTPConnection('api.trakt.tv')
        conn.request('POST', '/movie/unlibrary/' + apikey, jdata, headers)
        response = conn.getresponse()
        
        data = json.loads(response.read())
        
        Debug(str(data))
        
        if data['status'] == 'success':
            Debug ("successfully cleared collection: " + str(data['message']))
            if not daemon:
                xbmcgui.Dialog().ok("Trakt Utilities", str(data['message']))
        elif data['status'] == 'failure':
            Debug ("Error uploading movie collection: " + str(data['error']))
            if daemon:
                notification("Trakt Utilities", __language__(1121).encode( "utf-8", "ignore" ), str(data['error'])) # Error uploading movie collection
            else:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1121).encode( "utf-8", "ignore" ), str(data['error'])) # Error uploading movie collection
    else:
        xbmcgui.Dialog().ok("Trakt Utilities", __language__(1130).encode( "utf-8", "ignore" )) # No new movies in library to update

# updates tvshow collection entries on trakt (no unlibrary)
def updateTVShowCollection(daemon=False):

    if not daemon:
        progress = xbmcgui.DialogProgress()
        progress.create("Trakt Utilities", __language__(1133).encode( "utf-8", "ignore" )) # Checking Database for new Episodes

    # get the required informations
    trakt_tvshowlist = getTVShowCollectionFromTrakt()
    xbmc_tvshows = getTVShowsFromXBMC()
    
    trakt_tvshows = {}

    for i in range(0, len(trakt_tvshowlist)):
        trakt_tvshows[trakt_tvshowlist[i]['tvdb_id']] = trakt_tvshowlist[i]
        
    seasonid = -1
    seasonid2 = 0
    tvshows_toadd = []
    tvshow = {}
    foundseason = False
        
    for i in range(0, xbmc_tvshows['total']):
        if not daemon:
            progress.update(100 / xbmc_tvshows['total'] * i)
            if progress.iscanceled():
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1134).encode( "utf-8", "ignore" )) # Progress Aborted
                return
            
        seasons = getSeasonsFromXBMC(xbmc_tvshows['tvshows'][i])
        try:
            tvshow['title'] = xbmc_tvshows['tvshows'][i]['title']
        except KeyError:
            # no title? try label
            try:
                tvshow['title'] = xbmc_tvshows['tvshows'][i]['label']
            except KeyError:
                # no titel, no laben ... sorry no upload ...
                continue
                
        try:
            tvshow['year'] = xbmc_tvshows['tvshows'][i]['year']
            tvshow['tvdb_id'] = xbmc_tvshows['tvshows'][i]['imdbnumber']
        except KeyError:
            # no year, no imdb id ... sorry no upload ...
            continue
            
        tvshow['episodes'] = []
        for j in range(0, seasons['total']):
            while True:
                seasonid += 1
                episodes = getEpisodesFromXBMC(xbmc_tvshows['tvshows'][i], seasonid)
                if episodes['total'] > 0:
                    break
                if seasonid > 50:  # maybe something went wrong
                    break          # is there any tvshow out there with 50 seasons ?
            if seasonid > 50:
                continue
            try:
                foundseason = False
                for k in range(0, len(trakt_tvshows[xbmc_tvshows['tvshows'][i]['imdbnumber']]['seasons'])):
                    if trakt_tvshows[xbmc_tvshows['tvshows'][i]['imdbnumber']]['seasons'][k]['season'] == seasonid:
                        foundseason = True
                        for l in range(0, len(episodes['episodes'])):
                            if episodes['episodes'][l]['episode'] in trakt_tvshows[xbmc_tvshows['tvshows'][i]['imdbnumber']]['seasons'][k]['episodes']:
                                pass
                            else:
                                # add episode
                                tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][l]['episode']})
                if foundseason == False:
                    # add season
                    for k in range(0, len(episodes['episodes'])):
                        tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][k]['episode']})
            except KeyError:
                # add season (whole tv show missing)
                for k in range(0, len(episodes['episodes'])):
                    tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][k]['episode']})
        
        seasonid = -1
        # if there are episodes to add to trakt - append to list
        if len(tvshow['episodes']) > 0:
            tvshows_toadd.append(tvshow)
            tvshow = {}
        else:
            tvshow = {}
    
    if not daemon:
        progress.close()
            
    count = 0
    for i in range(0, len(tvshows_toadd)):
        for j in range(0, len(tvshows_toadd[i]['episodes'])):
            count += 1
            
    tvshows_string = ""
    for i in range(0, len(tvshows_toadd)):
        if i == 0:
            tvshows_string += tvshows_toadd[i]['title']
        elif i > 5:
            break
        else:
            tvshows_string += ", " + tvshows_toadd[i]['title']
    
    # add episodes to library (collection):
    if count > 0:
        if daemon:
            notification("Trakt Utilities", str(count) + " " + __language__(1131).encode( "utf-8", "ignore" )) # TVShow Episodes will be added to Trakt Collection
        else:
            choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(count) + " " + __language__(1131).encode( "utf-8", "ignore" ), tvshows_string) # TVShow Episodes will be added to Trakt Collection
            if choice == False:
                return
        
        error = None
        
        # refresh connection (don't want to get tcp timeout)
        conn = httplib.HTTPConnection('api.trakt.tv')
        
        for i in range(0, len(tvshows_toadd)):
            jdata = json.dumps({'username': username, 'password': pwd, 'tvdb_id': tvshows_toadd[i]['tvdb_id'], 'title': tvshows_toadd[i]['title'], 'year': tvshows_toadd[i]['year'], 'episodes': tvshows_toadd[i]['episodes']})
            
            conn.request('POST', '/show/episode/library/' + apikey, jdata, headers)
            response = conn.getresponse()
            
            data = json.loads(response.read())
            
            if data['status'] == 'success':
                Debug ("successfully uploaded collection: " + str(data['message']))
            elif data['status'] == 'failure':
                Debug ("Error uploading tvshow collection: " + str(data['error']))
                error = data['error']
                
        if error == None:
            if not daemon:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1137).encode( "utf-8", "ignore" )) # Episodes sucessfully updated to Trakt
        else:
            if daemon:
                notification("Trakt Utilities", __language__(1135).encode( "utf-8", "ignore" ) + str(error)) # Error uploading TVShow collection
            else:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1135).encode( "utf-8", "ignore" ), error) # Error uploading TVShow collection
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1136).encode( "utf-8", "ignore" )) # No new episodes in XBMC library to update

# removes deleted tvshow episodes from trakt collection (unlibrary)
def cleanTVShowCollection(daemon=False):

    if not daemon:
        progress = xbmcgui.DialogProgress()
        progress.create("Trakt Utilities", __language__(1140).encode( "utf-8", "ignore" )) # Checking Database for deleted Episodes

    # get the required informations
    trakt_tvshowlist = getTVShowCollectionFromTrakt()
    xbmc_tvshows = getTVShowsFromXBMC()
    
    trakt_tvshows = {}

    for i in range(0, len(trakt_tvshowlist)):
        trakt_tvshows[trakt_tvshowlist[i]['tvdb_id']] = trakt_tvshowlist[i]
    
    to_unlibrary = []
    
    xbmc_tvshows_tvdbid = {}
    tvshow = {}
    seasonid = -1
    foundseason = False
    progresscount = -1
    
    # make xbmc tvshows searchable by tvdbid
    for i in range(0, xbmc_tvshows['total']):
        try:
            xbmc_tvshows_tvdbid[xbmc_tvshows['tvshows'][i]['imdbnumber']] = xbmc_tvshows['tvshows'][i]
        except KeyError:
            continue # missing data, skip tvshow
    
    for trakt_tvshow in trakt_tvshows.items():
        if not daemon:
            progresscount += 1
            progress.update(100 / len(trakt_tvshows) * progresscount)
            if progress.iscanceled():
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1134).encode( "utf-8", "ignore" )) # Progress Aborted
                return
        
        try:
            tvshow['title'] = trakt_tvshow[1]['title']
            tvshow['year'] = trakt_tvshow[1]['year']
            tvshow['tvdb_id'] = trakt_tvshow[1]['tvdb_id']
        except KeyError:
            # something went wrong
            Debug("cleanTVShowCollection: KeyError trakt_tvshow[1] title, year or tvdb_id")
            continue # skip this tvshow
            
        tvshow['episodes'] = []
        try:
            xbmc_tvshow = xbmc_tvshows_tvdbid[trakt_tvshow[1]['tvdb_id']]
            # check seasons
            xbmc_seasons = getSeasonsFromXBMC(xbmc_tvshow)
            for i in range(0, len(trakt_tvshow[1]['seasons'])):
                count = 0
                for j in range(0, xbmc_seasons['total']):
                    while True:
                        seasonid += 1
                        xbmc_episodes = getEpisodesFromXBMC(xbmc_tvshow, seasonid)
                        if xbmc_episodes['total'] > 0:
                            count += 1
                            if trakt_tvshow[1]['seasons'][i]['season'] == seasonid:
                                foundseason = True
                                # check episodes
                                for k in range(0, len(trakt_tvshow[1]['seasons'][i]['episodes'])):
                                    episodeid = trakt_tvshow[1]['seasons'][i]['episodes'][k]
                                    found = False
                                    for l in range(0, xbmc_episodes['total']):
                                        if xbmc_episodes['episodes'][l]['episode'] == episodeid:
                                            found = True
                                            break
                                    if found == False:
                                        # delte episode from trakt collection
                                        tvshow['episodes'].append({'season': seasonid, 'episode': episodeid})
                                break
                        if count >= xbmc_seasons['total']:
                            break
                        if seasonid > 50:  # maybe something went wrong
                            break          # is there any tvshow out there with 50 seasons ?
                    if seasonid > 50:
                        continue
                if foundseason == False:
                    Debug("Season not found: " + trakt_tvshow[1]['title'] + ": " + trakt_tvshow[1]['seasons'][i]['season'])
                    # delte season from trakt collection
                    for episodeid in trakt_tvshow[1]['seasons'][i]['episodes']:
                        tvshow['episodes'].append({'season': trakt_tvshow[1]['seasons'][i]['season'], 'episode': episodeid})
                foundseason = False
                seasonid = -1
            
        except KeyError:
            Debug ("TVShow not found: " + trakt_tvshow[1]['title'])
            # delete tvshow from trakt collection
            for season in trakt_tvshow[1]['seasons']:
                for episode in season['episodes']:
                    tvshow['episodes'].append({'season': season['season'], 'episode': episode})
                    
        if len(tvshow['episodes']) > 0:
            to_unlibrary.append(tvshow)
        tvshow = {}
    
    if not daemon:
        progress.close()
    
    count = 0
    for tvshow in to_unlibrary:
        count += len(tvshow['episodes'])
        
    tvshows_string = ""
    for i in range(0, len(to_unlibrary)):
        if i == 0:
            tvshows_string += to_unlibrary[i]['title']
        elif i > 5:
            break
        else:
            tvshows_string += ", " + to_unlibrary[i]['title']
    
    # add episodes to library (collection):
    if count > 0:
        if not daemon:
            choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(count) + " " + __language__(1141).encode( "utf-8", "ignore" ), tvshows_string) # TVShow Episodes will be removed from Trakt Collection
            if choice == False:
                return
            
        error = None
        
        # refresh connection (don't want to get tcp timeout)
        conn = httplib.HTTPConnection('api.trakt.tv')
        
        for i in range(0, len(to_unlibrary)):
            jdata = json.dumps({'username': username, 'password': pwd, 'tvdb_id': to_unlibrary[i]['tvdb_id'], 'title': to_unlibrary[i]['title'], 'year': to_unlibrary[i]['year'], 'episodes': to_unlibrary[i]['episodes']})
            
            conn.request('POST', '/show/episode/unlibrary/' + apikey, jdata, headers)
            response = conn.getresponse()
            
            data = json.loads(response.read())
            
            if data['status'] == 'success':
                Debug ("successfully updated collection: " + str(data['message']))
            elif data['status'] == 'failure':
                Debug ("Error uploading tvshow collection: " + str(data['error']))
                error = data['error']
        
        if error == None:
            if daemon:
                notification("Trakt Utilities", __language__(1137).encode( "utf-8", "ignore" )) # Episodes sucessfully updated to Trakt
            else:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1137).encode( "utf-8", "ignore" )) # Episodes sucessfully updated to Trakt
        else:
            if daemon:
                notification("Trakt Utilities", __language__(1135).encode( "utf-8", "ignore" ) + str(error)) # Error uploading TVShow collection
            else:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1135).encode( "utf-8", "ignore" ), error) # Error uploading TVShow collection
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1142).encode( "utf-8", "ignore" )) # No episodes to remove from trakt
    
    
# syncs seen tvshows between trakt and xbmc (no unlibrary)
def syncSeenTVShows(daemon=False):

    if not daemon:
        progress = xbmcgui.DialogProgress()
        progress.create("Trakt Utilities", __language__(1143).encode( "utf-8", "ignore" )) # Checking XBMC Database for new seen Episodes

    # get the required informations
    trakt_tvshowlist = getWatchedTVShowsFromTrakt()
    xbmc_tvshows = getTVShowsFromXBMC()
    
    trakt_tvshows = {}

    for i in range(0, len(trakt_tvshowlist)):
        trakt_tvshows[trakt_tvshowlist[i]['tvdb_id']] = trakt_tvshowlist[i]
    
    set_as_seen = []
    seasonid = -1
    tvshow = {}
    
    for i in range(0, xbmc_tvshows['total']):
        if not daemon:
            progress.update(100 / xbmc_tvshows['total'] * i)
            if progress.iscanceled():
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1134).encode( "utf-8", "ignore" )) # Progress Aborted
                break
        
        seasons = getSeasonsFromXBMC(xbmc_tvshows['tvshows'][i])
        try:
            tvshow['title'] = xbmc_tvshows['tvshows'][i]['title']
            tvshow['year'] = xbmc_tvshows['tvshows'][i]['year']
            tvshow['tvdb_id'] = xbmc_tvshows['tvshows'][i]['imdbnumber']
        except KeyError:
            continue # missing data, skip
            
        tvshow['episodes'] = []
        
        for j in range(0, seasons['total']):
            while True:
                seasonid += 1
                episodes = getEpisodesFromXBMC(xbmc_tvshows['tvshows'][i], seasonid)
                if episodes['total'] > 0:
                    break
                if seasonid > 50:  # maybe something went wrong
                    break          # is there any tvshow out there with 50 seasons ?
            if seasonid > 50:
                continue
            try:
                foundseason = False
                for k in range(0, len(trakt_tvshows[xbmc_tvshows['tvshows'][i]['imdbnumber']]['seasons'])):
                    if trakt_tvshows[xbmc_tvshows['tvshows'][i]['imdbnumber']]['seasons'][k]['season'] == seasonid:
                        foundseason = True
                        for l in range(0, len(episodes['episodes'])):
                            if episodes['episodes'][l]['episode'] in trakt_tvshows[xbmc_tvshows['tvshows'][i]['imdbnumber']]['seasons'][k]['episodes']:
                                pass
                            else:
                                # add episode as seen if playcount > 0
                                try:
                                    if episodes['episodes'][l]['playcount'] > 0:
                                        tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][l]['episode']})
                                except KeyError:
                                    pass
                if foundseason == False:
                    # add season
                    for k in range(0, len(episodes['episodes'])):
                        try:
                            if episodes['episodes'][k]['playcount'] > 0:
                                tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][k]['episode']})
                        except KeyError:
                                    pass
            except KeyError:
                # add season as seen (whole tv show missing)
                for k in range(0, len(episodes['episodes'])):
                    try:
                        if episodes['episodes'][k]['playcount'] > 0:
                            tvshow['episodes'].append({'season': seasonid, 'episode': episodes['episodes'][k]['episode']})
                    except KeyError:
                        pass
        
        seasonid = -1
        # if there are episodes to add to trakt - append to list
        if len(tvshow['episodes']) > 0:
            set_as_seen.append(tvshow)
            tvshow = {}
        else:
            tvshow = {}
    
    if not daemon:
        progress.close()
            
    count = 0
    set_as_seen_titles = ""
    for i in range(0, len(set_as_seen)):
        if i == 0:
            set_as_seen_titles += set_as_seen[i]['title']
        elif i > 5:
            break
        else:
            set_as_seen_titles += ", " + set_as_seen[i]['title']
        for j in range(0, len(set_as_seen[i]['episodes'])):
            count += 1
    
    # add seen episodes to trakt library:
    if count > 0:
        if daemon:
            choice = True
        else:
            choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(count) + " " + __language__(1144).encode( "utf-8", "ignore" ), set_as_seen_titles) # TVShow Episodes will be added as seen on Trakt
        
        if choice == True:
        
            error = None
            
            # refresh connection (don't want to get tcp timeout)
            conn = httplib.HTTPConnection('api.trakt.tv')
            
            for i in range(0, len(set_as_seen)):
                jdata = json.dumps({'username': username, 'password': pwd, 'tvdb_id': set_as_seen[i]['tvdb_id'], 'title': set_as_seen[i]['title'], 'year': set_as_seen[i]['year'], 'episodes': set_as_seen[i]['episodes']})
            
                conn.request('POST', '/show/episode/seen/' + apikey, jdata, headers)
                response = conn.getresponse()
            
                data = json.loads(response.read())
            
                if data['status'] == 'success':
                    Debug ("successfully uploaded collection: " + str(data['message']))
                elif data['status'] == 'failure':
                    Debug ("Error uploading tvshow collection: " + str(data['error']))
                    error = data['error']
                
            if error == None:
                if daemon:
                    notification("Trakt Utilities", __language__(1137).encode( "utf-8", "ignore" )) # Episodes sucessfully updated to Trakt
                else:
                    xbmcgui.Dialog().ok("Trakt Utilities", __language__(1137).encode( "utf-8", "ignore" )) # Episodes sucessfully updated to Trakt
            else:
                if daemon:
                    notificationxbmcgui.Dialog().ok("Trakt Utilities", __language__(1145).encode( "utf-8", "ignore" ) + str(error)) # Error uploading seen TVShows
                else:
                    xbmcgui.Dialog().ok("Trakt Utilities", __language__(1145).encode( "utf-8", "ignore" ), error) # Error uploading seen TVShows
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1146).encode( "utf-8", "ignore" )) # No new seen episodes in XBMC library to update

    if not daemon:
        progress = xbmcgui.DialogProgress()
        progress.create("Trakt Utilities", __language__(1148).encode( "utf-8", "ignore" )) # Checking Trakt Database for new seen Episodes
    progress_count = 0
    
    xbmc_tvshows_tvdbid = {}
    
    # make xbmc tvshows searchable by tvdbid
    for i in range(0, xbmc_tvshows['total']):
        try:
            xbmc_tvshows_tvdbid[xbmc_tvshows['tvshows'][i]['imdbnumber']] = xbmc_tvshows['tvshows'][i]
        except KeyError:
            continue

    set_as_seen = []
    tvshow_to_set = {}

    # add seen episodes to xbmc
    for tvshow in trakt_tvshowlist:
        if not daemon:
            progress.update(100 / len(trakt_tvshowlist) * progress_count)
            progress_count += 1
            if progress.iscanceled():
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1134).encode( "utf-8", "ignore" )) # Progress Aborted
                return
        try:
            tvshow_to_set['title'] = tvshow['title']
            tvshow_to_set['tvdb_id'] = tvshow['tvdb_id']
        except KeyError:
            continue # missing data, skip to next tvshow
            
        tvshow_to_set['episodes'] = []
        
        Debug("checking: " + tvshow['title'])
        
        trakt_seasons = tvshow['seasons']
        for trakt_season in trakt_seasons:
            seasonid = trakt_season['season']
            episodes = trakt_season['episodes']
            try:
                xbmc_tvshow = xbmc_tvshows_tvdbid[tvshow['tvdb_id']]
            except KeyError:
                Debug("tvshow not found in xbmc database")
                continue # tvshow not in xbmc library

            xbmc_episodes = getEpisodesFromXBMC(xbmc_tvshow, seasonid)
            if xbmc_episodes['total'] > 0:
                # sort xbmc episodes by id
                xbmc_episodes_byid = {}
                for i in xbmc_episodes['episodes']:
                    xbmc_episodes_byid[i['episode']] = i
                
                for episode in episodes:
                    xbmc_episode = None
                    try:
                        xbmc_episode = xbmc_episodes_byid[episode]
                    except KeyError:
                        pass
                    try:
                        if xbmc_episode != None:
                            if xbmc_episode['playcount'] <= 0:
                                tvshow_to_set['episodes'].append([seasonid, episode])
                    except KeyError:
                        # episode not in xbmc database
                        pass
        
        if len(tvshow_to_set['episodes']) > 0:
            set_as_seen.append(tvshow_to_set)
        tvshow_to_set = {}
    
    if not daemon:
        progress.close()
    
    count = 0
    set_as_seen_titles = ""
    Debug ("set as seen length: " + str(len(set_as_seen)))
    for i in range(0, len(set_as_seen)):
        if i == 0:
            set_as_seen_titles += set_as_seen[i]['title']
        elif i > 5:
            break
        else:
            set_as_seen_titles += ", " + set_as_seen[i]['title']
        for j in range(0, len(set_as_seen[i]['episodes'])):
            count += 1
    
    # add seen episodes to xbmc library:
    if count > 0:
        if daemon:
            choice = True
        else:
            choice = xbmcgui.Dialog().yesno("Trakt Utilities", str(count) + " " + __language__(1149).encode( "utf-8", "ignore" ), set_as_seen_titles) # TVShow Episodes will be set as seen on XBMC
        
        if choice == True:
            
            dbpath = getDBPath()
            if dbpath == None:
                Debug ("dbpath = None")
                if daemon:
                    notification("Trakt Utilities", __language__(1152).encode( "utf-8", "ignore" )) # Error: can't open XBMC Movie Database
                else:
                    xbmcgui.Dialog().ok("Trakt Utilities", __language__(1152).encode( "utf-8", "ignore" )) # Error: can't open XBMC Movie Database
                return # dbpath not set

            # sqlite till jsonrpc supports playcount update
            db = sqlite3.connect(dbpath)
            cursor = db.cursor()
            
            if not daemon:
                progress = xbmcgui.DialogProgress()
                progress.create("Trakt Utilities", __language__(1150).encode( "utf-8", "ignore" )) # updating XBMC Database
            progress_count = 0

            for tvshow in set_as_seen:
                if not daemon:
                    progress.update(100 / len(set_as_seen) * progress_count)
                    progress_count += 1
                    if progress.iscanceled():
                        xbmcgui.Dialog().ok("Trakt Utilities", __language__(1134).encode( "utf-8", "ignore" )) # Progress Aborted
                        db.rollback()
                        cursor.close()
                        progress.close()
                        return
                    
                for episode in tvshow['episodes']:
                    setXBMCEpisodePlaycount(tvshow['tvdb_id'], episode[0], episode[1], 1, cursor)
    
            db.commit()
            cursor.close()
            progress.close()
    else:
        if not daemon:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1151).encode( "utf-8", "ignore" )) # No new seen episodes on Trakt to update
    

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
