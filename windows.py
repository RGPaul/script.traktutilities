# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *
from rating import *

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
ACTION_CONTEXT_MENU = 117
ACTION_NAV_BACK = 92

class MoviesWindow(xbmcgui.WindowXML):

    movies = None
    lis = [] #list items
    type = 'basic'

    def initWindow(self, movies, type):
        self.movies = movies
        self.type = type
        
    def onInit(self):
        self.getControl(MOVIE_LIST).reset()
        if self.movies != None:
            for movie in self.movies:
                li = xbmcgui.ListItem(unicode(movie.title), '', unicode(movie.poster))
                if movie.libraryStatus:
                    li.setProperty('Available','true')
                if self.type <> 'watchlist':
                    if movie.watchlistStatus:
                        li.setProperty('Watchlist','true')
                if movie.trailer <> None:
                    li.setInfo('video', {'trailer': movie.trailer})
                self.lis.append(li)
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
        if current >= len(self.movies) or current < 0:
            Debug("[MoviesWindow] invalid current movie size:"+repr(len(self.movies))+" posision:"+repr(current))
            return
        
        try:
            self.getControl(BACKGROUND).setImage(unicode(self.movies[current].fanart))
        except TypeError:
            Debug("TypeError for Backround")
            
        try:
            if self.movies[current].title is not None:
                self.getControl(TITLE).setLabel(unicode(self.movies[current].title))
            else:
                self.getControl(TITLE).setLabel("")
        except TypeError:
            Debug("TypeError for Title")
            
        try:
            if self.movies[current].overview is not None:
                self.getControl(OVERVIEW).setText(unicode(self.movies[current].overview))
            else:
                self.getControl(OVERVIEW).setText("*")
        except TypeError:
            Debug("TypeError for Overview")
            
        try:
            if self.movies[current].year is not None:
                self.getControl(YEAR).setLabel("Year: " + str(self.movies[current].year))
            else:
                self.getControl(YEAR).setLabel("")
        except TypeError:
            Debug("TypeError for Year")
        try:
            if self.movies[current].year is not None:
                self.getControl(RUNTIME).setLabel("Runtime: " + str(self.movies[current].runtime) + " Minutes")
            else:
                self.getControl(RUNTIME).setLabel("")
        except TypeError:
            Debug("TypeError for Runtime")
            
        try:
            if self.movies[current].tagline is not None and self.movies[current].tagline <> "":
                self.getControl(TAGLINE).setLabel("\""+unicode(self.movies[current].tagline)+"\"")
            else:
                self.getControl(TAGLINE).setLabel("")
        except TypeError:
            Debug("TypeError for Tagline")
            
        try:
            if self.movies[current].classification is not None:
                self.getControl(RATING).setLabel("Classification: " + unicode(self.movies[current].classification))
            else:
                self.getControl(RATING).setLabel("")
        except TypeError:
            Debug("TypeError for Rating")
            
        #if 'watchers' in self.movies[current]:
        #    try:
        #        self.getControl(WATCHERS).setLabel(str(self.movies[current]['watchers']) + " people watching")
        #    except KeyError:
        #        Debug("KeyError for Watchers")
        #        self.getControl(WATCHERS).setLabel("")
        #    except TypeError:
        #        Debug("TypeError for Watchers")
        
    def onFocus( self, controlId ):
        self.controlId = controlId
    
    def showContextMenu(self):
        movie = self.movies[self.getControl(MOVIE_LIST).getSelectedPosition()]
        li = self.getControl(MOVIE_LIST).getSelectedItem()
        options = []
        actions = []
        if movie.libraryStatus:
            options.append("Play")
            actions.append('play')
        if self.type <> 'watchlist':
            if movie.watchlistStatus:
                options.append("Remove from watchlist")
                actions.append('unwatchlist')
            else:
                options.append("Add to watchlist")
                actions.append('watchlist')
        else:
            options.append("Remove from watchlist")
            actions.append('unwatchlist')
        options.append("Rate")
        actions.append('rate')
        if movie.playcount == 0:
            options.append("Mark as seen")
            actions.append('seen')
        elif movie.watchlistStatus:
            options.append("Mark as seen")
            actions.append('seen')
        
        select = xbmcgui.Dialog().select(unicode(movie.title)+" - "+str(movie.year), options)
        if select != -1:
            Debug("Select: " + actions[select])
        if select == -1:
            Debug ("menu quit by user")
            return
        elif actions[select] == 'play':
            movie.play()
        elif actions[select] == 'unwatchlist':
            movie.watchlistStatus = False
            li.setProperty('Watchlist','false')
            if self.type == 'watchlist':
                self.lis.remove(li)
                self.getControl(MOVIE_LIST).reset()
                self.getControl(MOVIE_LIST).addItems(self.lis)
        elif actions[select] == 'watchlist':
            movie.watchlistStatus = True
            li.setProperty('Watchlist','true')
        elif actions[select] == 'rate':
            doRateMovie(movie)  
        elif actions[select] == 'seen':
            movie.playcount += 1
            if self.type == 'watchlist':
                self.lis.remove(li)
                self.getControl(MOVIE_LIST).reset()
                self.getControl(MOVIE_LIST).addItems(self.lis)
        
    def onAction(self, action):
        if action.getId() == 0:
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            Debug("Closing MoviesWindow")
            self.close()
        elif action.getId() in (1,2,3,4,107):
            self.listUpdate()
        elif action.getId() == ACTION_SELECT_ITEM:
            movie = self.movies[self.getControl(MOVIE_LIST).getSelectedPosition()]
            if not movie.libraryStatus: # Error
                xbmcgui.Dialog().ok("Trakt Utilities", movie['title'].encode( "utf-8", "ignore" ) + " " + __language__(1162).encode( "utf-8", "ignore" )) # "moviename" not found in your XBMC Library
            else:
                movie.play()
        elif action.getId() == ACTION_CONTEXT_MENU:
            self.showContextMenu()
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
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            Debug("Closing MovieInfoWindow")
            self.close()
        else:
            Debug("Uncaught action (movie info): "+str(action.getId()))

