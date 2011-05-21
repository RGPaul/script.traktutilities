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

BACKGROUND = 102
TITLE = 103
OVERVIEW = 104
POSTER = 105
PLAY_BUTTON = 106
YEAR = 107
RUNTIME = 108
TAGLINE = 109
MOVIE_LIST = 110
TVSHOW_LIST = 110
RATING = 111
WATCHERS = 112

RATE_SCENE = 98
RATE_TITLE = 100
RATE_CUR_NO_RATING = 101
RATE_CUR_LOVE = 102
RATE_CUR_HATE = 103
RATE_SKIP_RATING = 104
RATE_LOVE_BTN = 105
RATE_HATE_BTN = 106
RATE_RATE_SHOW_BG = 107
RATE_RATE_SHOW_BTN = 108

#get actioncodes from keymap.xml
ACTION_PARENT_DIRECTORY = 9
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

class MoviesWindow(xbmcgui.WindowXML):

    movies = None

    def initWindow(self, movies):
        self.movies = movies
        
    def onInit(self):
        self.getControl(MOVIE_LIST).reset()
        if self.movies != None:
            for movie in self.movies:
                li = xbmcgui.ListItem(movie['title'], '', movie['images']['poster'])
                if not ('idMovie' in movie):
                    movie['idMovie'] = getMovieIdFromXBMC(movie['imdb_id'], movie['title'])
                if movie['idMovie'] != -1:
                    li.setProperty('Available','true')
                if 'watchlist' in movie:
                    if movie['watchlist']:
                        li.setProperty('Watchlist','true')
                self.getControl(MOVIE_LIST).addItem(li)
            self.setFocus(self.getControl(MOVIE_LIST))
            self.listUpdate()
        else:
            Debug("MoviesWindow: Error: movies array is empty")
            self.close()

    def listUpdate(self):
        try:
            current = self.getControl(MOVIE_LIST).getSelectedPosition()
        except TypeError:
            return # ToDo: error output
        
        try:
            self.getControl(BACKGROUND).setImage(self.movies[current]['images']['fanart'])
        except KeyError:
            Debug("KeyError for Backround")
        except TypeError:
            Debug("TypeError for Backround")
        try:
            self.getControl(TITLE).setLabel(self.movies[current]['title'])
        except KeyError:
            Debug("KeyError for Title")
            self.getControl(TITLE).setLabel("")
        except TypeError:
            Debug("TypeError for Title")
        try:
            self.getControl(OVERVIEW).setText(self.movies[current]['overview'])
        except KeyError:
            Debug("KeyError for Overview")
            self.getControl(OVERVIEW).setText("")
        except TypeError:
            Debug("TypeError for Overview")
        try:
            self.getControl(YEAR).setLabel("Year: " + str(self.movies[current]['year']))
        except KeyError:
            Debug("KeyError for Year")
            self.getControl(YEAR).setLabel("")
        except TypeError:
            Debug("TypeError for Year")
        try:
            self.getControl(RUNTIME).setLabel("Runtime: " + str(self.movies[current]['runtime']) + " Minutes")
        except KeyError:
            Debug("KeyError for Runtime")
            self.getControl(RUNTIME).setLabel("")
        except TypeError:
            Debug("TypeError for Runtime")
        try:
            if self.movies[current]['tagline'] <> "":
                self.getControl(TAGLINE).setLabel("\""+self.movies[current]['tagline']+"\"")
            else:
                self.getControl(TAGLINE).setLabel("")
        except KeyError:
            Debug("KeyError for Tagline")
            self.getControl(TAGLINE).setLabel("")
        except TypeError:
            Debug("TypeError for Tagline")
        try:
            self.getControl(RATING).setLabel("Rating: " + self.movies[current]['certification'])
        except KeyError:
            Debug("KeyError for Rating")
            self.getControl(RATING).setLabel("")
        except TypeError:
            Debug("TypeError for Rating")
        if 'watchers' in self.movies[current]:
            try:
                self.getControl(WATCHERS).setLabel(str(self.movies[current]['watchers']) + " people watching")
            except KeyError:
                Debug("KeyError for Watchers")
                self.getControl(WATCHERS).setLabel("")
            except TypeError:
                Debug("TypeError for Watchers")
        
    def onFocus( self, controlId ):
        self.controlId = controlId

    def onAction(self, action):
        if action.getId() == 0:
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU):
            Debug("Closing MoviesWindow")
            self.close()
        elif action.getId() in (1,2,107):
            self.listUpdate()
        elif action.getId() == ACTION_SELECT_ITEM:
            movie = self.movies[self.getControl(MOVIE_LIST).getSelectedPosition()]
            if movie['idMovie'] == -1: # Error
                xbmcgui.Dialog().ok("Trakt Utilities", movie['title'].encode( "utf-8", "ignore" ) + " " + __language__(1162).encode( "utf-8", "ignore" )) # "moviename" not found in your XBMC Library
            else:
                playMovieById(movie['idMovie'])
        else:
            Debug("Uncaught action (movies): "+str(action.getId()))

