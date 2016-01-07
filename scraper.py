from __future__ import print_function
import requests
import re
import time
import logging
from robotparser import RobotFileParser
from urlmanip import URLManip
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchWindowException

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
handler = logging.NullHandler()
logger.addHandler(handler)

binaryExtentions = [".mp3", ".aac", ".ogg", ".png", ".jpg", "jpeg", ".gif", ".mov", ".mp4"]

urlManip = URLManip()

class Website:
    """Contains Page objects and site-wide suggestion list"""
    def __init__(self, url):
        self.url = urlManip.cleanURL(url)
        self.pages = []
        self.suggestions = set()
        self.loaded = False
        logger.info("Loading %s..." % (self.url))
        try:
            requests.get(self.url)
            self.loaded = True
        except IOError as e:
            logger.error("%s cannot be loaded: %s" % (self.url, e))

        # if the website can be loaded
        if self.loaded == True:
            logger.info("Load successful. Generating suggestions...")

            # get robots.txt
            rp = RobotFileParser(self.url + "robots.txt")
            try:
                rp.read()
            except IOError:
                logger.warning("robots.txt cannot be found.")

            # get home page
            self.pages.append(Page(self.url))

            # get all pages on homepage
            self.pages[0].load()
            for link in self.pages[0].internalLinks:
                if rp.can_fetch("*", link):
                    if link[:4] == 'http':
                        self.pages.append(Page(link))
                    else:
                        self.pages.append(Page(self.url + link))
                else:
                    logger.debug("Ignoring %s based on robots.txt" % link)

    def getPageURLs(self):
        pageURLs = []
        for page in self.pages:
            pageURLs.append(page.url)
        return pageURLs

    def getSuggestions(self):
        for page in self.pages:
            for suggestion in page.iterSuggestions():
                if suggestion not in self.suggestions:
                    self.suggestions.add(suggestion)
                    yield suggestion
        storeSuggestion = self.pages[0].getStoreSuggestion()
        if storeSuggestion:
            yield storeSuggestion
        self.pages[0].closeDriver()

