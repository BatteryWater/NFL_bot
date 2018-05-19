from lxml import html
from collections import OrderedDict
import re
import requests
import praw
import config
import time
import os
import requests
import random
import traceback
from bs4 import BeautifulSoup
player_info = OrderedDict()

def defaultCheck(value):
    if value is None:
        return "-"
    return value.text


def botLogin():
    print("Logging in...")

    r = praw.Reddit(username = config.username,
            password = config.password,
            client_id = config.client_id,
            client_secret = config.client_secret,
            user_agent = "NFL Player Stats Bot v0.1")
    print("Logged in!")
    return r

class Player:
    """Encapsulation for Player stats"""
    def __init__(self, url):
        self.GetInfo(url)

    def GetInfo(self, url):
        """Scrape and parse relevant player stats from the soup"""
        print(url)
        soup = BeautifulSoup(requests.get(url).text, "lxml")
        self.Name = soup.find('h1', {'itemprop':'name'}).text.strip()
        self.PlayerURL = url
        self.NameString = "[{}]({})".format(self.Name, self.PlayerURL)
        self.Height = defaultCheck(soup.find('span', {'itemprop':'height'}))\
                        .strip()
        self.Weight = defaultCheck(soup.find('span', {'itemprop':'weight'}))\
                        .strip()
        team = soup.find('span', {'itemprop' : 'affiliation'})
        if team is not None:
            self.Team = team.find('a').text.strip()
            self.TeamURL = "https://www.pro-football-reference.com" + \
                            team.find('a')['href'].strip()
            self.TeamString = "[{}]({})".format(self.Team, self.TeamURL)
        else:
            self.Team = None
            self.TeamURL = None
            self.TeamString = "Free Agent"
        self.DOB = defaultCheck(soup.find('span', {'itemprop':'birthDate'}))\
                        .strip()
#TODO:     #self.College = DefaultCheck(soup.find('span', {'itemprop':'fig'}))
        self.Stats = Stats(soup.find('div', {'class':'stats_pullout'}))


    def __str__(self):
        s= "**Name:** {}\n\n**Height:** {}\n\n**Weight:** {}\n\n"\
                .format(self.NameString,
                        self.Height,
                        self.Weight)
        sTwo = "**Team:** {}\n\n**Date of Birth:** {}\n\n{}\n\n\n\n"\
                .format(self.TeamString,
                        self.DOB,
                        self.Stats)
        return s + sTwo


class Stats:
    """Encapsulation of stats table data"""
    def __init__(self, statsDiv):
        self.statDict = {}
        if statsDiv is None:
            return
        cols = statsDiv.find_all('div')
        if cols is None:
            return
        for col in cols:
            key = col.find_all('h4')[0].text
            p = col.find_all('p')
            if(len(p) > 1):
                self.statDict[key] = [p[0].text, p[1].text]
            else:
                self.statDict[key] = [p[0].text]

    def __str__(self):
        """Formats to reddit's table markup"""
        if len(self.statDict) == 0:
            return ""
        colCount = len(self.statDict)
        retStringList= []
        maxPCount = 0
        for key, val in self.statDict.items():
            retStringList.append(key)
            retStringList.append('|')
            maxPCount = max(maxPCount, len(val))

        del retStringList[-1]
        retStringList.append("\n")

        for i in range(0, colCount):
            retStringList.append(":--")
            retStringList.append("|")

        del retStringList[-1]
        retStringList.append('\n')

        for key, val in self.statDict.items():
            retStringList.append(val[0])
            retStringList.append('|')

        del retStringList[-1]
        retStringList.append("\n")

        if(maxPCount > 1):
            for key, val in self.statDict.items():
                retStringList.append(val[1])
                retStringList.append('|')
            del retStringList[-1]
        retStringList.append("\n\n\n\n")

        return ''.join(retStringList)


def getPlayerURLs(playerName, position):
    """Searches for playerName, returns a list of the first exact match or
    first three matches"""
    urlBaseString = "https://www.pro-football-reference.com" +\
    "/search/search.fcgi?hint=&search="
    siteBaseString = "https://www.pro-football-reference.com"
    searchUrl = requests.get(urlBaseString + playerName.replace(" ", "+"))
    url = searchUrl.url
    soup = BeautifulSoup(searchUrl.text, "lxml")
    playerURLsList = []
    playersDiv = soup.find('div', id="players")

    if playersDiv is None:
        playerURLsList.append(url)
        return playerURLsList

    if position is None or position is "":
        playerURLS = playersDiv.find_all('a')
        for player in playerURLS:
            playerURLsList.append(siteBaseString + player['href'])
            if(len(playerURLsList) == 3):
                break
    else:
        matchedPos = playersDiv.find_all("div", {"class":"search-item-name"})
        for match in matchedPos:
            if re.search(str(position.upper()), match.text) is not None:
                url = match.find('a')
                playerURLsList.append(siteBaseString + url['href'])
                if(len(playerURLsList) == 3):
                    break
    return playerURLsList


def runBotLoop(r, comments_replied_to):
    try:
        print("Obtaining 250 comments...")
        for comment in r.subreddit('test').comments(limit=250):
            if isValidComment(comment, comments_replied_to):
                replies = processComment(comment)
                if replies is not None and len(replies) > 0:
                    comment.reply(''.join(replies))
                    comments_replied_to.add(comment.id)
                    with open("comments_replied_to.txt", "a") as f:
                        f.write(comment.id + "\n")

        print("Sleeping for 10 seconds...")
        time.sleep(10)

    except praw.exceptions.APIException as e:
        exc = e._raw
        print("Something bad happened! APIException", exc.status_code)
        if exc.status_code == 503:
            print("Let's wait til reddit comes back! Sleeping 60 seconds.")
        time.sleep(60)

    except Exception as e:
        print("Something bad happened!", e)
        traceback.print_exc()


def isValidComment(comment, comments_replied_to):
    return (comment.id not in comments_replied_to) and \
     comment.author is not config.username


def processComment(comment):
    """Processes a comment. Returns a string representing a comment reply, or
    None in the case that a comment doesn't need a reply"""
    replies = []
    matches = getMatches(comment)
    for match in matches:
        replies.append(response_bs_pfr(match[0], match[1]))
    return replies


def getMatches(comment):
    """returns a list of matching groups"""
    pattern = "\[\[([\w+'\-\s]+)(?:\]\]|(?:\()([\w+'-]+)(?:\))\]\])"
    match = re.findall(pattern, comment.body)
    responseComments = []
    if(match is not None and len(match) > 0):
        for groupMatch in match:
            if len(groupMatch[0]) > 1:
                responseComments.append((groupMatch[0].strip(), groupMatch[1]))
            else:
                reponseComments.append((groupMatch[0].strip(), None))
    return responseComments


def getSavedComments():
    try:
        if not os.path.isfile("comments_replied_to.txt"):
            comments_replied_to = set()
        else:
            comments_replied_to = \
                set(open('comments_replied_to.txt').read().split())

        return comments_replied_to

    except PermissionError as e:
        print("Permission Error! Ensure filepath is set to a directory " + \
            "in which you have create/edit permissions")


def startUp():
    try:
        r = botLogin()
    except prawcore.exceptions.OAuthException:
        print("OAUTH Exception! Check config info")
        return
    comments_replied_to = getSavedComments()
    print(comments_replied_to)
    while True:
        try:
            runBotLoop(r, comments_replied_to)
        except KeyboardInterrupt:
            print("Shutting down.")
            break

if __name__ == '__main__':
    startUp()