class MovieWindow(xbmcgui.WindowXML):

    movie = None

    def initWindow(self, movie):
        self.movie = movie
        
    def onInit(self):
        if self.movie != None:
            try:
                self.getControl(BACKGROUND).setImage(self.movie['images']['fanart'])
            except KeyError:
                Debug("KeyError for Backround")
            except TypeError:
                Debug("TypeError for Backround")
            try:
                self.getControl(POSTER).setImage(self.movie['images']['poster'])
            except KeyError:
                Debug("KeyError for Poster")
            except TypeError:
                Debug("TypeError for Poster")
            try:
                self.getControl(TITLE).setLabel(self.movie['title'])
            except KeyError:
                Debug("KeyError for Title")
            except TypeError:
                Debug("TypeError for Title")
            try:
                self.getControl(OVERVIEW).setText(self.movie['overview'])
            except KeyError:
                Debug("KeyError for Overview")
            except TypeError:
                Debug("TypeError for Overview")
            try:
                self.getControl(YEAR).setLabel("Year: " + str(self.movie['year']))
            except KeyError:
                Debug("KeyError for Year")
            except TypeError:
                Debug("TypeError for Year")
            try:
                self.getControl(RUNTIME).setLabel("Runtime: " + str(self.movie['runtime']) + " Minutes")
            except KeyError:
                Debug("KeyError for Runtime")
            except TypeError:
                Debug("TypeError for Runtime")
            try:
                self.getControl(TAGLINE).setLabel(self.movie['tagline'])
            except KeyError:
                Debug("KeyError for Runtime")
            except TypeError:
                Debug("TypeError for Runtime")
            try:
                self.playbutton = self.getControl(PLAY_BUTTON)
                self.setFocus(self.playbutton)
            except (KeyError,TypeError):
                pass
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == PLAY_BUTTON:
            pass

    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action.getId() == 0:
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU):
            Debug("Closing MovieInfoWindow")
            self.close()
        else:
            Debug("Uncaught action (movie info): "+str(action.getId()))

class TVShowsWindow(xbmcgui.WindowXML):

    tvshows = None

    def initWindow(self, tvshows):
        self.tvshows = tvshows
        
    def onInit(self):
        if self.tvshows != None:
            for tvshow in self.tvshows:
                self.getControl(TVSHOW_LIST).addItem(xbmcgui.ListItem(tvshow['title'], '', tvshow['images']['poster']))
            self.setFocus(self.getControl(TVSHOW_LIST))
            self.listUpdate()
        else:
            Debug("TVShowsWindow: Error: tvshows array is empty")
            self.close()
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def listUpdate(self):
        
        try:
            current = self.getControl(TVSHOW_LIST).getSelectedPosition()
        except TypeError:
            return # ToDo: error output
        
        try:
            self.getControl(BACKGROUND).setImage(self.tvshows[current]['images']['fanart'])
        except KeyError:
            Debug("KeyError for Backround")
        except TypeError:
            Debug("TypeError for Backround")
        try:
            self.getControl(TITLE).setLabel(self.tvshows[current]['title'])
        except KeyError:
            Debug("KeyError for Title")
            self.getControl(TITLE).setLabel("")
        except TypeError:
            Debug("TypeError for Title")
        try:
            self.getControl(OVERVIEW).setText(self.tvshows[current]['overview'])
        except KeyError:
            Debug("KeyError for Overview")
            self.getControl(OVERVIEW).setText("")
        except TypeError:
            Debug("TypeError for Overview")
        try:
            self.getControl(YEAR).setLabel("Year: " + str(self.tvshows[current]['year']))
        except KeyError:
            Debug("KeyError for Year")
            self.getControl(YEAR).setLabel("")
        except TypeError:
            Debug("TypeError for Year")
        try:
            self.getControl(RUNTIME).setLabel("Runtime: " + str(self.tvshows[current]['runtime']) + " Minutes")
        except KeyError:
            Debug("KeyError for Runtime")
            self.getControl(RUNTIME).setLabel("")
        except TypeError:
            Debug("TypeError for Runtime")
        try:
            self.getControl(TAGLINE).setLabel(self.tvshows[current]['tagline'])
        except KeyError:
            Debug("KeyError for Tagline")
            self.getControl(TAGLINE).setLabel("")
        except TypeError:
            Debug("TypeError for Tagline")
        try:
            self.getControl(RATING).setLabel("Rating: " + self.tvshows[current]['certification'])
        except KeyError:
            Debug("KeyError for Rating")
            self.getControl(RATING).setLabel("")
        except TypeError:
            Debug("TypeError for Rating")
        try:
            self.getControl(WATCHERS).setLabel(str(self.tvshows[current]['watchers']) + " people watching")
        except KeyError:
            Debug("KeyError for Watchers")
            self.getControl(WATCHERS).setLabel("")
        except TypeError:
            Debug("TypeError for Watchers")


    def onAction(self, action):

        if action.getId() == 0:
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU):
            Debug("Closing TV Shows Window")
            self.close()
        elif action.getId() in (1,2,107):
            self.listUpdate()
        elif action.getId() == ACTION_SELECT_ITEM:
            pass # do something here ?
        else:
            Debug("Uncaught action (tv shows): "+str(action.getId()))