class TVShowsWindow(xbmcgui.WindowXML):

    shows = None
    lis = [] #list items
    type = 'basic'

    def initWindow(self, shows, type):
        self.shows = shows
        self.type = type
        
    def onInit(self):
        if self.shows != None:
            for show in self.tvshows:
                li = xbmcgui.ListItem(unicode(show.title), '', unicode(show.poster))
                if show.libraryStatus:
                    li.setProperty('Available','true')
                if self.type <> 'watchlist':
                    if show.watchlistStatus:
                        li.setProperty('Watchlist','true')
                self.lis.append(li)
                self.getControl(TVSHOW_LIST).addItem(li)
            self.setFocus(self.getControl(TVSHOW_LIST))
            self.listUpdate()
        else:
            Debug("TVShowsWindow: Error: shows array is empty")
            self.close()
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def listUpdate(self):
        
        try:
            current = self.getControl(TVSHOW_LIST).getSelectedPosition()
        except TypeError:
            return # ToDo: error output
        if current >= len(self.shows) or current < 0:
            Debug("[TVShowsWindow] invalid current shows size:"+repr(len(self.movies))+" posision:"+repr(current))
            return
        
        try:
            self.getControl(BACKGROUND).setImage(self.shows[current].fanart)
        except KeyError:
            Debug("KeyError for Backround")
        except TypeError:
            Debug("TypeError for Backround")
        try:
            self.getControl(TITLE).setLabel(self.shows[current].title)
        except KeyError:
            Debug("KeyError for Title")
            self.getControl(TITLE).setLabel("")
        except TypeError:
            Debug("TypeError for Title")
        try:
            self.getControl(OVERVIEW).setText(self.shows[current].overview)
        except KeyError:
            Debug("KeyError for Overview")
            self.getControl(OVERVIEW).setText("")
        except TypeError:
            Debug("TypeError for Overview")
        try:
            self.getControl(YEAR).setLabel("Year: " + str(self.shows[current].year))
        except KeyError:
            Debug("KeyError for Year")
            self.getControl(YEAR).setLabel("")
        except TypeError:
            Debug("TypeError for Year")
        try:
            self.getControl(RUNTIME).setLabel("Runtime: " + str(self.shows[current].runtime) + " Minutes")
        except KeyError:
            Debug("KeyError for Runtime")
            self.getControl(RUNTIME).setLabel("")
        except TypeError:
            Debug("TypeError for Runtime")
        try:
            self.getControl(TAGLINE).setLabel(str(self.shows[current].tagline))
        except KeyError:
            Debug("KeyError for Tagline")
            self.getControl(TAGLINE).setLabel("")
        except TypeError:
            Debug("TypeError for Tagline")
        try:
            self.getControl(RATING).setLabel("Rating: " + self.shows[current].classification)
        except KeyError:
            Debug("KeyError for Rating")
            self.getControl(RATING).setLabel("")
        except TypeError:
            Debug("TypeError for Rating")
        """if self.type == 'trending':
            try:
                self.getControl(WATCHERS).setLabel(str(self.tvshows[current]['watchers']) + " people watching")
            except KeyError:
                Debug("KeyError for Watchers")
                self.getControl(WATCHERS).setLabel("")
            except TypeError:
                Debug("TypeError for Watchers")"""

    def showContextMenu(self):
        show = self.shows[self.getControl(TVSHOW_LIST).getSelectedPosition()]
        li = self.getControl(TVSHOW_LIST).getSelectedItem()
        options = []
        actions = []
        if movie.libraryStatus:
            options.append("Play next")
            actions.append('playNext')
        if self.type <> 'watchlist':
            if 'watchlist' in show:
                if show['watchlist']:
                    options.append("Remove from watchlist")
                    actions.append('unwatchlist')
                else:
                    options.append("Add to watchlist")
                    actions.append('watchlist')
            else:
                options.append("Add to watchlist")
                actions.append('watchlist')
        else:
            options.append("Remove from watchlist")
            actions.append('unwatchlist')
        options.append("Rate")
        actions.append('rate')
        
        select = xbmcgui.Dialog().select(show['title'], options)
        if select != -1:
            Debug("Select: " + actions[select])
        if select == -1:
            Debug ("menu quit by user")
            return
        elif actions[select] == 'playNext':
            show.playNext()
        elif actions[select] == 'unwatchlist':
            show.watchlistStatus = False
            li.setProperty('Watchlist','false')
            if self.type == 'watchlist':
                self.lis.remove(li)
                self.getControl(TVSHOW_LIST).reset()
                self.getControl(TVSHOW_LIST).addItems(self.lis)
        elif actions[select] == 'watchlist':
            show.watchlistStatus = True
            li.setProperty('Watchlist','true')
        elif actions[select] == 'rate':
            doRateShow(show)

    def onAction(self, action):

        if action.getId() == 0:
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            Debug("Closing TV Shows Window")
            self.close()
        elif action.getId() in (1,2,107):
            self.listUpdate()
        elif action.getId() == ACTION_SELECT_ITEM:
            show.playNext()
        elif action.getId() == ACTION_CONTEXT_MENU:
            self.showContextMenu()
        else:
            Debug("Uncaught action (tv shows): "+str(action.getId()))

