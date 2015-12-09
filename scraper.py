from __future__ import print_function
import requests
import re

from bs4 import BeautifulSoup

class Website:

    def __init__(self, url):
        # must add cleaning functionality
        self.url = url
        self.pages = []
        self.suggestions = set()

        # get home page
        self.pages.append(Page(self.url))

        # get all pages on homepage
        self.pages[0].load()
        for link in self.pages[0].internalLinks:
            if link[:4] == 'http':
                self.pages.append(Page(link))
            else:
                self.pages.append(Page(self.url + link))

    def getPageURLs(self):
        pageURLs = []
        for page in self.pages:
            pageURLs.append(page.url)
        return pageURLs

    def getSuggestions(self):
        for page in self.pages:
            self.suggestions.update(page.makeSuggestions())
        return self.suggestions

class Page:

    suggestionList = {
        'musicbin': "You've embedded music files!  Try monetizing these with a little Scratch magic!",
        'videobin': "You've embedded video files!  Try monetizing these with a little Scratch magic!",
        'smarturl': "Looks like you're sending visitors through smarturl to an external music store.  Why not monetize directly with Scratch?",
        'storelinks': "Your site has links to %s.  Using Scratch would enable you to cut out %s and make more profit.",
        'itunesembed': "You've embedded an Itunes widget in your site.  You can sell your tracks straight from your site with Scratch!",
        'soundcloudembed': "You've embedded a Sound Cloud player in your site.  You can sell your tracks straight from your site with Scratch!",
        'spotifyembed': "You've embedded a Spotify player in your site.  You can sell your tracks straight from your site with Scratch!",
    }

    def __init__(self, url):
        self.url = url
        self.bs = BeautifulSoup()
        self.internalLinks = []
        self.externalLinks = []
        self.allLinks = []
        self.suggestions = set()
        self.loaded = False

    def load(self):
        try:
            req = requests.get(self.url)
        except:
            print("Connection failed.")
            return False

        self.bs = BeautifulSoup(req.text, 'lxml')
        self.internalLinks = self.getInternalLinks(URLManip().splitAddress(self.url)[0])
        self.externalLinks = self.getExternalLinks(URLManip().splitAddress(self.url)[0])
        self.allLinks = self.internalLinks + self.externalLinks
        self.loaded = True

    def getInternalLinks(self, includeURL):
        internalLinks = []
        print("Internal links: ")
        #Finds all links beginning with "/"
        for link in self.bs.findAll("a", href=re.compile("^(/|.*"+includeURL+")", re.I)):
            if link.attrs['href'] is not None:
                if link.attrs['href'] not in self.internalLinks:
                    print(link.attrs['href'].lower())
                    internalLinks.append(link.attrs['href'].lower())
        return internalLinks

    def getExternalLinks(self, excludeUrl):
        externalLinks = []
        print("External links: ")
        #Finds all links that start with "http" or "www" that do not contain current url
        for link in self.bs.findAll("a", href=re.compile("^(http|www)((?!"+excludeUrl+").)*$", re.I)):
            if link.attrs['href'] is not None:
                if link.attrs['href'] not in self.externalLinks:
                    print(link.attrs['href'].lower())
                    externalLinks.append(link.attrs['href'].lower())
        return externalLinks

    def makeSuggestions(self):
        if not self.loaded:
            self.load()

        print('')
        print('---------------------------------------')
        print('URL')
        print(self.url)
        print()
        # if embedded binary files
        for link in self.allLinks:
            if re.compile('(.mp3|.aac|.ogg)', re.I).search(link):
                self.suggestions.add(self.suggestionList['musicbin'])
        # if links to smarturl
        for link in self.externalLinks:
            if re.compile('http://smarturl\.it.').search(link):
                self.suggestions.add(self.suggestionList['smarturl'])
        # if embedded player
        iframes = self.bs.findAll('iframe')
        for iframe in iframes:
            try:
                if re.compile('https://w.soundcloud.com/player', re.I).search(iframe.attrs['src']):
                    self.suggestions.add(self.suggestionList['soundcloudembed'])
                elif re.compile('https://embed.spotify.com/', re.I).search(iframe.attrs['src']):
                    self.suggestions.add(self.suggestionList['spotifyembed'])
                elif re.compile('https://widgets.itunes.apple.com/', re.I).search(iframe.attrs['src']):
                    self.suggestions.add(self.suggestionList['itunesembed'])
            except KeyError:
                pass
        # if direct links to music stores
        linktypes = ""
        for link in self.allLinks:
            if re.compile('(itunes)', re.I).search(link):
                linktypes += "itunes"
            if re.compile('(google play)', re.I).search(link):
                linktypes += "google play"
                self.suggestions.add(self.suggestionList['storelinks'] % (linktypes))
        return self.suggestions

class URLManip:
    def splitAddress(self, address):
        addressParts = address.replace("http://", "").split("/")
        return addressParts