class RateMovieDialog(xbmcgui.WindowXMLDialog):

    def initDialog(self, imdbid, title, year, curRating):
        self.imdbid = imdbid
        self.title = title
        self.year = year
        self.curRating = curRating
        if self.curRating <> "love" and self.curRating <> "hate": self.curRating = None
        
    def onInit(self):
        self.getControl(RATE_TITLE).setLabel(__language__(1303).encode( "utf-8", "ignore" )) # How would you rate that movie?
        self.getControl(RATE_RATE_SHOW_BG).setVisible(False)
        self.getControl(RATE_RATE_SHOW_BTN).setVisible(False)
        self.getControl(RATE_CUR_NO_RATING).setEnabled(False)
        self.updateRatedButton();
        return
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == RATE_LOVE_BTN:
            self.curRating = "love"
            self.updateRatedButton()
            rateMovieOnTrakt(self.imdbid, self.title, self.year, "love")
            self.close()
            return
        elif controlId == RATE_HATE_BTN:
            self.curRating = "hate"
            self.updateRatedButton()
            rateMovieOnTrakt(self.imdbid, self.title, self.year, "hate")
            self.close()
            return
        elif controlId == RATE_SKIP_RATING:
            self.close()
            return
        elif controlId in (RATE_CUR_LOVE, RATE_CUR_HATE): #unrate clicked
            self.curRating = None
            self.updateRatedButton()
            rateMovieOnTrakt(self.imdbid, self.title, self.year, "unrate")
            return
        else:
            Debug("Uncaught click (rate movie dialog): "+str(controlId))
    
    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action.getId() in (0, 107):
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU):
            Debug("Closing RateMovieDialog")
            self.close()
        else:
            Debug("Uncaught action (rate movie dialog): "+str(action.getId()))
            
    def updateRatedButton(self):
        self.getControl(RATE_CUR_NO_RATING).setVisible(False if self.curRating <> None else True)
        self.getControl(RATE_CUR_LOVE).setVisible(False if self.curRating <> "love" else True)
        self.getControl(RATE_CUR_HATE).setVisible(False if self.curRating <> "hate" else True)