class RateMovieDialog(xbmcgui.WindowXMLDialog):

    def initDialog(self, movie):
        self.movie = movie
        self.curRating = movie.rating
        if self.curRating <> 'love' and self.curRating <> 'hate': self.curRating = None
        
    def onInit(self):
        self.getControl(RATE_TITLE).setLabel(__language__(1303).encode( "utf-8", "ignore" )) # How would you rate that movie?
        self.getControl(RATE_RATE_SHOW_BG).setVisible(False)
        self.getControl(RATE_RATE_SHOW_BTN).setVisible(False)
        self.getControl(RATE_CUR_NO_RATING).setEnabled(False)
        self.setFocus(self.getControl(RATE_SKIP_RATING))
        self.updateRatedButton();
        return
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == RATE_LOVE_BTN:
            self.curRating = 'love'
            self.updateRatedButton()
            self.movie.rating = 'love'
            self.close()
            return
        elif controlId == RATE_HATE_BTN:
            self.curRating = 'hate'
            self.updateRatedButton()
            self.movie.rating = 'hate'
            self.close()
            return
        elif controlId == RATE_SKIP_RATING:
            self.close()
            return
        elif controlId in (RATE_CUR_LOVE, RATE_CUR_HATE): #unrate clicked
            self.curRating = None
            self.updateRatedButton()
            self.movie.rating = 'unrate'
            return
        else:
            Debug("Uncaught click (rate movie dialog): "+str(controlId))
    
    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action.getId() in (0, 107):
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            Debug("Closing RateMovieDialog")
            self.close()
        else:
            Debug("Uncaught action (rate movie dialog): "+str(action.getId()))
            
    def updateRatedButton(self):
        self.getControl(RATE_CUR_NO_RATING).setVisible(False if self.curRating <> None else True)
        self.getControl(RATE_CUR_LOVE).setVisible(False if self.curRating <> 'love' else True)
        self.getControl(RATE_CUR_HATE).setVisible(False if self.curRating <> 'hate' else True)