class Page:
    """Contains and returns suggestions for a particular webpage.  Also loads and contains webpage's HTML."""

    suggestionList = {
        'musicbin': "You've embedded music files!  Try monetizing these with a little Scratch magic!",
        'videobin': "You've embedded video files!  Try monetizing these with a little Scratch magic!",
        'smarturl': "Looks like you're sending visitors through smarturl to an external music store.  Why not monetize directly with Scratch?",
        'storelinks': "Your site has links to %s.  Using Scratch would enable you to cut out music stores and make more profit.",
        'pdf': "You have a PDF on your site!  You can monetize your content with Scratch!",
        'itunesembed': "You've embedded an Itunes widget in your site.  You can sell your tracks straight from your site with Scratch!",
        'soundcloudembed': "You've embedded a Sound Cloud player in your site.  You can sell your tracks straight from your site with Scratch!",
        'spotifyembed': "You've embedded a Spotify player in your site.  You can sell your tracks straight from your site with Scratch!",
        'youtubeembed': "You've embedded a YouTube player in your site.  Try selling your vids straight from your site with Scratch!",
        'wordpress': "Your website is built in WordPress.  Did you know that Scratch has a WordPress plugin?",
        'donations': "Using Scratch will enable you to accept microdonations!"
    }

    driver = webdriver.PhantomJS(executable_path="/app/vendor/phantomjs/bin/phantomjs")

    storeLinks = set()

    def __init__(self, url):
        self.url = url
        self.bs = BeautifulSoup()
        self.internalLinks = []
        self.externalLinks = []
        self.allLinks = []
        self.suggestions = set()
        self.parser = 'lxml'
        self.loaded = False

    def load(self):
        # if not a binary file
        if self.url[-4:] not in binaryExtentions:
            try:
                req = requests.get(self.url)
            except IOError as e:
                logger.error("Connection to %s failed: %s" % (self.url, e))
                return False

            self.bs = BeautifulSoup(req.text, self.parser)
            self.internalLinks = self.getInternalLinks(urlManip.splitAddress(self.url)[0])
            self.externalLinks = self.getExternalLinks(urlManip.splitAddress(self.url)[0])
            self.allLinks = self.internalLinks + self.externalLinks
            self.loaded = True

            # if no links were loaded and it isn't a binary file, try looking for an iframe
            if not self.allLinks:
                iframe = self.bs.find("iframe")
                if iframe:
                    self.url = iframe.attrs['src']
                    self.load()

            # if that didn't work, try handling a client-side redirect
            if not self.allLinks:
                logger.debug("Handling client-side redirect...")
                self.driver.get(self.url)
                self.waitForLoad()
                self.bs = BeautifulSoup(self.driver.page_source, self.parser)
                self.internalLinks = self.getInternalLinks(urlManip.splitAddress(self.url)[0])
                self.externalLinks = self.getExternalLinks(urlManip.splitAddress(self.url)[0])
                self.allLinks = self.internalLinks + self.externalLinks

    def waitForLoad(self):
        source = self.driver.page_source
        url = self.driver.current_url
        secCount = 5
        count = 0
        while True:
            count += 1
            if count > secCount * 2:
                logger.debug("Timing out after %s sec" % secCount)
                return
            time.sleep(.5)
            if source == self.driver.page_source or url == self.driver.current_url:
                pass
            else:
                return

    def closeDriver(self):
        try:
            self.driver.close()
        except NoSuchWindowException:
            logger.debug("NoSuchWindowException... Selenium driver already closed?")
            pass

    def getInternalLinks(self, includeURL):
        internalLinks = []
        #Finds all links beginning with "/"
        for link in self.bs.findAll("a", href=re.compile("^(/|.*"+includeURL+")", re.I)):
            if link.attrs['href'] is not None:
                href = urlManip.cleanHref(link.attrs['href']).lower()
                if href not in internalLinks:
                    if not urlManip.isID(href):
                        internalLinks.append(href)
        return internalLinks

    def getExternalLinks(self, excludeUrl):
        externalLinks = []
        #Finds all links that start with "http" or "www" that do not contain current url
        for link in self.bs.findAll("a", href=re.compile("^(http|www)((?!"+excludeUrl+").)*$", re.I)):
            if link.attrs['href'] is not None:
                href = urlManip.cleanHref(link.attrs['href']).lower()
                if href not in externalLinks:
                    if not urlManip.isID(href):
                        externalLinks.append(href)
        return externalLinks

    def printLinks(self):
        print('')
        print('---------------------------------------')
        print('URL')
        print(self.url)
        print()
        print("Internal Links:")
        for link in self.internalLinks:
            print(link)
        print()
        print("External Links:")
        for link in self.externalLinks:
            print(link)

    def makeSuggestions(self):
        if not self.loaded:
            self.load()
        # self.printLinks() (uncomment for debugging)
        for suggestion in self.iterSuggestions():
            self.suggestions.add(suggestion)
        return self.suggestions

    def iterSuggestions(self):
        # if embedded binary files
        for link in self.allLinks:
            if link[-4:] in [".mp3", ".aac", ".ogg"]:
                yield self.suggestionList['musicbin']
        # if pdf
        for link in self.allLinks:
            if link[-4:] == ".pdf":
                yield self.suggestionList['pdf']
        # if embedded pdf
        for obj in self.bs.findAll('object'):
            try:
                if obj.attrs['data'][-4:] == ".pdf":
                    yield self.suggestionList['pdf']
            except KeyError:
                pass
        # if links to smarturl
        for link in self.externalLinks:
            if re.compile('http://smarturl\.it.').search(link):
                yield self.suggestionList['smarturl']
        # if embedded player
        iframes = self.bs.findAll('iframe')
        for iframe in iframes:
            try:
                src = iframe.attrs['src']
                if re.compile('(http|https)://w\.soundcloud\.com/player', re.I).search(src):
                    yield self.suggestionList['soundcloudembed']
                elif re.compile('(http|https)://embed\.spotify\.com/', re.I).search(src):
                    yield self.suggestionList['spotifyembed']
                elif re.compile('(http|https)://widgets\.itunes\.apple\.com/', re.I).search(src):
                    yield self.suggestionList['itunesembed']
                elif re.compile('(http|https)://www\.youtube\.com/embed/', re.I).search(src):
                    yield self.suggestionList['youtubeembed']
            except KeyError: # if iframe doesn't have attribute 'src'
                pass
        # if direct links to music stores
        for link in self.allLinks:
            if re.compile('(itunes)', re.I).search(link):
                self.storeLinks.add("Itunes")
            if re.compile('(play\.google)', re.I).search(link):
                self.storeLinks.add("Google Play")
            if re.compile('(soundcloud)', re.I).search(link):
                self.storeLinks.add("Sound Cloud")
            if re.compile('(bandcamp)', re.I).search(link):
                self.storeLinks.add("Band Camp")
        # if WordPress site
        meta = self.bs.find("meta", attrs={'name': 'generator'})
        if meta:
            if re.compile('wordpress', re.I).search(meta.attrs['content']):
                yield self.suggestionList['wordpress']
        # donations are always an option
        yield self.suggestionList['donations']

    def getStoreSuggestion(self):
        if self.storeLinks:
            storeString = ""
            if len(self.storeLinks) == 0:
                return storeString
            elif len(self.storeLinks) == 1:
                storeString = self.storeLinks.pop()
            elif len(self.storeLinks) == 2:
                storeString = self.storeLinks.pop() + " and " + self.storeLinks.pop()
            else:
                for i in range(len(self.storeLinks) - 1):
                    storeString += self.storeLinks.pop() + ", "
                storeString += "and " + self.storeLinks.pop()
            return self.suggestionList['storelinks'] % (storeString)
        else:
            return None