class RateEpisodeDialog(xbmcgui.WindowXMLDialog):

    def initDialog(self, tvdbid, title, year, season, episode, curRating):
        self.tvdbid = tvdbid
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.curRating = curRating
        if self.curRating <> "love" and self.curRating <> "hate": self.curRating = None
        
    def onInit(self):
        self.getControl(RATE_TITLE).setLabel(__language__(1304).encode( "utf-8", "ignore" )) # How would you rate that episode?
        self.getControl(RATE_RATE_SHOW_BTN).setLabel(__language__(1305).encode( "utf-8", "ignore" )) # Rate whole show
        self.getControl(RATE_CUR_NO_RATING).setEnabled(False)
        self.updateRatedButton();
        return
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == RATE_LOVE_BTN:
            self.curRating = "love"
            self.updateRatedButton()
            rateEpisodeOnTrakt(self.tvdbid, self.title, self.year, self.season, self.episode, "love")
            self.close()
            return
        elif controlId == RATE_HATE_BTN:
            self.curRating = "hate"
            self.updateRatedButton()
            rateEpisodeOnTrakt(self.tvdbid, self.title, self.year, self.season, self.episode, "hate")
            self.close()
            return
        elif controlId == RATE_SKIP_RATING:
            self.close()
            return
        elif controlId in (RATE_CUR_LOVE, RATE_CUR_HATE): #unrate clicked
            self.curRating = None
            self.updateRatedButton();
            rateEpisodeOnTrakt(self.tvdbid, self.title, self.year, self.season, self.episode, "unrate")
            return
        elif controlId == RATE_RATE_SHOW_BTN:
            self.getControl(RATE_RATE_SHOW_BG).setVisible(False)
            self.getControl(RATE_RATE_SHOW_BTN).setVisible(False)
            self.setFocus(self.getControl(RATE_SKIP_RATING))
            rateShow = RateShowDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
            rateShow.initDialog(self.tvdbid, self.title, self.year, getShowRatingFromTrakt(self.tvdbid, self.title, self.year))
            rateShow.doModal()
            del rateShow
        else:
            Debug("Uncaught click (rate episode dialog): "+str(controlId))
    
    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action.getId() in (0, 107):
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU):
            Debug("Closing RateEpisodeDialog")
            self.close()
        else:
            Debug("Uncaught action (rate episode dialog): "+str(action.getId()))
            
    def updateRatedButton(self):
        self.getControl(RATE_CUR_NO_RATING).setVisible(False if self.curRating <> None else True)
        self.getControl(RATE_CUR_LOVE).setVisible(False if self.curRating <> "love" else True)
        self.getControl(RATE_CUR_HATE).setVisible(False if self.curRating <> "hate" else True)

class RateShowDialog(xbmcgui.WindowXMLDialog):

    def initDialog(self, tvdbid, title, year, curRating):
        self.tvdbid = tvdbid
        self.title = title
        self.year = year
        self.curRating = curRating
        if self.curRating <> "love" and self.curRating <> "hate": self.curRating = None
        
    def onInit(self):
        self.getControl(RATE_TITLE).setLabel(__language__(1306).encode( "utf-8", "ignore" )) # How would you rate that show?
        self.getControl(RATE_SCENE).setVisible(False)
        self.getControl(RATE_RATE_SHOW_BG).setVisible(False)
        self.getControl(RATE_RATE_SHOW_BTN).setVisible(False)
        self.getControl(RATE_CUR_NO_RATING).setEnabled(False)
        self.updateRatedButton();
        return
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == RATE_LOVE_BTN:
            self.curRating = "love"
            self.updateRatedButton()
            rateShowOnTrakt(self.tvdbid, self.title, self.year, "love")
            self.close()
            return
        elif controlId == RATE_HATE_BTN:
            self.curRating = "hate"
            self.updateRatedButton()
            rateShowOnTrakt(self.tvdbid, self.title, self.year, "hate")
            self.close()
            return
        elif controlId == RATE_SKIP_RATING:
            self.close()
            return
        elif controlId in (RATE_CUR_LOVE, RATE_CUR_HATE): #unrate clicked
            self.curRating = None
            self.updateRatedButton();
            rateShowOnTrakt(self.tvdbid, self.title, self.year, "unrate")
            return
        elif controlId == RATE_RATE_SHOW_BTN:
            return
        else:
            Debug("Uncaught click (rate show dialog): "+str(controlId))
    
    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action.getId() in (0, 107):
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU):
            Debug("Closing RateShowDialog")
            self.close()
        else:
            Debug("Uncaught action (rate show dialog): "+str(action.getId()))
            
    def updateRatedButton(self):    
        self.getControl(RATE_CUR_NO_RATING).setVisible(False if self.curRating <> None else True)
        self.getControl(RATE_CUR_LOVE).setVisible(False if self.curRating <> "love" else True)
        self.getControl(RATE_CUR_HATE).setVisible(False if self.curRating <> "hate" else True)
