from lxml import html
from collections import OrderedDict
import re
import requests
import praw
import prawcore
import config
import time
import os
import requests
import random
player_info = OrderedDict()

def bot_login():
	print("Loggin in...")
	r = praw.Reddit(username = config.username,
			password = config.password,
			client_id = config.client_id,
			client_secret = config.client_secret,
			user_agent = "NFL Player Stats Bot v0.1")
	print("Logged in!")

	return r

def response(player, player_info):
	if player is not None:
		search = requests.get("http://www.nfl.com/players/search?category=name&filter={}&playerType=current".format(player.replace(" ", "+")))

		search_tree = html.fromstring(search.content)

		if search_tree.xpath('//div[@id="searchResults"]//@href'):
			search_result = search_tree.xpath('//div[@id="searchResults"]//@href')[0]
		else:
			search_result = None

		if search_result is not None:

			try:
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

				player_info["Seasons Played in Current Team"] = " - "
				# player_info["career_total_stats"] = ""
				# player_info["games_played"] = ""
				# player_info["game_victories"] = ""
				# player_info[""] = ""
			except:
				pass
		return player_info

def comment_message(player_info):
	if not player_info:
		return "`Player not found`"
	else:
		response_message = "Player Bio | Info \n-------|-------\n"
		for k,v in player_info.iteritems():
			response_message = response_message + ("{} | {} \n".format(str(k), str(v)))

		return response_message


def run_bot(r, comments_replied_to):
	# try:
	print("Obtaining 250 comments...")
	for comment in r.subreddit('test').comments(limit=250):

		match = re.search(r"\[\[(.*?)\]\]", comment.body)

		if(match) and comment.id not in comments_replied_to and comment.author != config.username:

			comment_reply = comment_message(response(match.group(1).replace("'", "%91"), player_info))
			comment.reply(comment_reply)
			comments_replied_to.append(comment.id)

			with open ("comments_replied_to.txt", "a") as f:
				f.write(comment.id + "\n")

	print("Sleeping for 10 seconds...")
	time.sleep(10)
	# except (KeyboardInterrupt, SystemExit):
	# 	print("Shutting down.")
	# 	raise
	# except prawcore.exceptions.ServerError as e:
	# 	exc = e._raw
	# 	print("Some thing bad happened! HTTPError", exc.status_code)
	# 	if exc.status_code == 503:
	# 		print("Let's wait til reddit comes back! Sleeping 60 seconds.")
	# 	time.sleep(60)
	# except Exception as e:
	# 	print("Some thing bad happened!", e)
	#
	# 	pass

def get_saved_comments(file):
	if not os.path.isfile(file):
		comments = []
	else:
		with open (file, "r") as f:
			comments = f.read()
			comments = comments.split("\n")
			comments = filter(None, comments)

	return comments

r = bot_login()
comments_replied_to = get_saved_comments("comments_replied_to.txt")
print("Comments replied to: %s \n Comments with errors: %s" % (get_saved_comments("comments_replied_to.txt"), get_saved_comments("comments_with_errors.txt")))

while True:
	run_bot(r, comments_replied_to)
