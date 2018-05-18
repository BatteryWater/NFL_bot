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

def DefaultCheck(value):
    if value is None:
        return "-"
    return value.text


def bot_login():
    print("Loggin in...")
    print(config.username)
    print(config.client_id)
    print(config.client_secret)
    print(config.password)

    r = praw.Reddit(username = config.username,
            password = config.password,
            client_id = config.client_id,
            client_secret = config.client_secret,
            user_agent = "NFL Player Stats Bot v0.1")
    print("Logged in!")

    return r

class Player:
    def __init__(self, soup):
        self.GetInfo(soup)

    def GetInfo(self, soup):
        """Scrape and parse relevant player stats from the soup"""
        self.Name = soup.find('h1', {'itemprop':'name'}).text
        #height = soup.find('span', {'itemprop':'height'}).text
        self.Height = DefaultCheck(soup.find('span', {'itemprop':'height'}))
        #self.Height = soup.find('span', {'itemprop':'height'}).text
        self.Weight = DefaultCheck(soup.find('span', {'itemprop':'weight'}))
        #weight = soup.find(
        team = soup.find('span', {'itemprop' : 'affiliation'})
        if team is not None:
            self.Team = team.find('a').text
            self.TeamURL = "https://www.pro-football-reference.com" + team.find('a')['href']
            self.TeamString = "[{}]({})".format(self.Team, self.TeamURL)
        else:
            self.Team = None
            self.TeamURL = None
            self.TeamString = "Free Agent"
        self.DOB = DefaultCheck(soup.find('span', {'itemprop':'birthDate'}))
        #self.College = DefaultCheck(soup.find('span', {'itemprop':'fig'})) #TODO:
        self.Stats = Stats(soup.find('div', {'class':'stats_pullout'}))


    def __str__(self):
        teamstring = "[{}]({})".format(self.Team, self.TeamURL)
        s= """**Name:** {}\n
**Height:** {}\n
**Weight:** {}\n
**Team:** {}\n\n **Date of Birth:** {}\n{}\n\n\n\n""".format(self.Name, self.Height, self.Weight, self.TeamString, self.DOB, self.Stats)
        return s



def StatsTest(url):
    soup = BeautifulSoup(requests.get(url).text, "lxml")
    print(Stats(soup.find('div', {'class':'stats_pullout'})))


class Stats:
    def __init__(self, statsDiv):
        """Encapsulation of stats table data"""
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
            #print(p)
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
            #print(len(val))
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
        #print(maxPCount)
        if(maxPCount > 1):
            for key, val in self.statDict.items():
                retStringList.append(val[1])
                retStringList.append('|')
            del retStringList[-1]

        return ''.join(retStringList)




def IsPosMatch(position, toCheck):
    if position.ascii_lowercase == toCheck.ascii_lowercase:
        return True
    return False

def response_bs_pfr(player, position):
    """BeautifulSoup PFR scraped response generator"""
    print(player)
    searchUrl = requests.get("https://www.pro-football-reference.com/search/search.fcgi?hint=&search={}".format(player.replace(" ", "+")))
    soup = BeautifulSoup(searchUrl.text, "lxml")
    responsePlayers = []
    players = soup.find('div', id="players")
    if players is None:
            info = soup.find('div', id="info")
            responsePlayers.append(str(Player(info)))
            #print(p)
    else:
            playerUrlList = []
            if position is None or position is "":#filter by position if possible
                playerUrls = players.find_all('a')
                for player in playerUrls:
                    playerUrlList.append(player['href'])
            else:
                    matchedPos = players.find_all("div", {"class":"search-item-name"})
                    for match in matchedPos:
                                            #print(position)
                                            if re.search(str(position.upper()), match.text) is not None:
                                                url = match.find('a')
                                                print(url)
                                                playerUrlList.append(url['href'])
                                                #print(url.find('href'))
                                                #print(url['href'])
                                                #print (match.text)
                                                #responsePlayers.append(match)

            if len(playerUrlList) != 0:
                for playerUrl in playerUrlList[0:3]:
                    player = BeautifulSoup(requests.get("https://www.pro-football-reference.com/{}".format(playerUrl)).text, "lxml")
                    #print(Player(player))
                    #info = player.find('div', id="info")
                    responsePlayers.append(str(Player(player)))
            else:
                print("No matches")
                #print(info)

            #at least one player
            #comment each player

    return ''.join(responsePlayers)
    #print(searchUrl.url)
    #print(soup.url)
    #print(searchUrl.text)

