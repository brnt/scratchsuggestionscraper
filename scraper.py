from __future__ import print_function
import requests
import re
import time
import csv
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException

from bs4 import BeautifulSoup

binaryExtentions = [".mp3", ".aac", ".ogg", ".png", ".jpg", "jpeg", ".gif", ".mov", ".mp4"]

class URLManip:
    def splitAddress(self, address):
        addressParts = address.replace("http://", "").split("/")
        return addressParts

    def isID(self, url):
        if re.compile("#").search(url):
            return True
        return False

    def cleanHref(self, ref):
        if ref[:2] == "./":
            ref = ref[2:]
        elif ref[0] == "/":
            ref = ref[1:]
        return ref

urlManip = URLManip()

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
        self.suggestions.add(self.pages[0].getStoreSuggestion())
        return self.suggestions

class Page:

    suggestionList = {
        'musicbin': "You've embedded music files!  Try monetizing these with a little Scratch magic!",
        'videobin': "You've embedded video files!  Try monetizing these with a little Scratch magic!",
        'smarturl': "Looks like you're sending visitors through smarturl to an external music store.  Why not monetize directly with Scratch?",
        'storelinks': "Your site has links to %s.  Using Scratch would enable you to cut out music stores and make more profit.",
        'itunesembed': "You've embedded an Itunes widget in your site.  You can sell your tracks straight from your site with Scratch!",
        'soundcloudembed': "You've embedded a Sound Cloud player in your site.  You can sell your tracks straight from your site with Scratch!",
        'spotifyembed': "You've embedded a Spotify player in your site.  You can sell your tracks straight from your site with Scratch!",
        'wordpress': "Your website is built in WordPress.  Did you know that Scratch has a WordPress plugin?"
    }

    storeLinks = set()

    def __init__(self, url):
        self.url = url
        self.bs = BeautifulSoup()
        self.internalLinks = []
        self.externalLinks = []
        self.allLinks = []
        self.suggestions = set()
        self.loaded = False

    def load(self):
        # if not a binary file
        if self.url[-4:] not in binaryExtentions:
            try:
                req = requests.get(self.url)
            except:
                print("Connection failed.")
                return False

            self.bs = BeautifulSoup(req.text, 'lxml')
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
                print("Handling client-side redirect...")
                driver = webdriver.PhantomJS(executable_path="/usr/local/lib/node_modules/phantomjs/lib/phantom/bin/phantomjs")
                driver.get(self.url)
                self.waitForLoad(driver)
                self.bs = BeautifulSoup(driver.page_source, 'lxml')
                self.internalLinks = self.getInternalLinks(urlManip.splitAddress(self.url)[0])
                self.externalLinks = self.getExternalLinks(urlManip.splitAddress(self.url)[0])
                self.allLinks = self.internalLinks + self.externalLinks
                driver.close()

    def waitForLoad(self, driver):
        source = driver.page_source
        url = driver.current_url
        count = 0
        while True:
            count += 1
            if count > 16:
                print("Timing out after 8 sec")
                return
            time.sleep(.5)
            if source == driver.page_source or url == driver.current_url:
                pass
            else:
                return

    def getInternalLinks(self, includeURL):
        internalLinks = []
        #Finds all links beginning with "/"
        for link in self.bs.findAll("a", href=re.compile("^(/|.*"+includeURL+")", re.I)):
            if link.attrs['href'] is not None:
                if link.attrs['href'] not in self.internalLinks:
                    if not urlManip.isID(link.attrs['href']):
                        internalLinks.append(urlManip.cleanHref(link.attrs['href']).lower())
        return internalLinks

    def getExternalLinks(self, excludeUrl):
        externalLinks = []
        #Finds all links that start with "http" or "www" that do not contain current url
        for link in self.bs.findAll("a", href=re.compile("^(http|www)((?!"+excludeUrl+").)*$", re.I)):
            if link.attrs['href'] is not None:
                if link.attrs['href'] not in self.externalLinks:
                    if not urlManip.isID(link.attrs['href']):
                        externalLinks.append(urlManip.cleanHref(link.attrs['href']).lower())
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
        self.printLinks()
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
        for link in self.allLinks:
            if re.compile('(itunes)', re.I).search(link):
                self.storeLinks.add("Itunes")
            if re.compile('(play\.google)', re.I).search(link):
                self.storeLinks.add("Google Play")
            if re.compile('(soundcloud)', re.I).search(link):
                self.storeLinks.add("Sound Cloud")
        # if WordPress site

        meta = self.bs.find("meta", attrs={'name': 'generator'})
        if meta:
            if re.compile('wordpress', re.I).search(meta.attrs['content']):
                self.suggestions.add(self.suggestionList['wordpress'])

        return self.suggestions

    def getStoreSuggestion(self):
        if self.storeLinks:
            storeString = ""
            if len(self.storeLinks) == 1:
                storeString = self.storeLinks.pop()
            elif len(self.storeLinks) == 2:
                storeString = self.storeLinks.pop() + " and " + self.storeLinks.pop()
            else:
                for i in range(len(self.storeLinks) - 1):
                    storeString += self.storeLinks.pop() + ", "
                storeString += "and " + self.storeLinks.pop()
            return self.suggestionList['storelinks'] % (storeString)