class RateEpisodeDialog(xbmcgui.WindowXMLDialog):

    def initDialog(self, episode):
        self.episode = episode
        self.curRating = episode.rating
        if self.curRating <> "love" and self.curRating <> "hate": self.curRating = None
        
    def onInit(self):
        self.getControl(RATE_TITLE).setLabel(__language__(1304).encode( "utf-8", "ignore" )) # How would you rate that episode?
        self.getControl(RATE_RATE_SHOW_BTN).setLabel(__language__(1305).encode( "utf-8", "ignore" )) # Rate whole show
        self.getControl(RATE_CUR_NO_RATING).setEnabled(False)
        self.setFocus(self.getControl(RATE_SKIP_RATING))
        self.updateRatedButton();
        return
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == RATE_LOVE_BTN:
            self.curRating = "love"
            self.updateRatedButton()
            self.episode.rating = 'love'
            self.close()
            return
        elif controlId == RATE_HATE_BTN:
            self.curRating = "hate"
            self.updateRatedButton()
            self.episode.rating = 'hate'
            self.close()
            return
        elif controlId == RATE_SKIP_RATING:
            self.close()
            return
        elif controlId in (RATE_CUR_LOVE, RATE_CUR_HATE): #unrate clicked
            self.curRating = None
            self.updateRatedButton();
            self.episode.rating = 'unrate'
            return
        elif controlId == RATE_RATE_SHOW_BTN:
            self.getControl(RATE_RATE_SHOW_BG).setVisible(False)
            self.getControl(RATE_RATE_SHOW_BTN).setVisible(False)
            self.setFocus(self.getControl(RATE_SKIP_RATING))
            rateShow = RateShowDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
            rateShow.initDialog(episode.getShow())
            rateShow.doModal()
            del rateShow
        else:
            Debug("Uncaught click (rate episode dialog): "+str(controlId))
    
    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action.getId() in (0, 107):
            return
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            Debug("Closing RateEpisodeDialog")
            self.close()
        else:
            Debug("Uncaught action (rate episode dialog): "+str(action.getId()))
            
    def updateRatedButton(self):
        self.getControl(RATE_CUR_NO_RATING).setVisible(False if self.curRating <> None else True)
        self.getControl(RATE_CUR_LOVE).setVisible(False if self.curRating <> "love" else True)
        self.getControl(RATE_CUR_HATE).setVisible(False if self.curRating <> "hate" else True)

class RateShowDialog(xbmcgui.WindowXMLDialog):

    def initDialog(self, show):
        self.show = show
        self.curRating = show.rating
        if self.curRating <> "love" and self.curRating <> "hate": self.curRating = None
        
    def onInit(self):
        self.getControl(RATE_TITLE).setLabel(__language__(1306).encode( "utf-8", "ignore" )) # How would you rate that show?
        self.getControl(RATE_SCENE).setVisible(False)
        self.getControl(RATE_RATE_SHOW_BG).setVisible(False)
        self.getControl(RATE_RATE_SHOW_BTN).setVisible(False)
        self.getControl(RATE_CUR_NO_RATING).setEnabled(False)
        self.setFocus(self.getControl(RATE_SKIP_RATING))
        self.updateRatedButton();
        return
        
    def onFocus( self, controlId ):
        self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == RATE_LOVE_BTN:
            self.curRating = 'love'
            self.updateRatedButton()
            self.show.rating = 'love'
            self.close()
            return
        elif controlId == RATE_HATE_BTN:
            self.curRating = 'hate'
            self.updateRatedButton()
            self.show.rating = 'hate'
            self.close()
            return
        elif controlId == RATE_SKIP_RATING:
            self.close()
            return
        elif controlId in (RATE_CUR_LOVE, RATE_CUR_HATE): #unrate clicked
            self.curRating = None
            self.updateRatedButton();
            self.show.rating = 'unrate'
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
        if action.getId() in (ACTION_PARENT_DIRECTORY, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            Debug("Closing RateShowDialog")
            self.close()
        else:
            Debug("Uncaught action (rate show dialog): "+str(action.getId()))
            
    def updateRatedButton(self):    
        self.getControl(RATE_CUR_NO_RATING).setVisible(False if self.curRating <> None else True)
        self.getControl(RATE_CUR_LOVE).setVisible(False if self.curRating <> "love" else True)
        self.getControl(RATE_CUR_HATE).setVisible(False if self.curRating <> "hate" else True)