def response(player, player_info):
    if player is not None:
        search = requests.get("http://www.nfl.com/players/search?category=name&filter={}&playerType=current".format(player.replace(" ", "+")))

        search_tree = html.fromstring(search.content)

        if search_tree.xpath('//div[@id="searchResults"]//@href'):
            search_result = search_tree.xpath('//div[@id="searchResults"]//@href')[0]
        else:
            search_result = None

        if search_result is not None:

            page = requests.get("http://www.nfl.com" + str(search_tree.xpath('//div[@id="searchResults"]//@href')[0]))
            tree = html.fromstring(page.content)
            bio = tree.xpath('//div[@class="player-info"]//p//text()')

            player_info["Name"] = str(tree.xpath('//div[@class="player-info"]//span[@class="player-name"]/text()')[0].encode("ascii", errors="ignore").decode()).strip()
            print("player name: " + player_info["Name"])
            player_info["Number"] = str(tree.xpath('//div[@class="player-info"]//span[@class="player-number"]/text()')[0].encode("ascii", errors="ignore").decode()).strip()

            player_info["Height"] = str(bio[bio.index("Height") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip().replace("-", "ft ").strip()

            player_info["Weight"] = str(bio[bio.index("Weight") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip()

            player_info["Age"] = str(bio[bio.index("Age") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip()

            player_info["D.O.B"] = str(bio[bio.index("Born") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip()

            player_info["Seasons Played"] = str(bio[bio.index("Experience") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip()

            player_info["College"] = str(bio[bio.index("College") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip()

            player_info["High School"] = str(bio[bio.index("High School") + 1].encode("ascii", errors="ignore").decode()).split(": ",1)[1].strip()

            player_info["Current Team"] = "[ {} ]( {} )".format(str(tree.xpath('//div[@class="player-info"]//p[@class="player-team-links"]//a/text()')[0]).strip(), str(tree.xpath('//div[@class="player-info"]//p[@class="player-team-links"]//@href')[1]).replace(".com/", ".com"))

        # player_info["seasons_played_for_current_team"] = ""
        # player_info["career_total_stats"] = ""
        # player_info["games_played"] = ""
        # player_info["game_victories"] = ""
        # player_info[""] = ""

        return player_info

def comment_message(response_message, player_info):
    for k,v in player_info.iteritems():
        response_message = response_message + ("> {}: {}\n\n".format(str(k), str(v)))

    return response_message

def run_bot(r, comments_replied_to):
    try:
        print("Obtaining 250 comments...")
        for comment in r.subreddit('test').comments(limit=250):

            #match = re.search(r"\[\[(.*?)\]\]", comment.body)
            match = re.findall("\[\[([\w'\-\s]+)(\([\w'\-\s]+\))?\]\]", comment.body)
           # print(match)
            #if match is not None:
               #print(len(match))
            if match is not None and (len(match) > 0) and comment.id not in comments_replied_to and comment.author != config.username:
                if len(match) > 1:
                    comment.reply(response_bs_pfr(match[0][0], match[1]))
                else:
                    comment.reply(response_bs_pfr(match[0][0], None))



            #if(match) and comment.id not in comments_replied_to and comment.author != config.username:

                #comment_reply = comment_message("Player Stats: \n\n", response(match.group(1).replace("'", "%91"), player_info))
                #comment.reply(comment_reply)
                comments_replied_to.add(comment.id)

                with open ("comments_replied_to.txt", "a") as f:
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

def get_saved_comments():
    #comments_replied_to = set()
    try:
        if not os.path.isfile("comments_replied_to.txt"):
            comments_replied_to = set()
        else:
            comments_replied_to = set(open('comments_replied_to.txt').read().split())
            #with open ("comments_replied_to.txt", "r") as f:
                #comments_replied_to = f.read()
                #comments_replied_to = comments_replied_to.split("\n")
                #comments_replied_to = filter(None, comments_replied_to)
        return comments_replied_to

    except PermissionError as e:
        print("Permission Error! Ensure filepath is set to a directory in which you have create/edit permissions")

def start_up():
    try:
        r = bot_login()
    except prawcore.exceptions.OAuthException:
        print("OAUTH Exception! Check config info")
        return
    comments_replied_to = get_saved_comments()
    print(comments_replied_to)
    while True:
        try:
            run_bot(r, comments_replied_to)
        except KeyboardInterrupt:
            print("Shutting down.")
            break
    #print(comments_replied_to)


start_up()
