#! /usr/bin/python

# this program scrapes a news webpage for all links, filters the links for stories only and compiles a dictionary

# worzel_gummidge

import urllib
import re
import os
import glob
import Queue
import threading
import sys
from bs4 import BeautifulSoup

#this function compares the links fetched to the links previously fetched
def getNewLinks(links):
    try:
        fd = open('/usr/share/shwoma/links.dat', 'r')
    except:
        try:
            os.makedirs('/usr/share/shwoma')
        except:
            pass
        try:
            fd = open('/usr/share/shwoma/links.dat', 'w')
        except:
            print "[!]error: unable to create 'links.dat'"
            sys.exit(1)
        fd.close()
        try:
            fd = open('/usr/share/shwoma/links.dat', 'r')
        except:
            print "[!]error: unable to open 'links.dat' for reading"
            sys.exit(1)
    oldLinks = []
    for line in fd.readlines():
        oldLinks.append(line.strip())
    fd.close()
    for item in oldLinks:
        if item in links:
            links.remove(item)
    if len(oldLinks) < 200:
        try:
            fd = open('/usr/share/shwoma/links.dat', 'a')
            for link in links:
                fd.write(link + '\n')
        except:
            print "[!]error: unable to append to links cache"
            sys.exit(1)
    else:
        try:
            fd = open('/usr/share/shwoma/links.dat', 'w')
            for link in links:
                fd.write(link + '\n')
        except:
            print "[!]error: unable to overwrite links cache"
            sys.exit(1)
    return links

#this function opens the webpage
def getPage(site):
    html = urllib.urlopen(site)
    hC = html.code                              # hC = httpCode
    return BeautifulSoup(html.read(), 'lxml')

#this function gets the links from a webpage
def fetchLinks(site):
    soup = getPage(site)
    aL = soup.find_all('a')                     # aL = allLinks
    lL = []                                     # lL = linkList
    for link in aL:
        lL.append(link['href'])
    lS = set(lL)                                # lS = linkSet
    lOL = list(lS)                              # lOL = listOfLinks
    return lOL

#this function filters links found on the kwayedza webpage
def kwayedzaLinkFilter(lOL):

    links = lOL
    unwanted = []

    for link in links:
        if len(link) < 23:
            unwanted.append(link)
    for link in links:
        if not link.startswith('http://kwayedza.co.zw'):
            unwanted.append(link)
    for link in links:
        if link.startswith('http://kwayedza.co.zw/contact-us'):
            unwanted.append(link)
    for link in links:
        if link.startswith('http://kwayedza.co.zw/category'):
            unwanted.append(link)
    for link in links:
        if link.endswith('#respond'):
            unwanted.append(link)
    for link in links:
        if link.endswith('#comments'):
            unwanted.append(link)

    wanted = [x for x in links if x not in unwanted]

    return wanted

#this function scrapes words from kwayedza
def kwayedzaScraper(link):
    soup = getPage(link)
    try:
        story = soup.find('article').find('div',{'class': 'post-content'}).find_all('p')
    except:
        print "[!]error: cannot scrape link for words"
    return story

def addWords():
    global newLinks
    badWords = []

    while not newLinks.empty():
        link = newLinks.get()
        lines = kwayedzaScraper(link)
        for word in str(lines).split(' '):
            if word.startswith('<p>\u201c'):
                badWords.append(word)
        sOL = [x for x in str(lines).split(' ') if x not in badWords]     # sOL = stringOfLines
        sOL = str(sOL)
        rx = re.compile("[^\W\d_]{5,}")
        words = rx.findall(sOL)
        sL = list(set(words))               # sL = sortedList
        for entry in sL:
            fd.write(entry + '\n')
        print "[!]added %d words to list" % len(sL)

def arrangeList():
    fd = open('/usr/share/shwoma/wordlist.txt', 'r')
    uniqSet = set(fd.readlines())
    fd.close()
    uniqList = list(uniqSet)
    uniqList.sort()
    fd = open('/usr/share/shwoma/wordlist.txt', 'w')
    for word in uniqList:
        fd.write(word)
    fd.close()
    print "[*] %d words in list" % len(uniqList)


threads = 10
links = kwayedzaLinkFilter(fetchLinks("http://www.kwayedza.co.zw"))
links = getNewLinks(links)
newLinks = Queue.Queue()
try:
    fd = open('/usr/share/shwoma/wordlist.txt', 'a')
    print "[*] Adding to wordlist.."
except:
    try:
        fd = open('/usr/share/shwoma/wordlist.txt', 'w')
        print "[*] Wordlist not found! Creating a new wordlist.."
    except:
        print "[!] Error: cannot open 'wordlist.txt'"
numberOfNewLinks = len(links)
for link in links:
    newLinks.put(link)
print "[*] Scraping %d new links" % numberOfNewLinks
threadList = []
for i in range(threads):
    t = threading.Thread(target=addWords)
    threadList.append(t)
for thread in threadList:
    thread.start()
for thread in threadList:
    thread.join()
print "[*] Re-ordering the wordlist.."
arrangeList()
