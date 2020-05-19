import pymongo
from datetime import datetime, timezone
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
import logging
import csv
from collections import defaultdict
from lm_lexicon import lm_positive, lm_negative

SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
DATABASE_NAME = "reddit_data"
LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"
NEWS_DATABASE_NAME = "news_data"
NEWS_COLLECTION = "coin_telegraph_news"

#set logger
logging.basicConfig(filename='./logs.txt', level=logging.INFO, format='%(name)s@%(asctime)s - %(message)s')

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
mydb = myclient[DATABASE_NAME]
submissions_db = mydb[SUBMISSIONS_COLLECTION]
comments_db = mydb[COMMENTS_COLLECTION]
submissions_db = mydb[SUBMISSIONS_COLLECTION]

query_start_date = datetime(2019,9,1).replace(tzinfo=timezone.utc).timestamp()
query_end_date =datetime(2020,5,1).replace(tzinfo=timezone.utc).timestamp()

subreddits_regex = ["r\/btc", "r\/ripple", "r\/xrp", "r\/bitcoin", "r\/litecoin",
 "r\/litecoinmarkets", "r\/ethtrader",
"r\/ethfinance"]

analyzer = SentimentIntensityAnalyzer()
analyzer.lexicon.update(lm_positive)
analyzer.lexicon.update(lm_negative)

def add_sentiment_reddit():
	for subreddit in subreddits_regex:
		logging.info("Adding sentiment data to comments of %s", subreddit.split('/')[1])
		regx = re.compile(subreddit, re.IGNORECASE)

		#add sentiment values to the comments
		comments = comments_db.find({
			"created_utc" : {
								"$gt" : query_start_date,
								"$lt": query_end_date
							},
			"subreddit_name_prefixed": regx
		})

		no_comments = 0
		if subreddit.split('/')[1] != "btc":
			for comment in comments:
				#check if it has already been anaalyzed
				if "compound" in comment:
					continue
				query = {
					"_id" : comment["_id"]
				}
				vs = analyzer.polarity_scores(comment["body"])
				comments_db.update_one(query, {"$set": vs})
				no_comments+=1

		logging.info("Done. %d comments from %s where analyzed.", no_comments, subreddit.split('/')[1])

		#add sentiment values to the posts
		logging.info("Adding sentiment data to submissions of %s", subreddit.split('/')[1])
		no_submissions = 0
		submissions = submissions_db.find({
			"created_utc" : {
								"$gt" : query_start_date,
								"$lt": query_end_date
							},
			"subreddit_name_prefixed": regx
		})

		for submission in submissions:
			query = {
				"_id" : submission["_id"]
			}
			#check if it has already been analyzed
			if "compound_title" in submission:
				continue
			vs = analyzer.polarity_scores(submission["title"])
			vs_doc = {}
			vs_doc["compound_title"] = vs["compound"]
			vs_doc["neg_title"] = vs["neg"]
			vs_doc["neu_title"] = vs["neu"]
			vs_doc["pos_title"] = vs["pos"]
			vs = analyzer.polarity_scores(submission["selftext"])
			vs_doc["compound_selftext"] = vs["compound"]
			vs_doc["neg_selftext"] = vs["neg"]
			vs_doc["neu_selftext"] = vs["neu"]
			vs_doc["pos_selftext"] = vs["pos"]
			comments_db.update_one(query, {"$set": vs})
			no_submissions+=1
		logging.info("Done. %d submissions from %s where analyzed.", no_submissions, subreddit.split('/')[1])

def add_sentiment_news():
	logging.info("Adding sentiment data to news of Coin Telegraph")
	db = myclient[NEWS_DATABASE_NAME]
	news_collection = db[NEWS_COLLECTION]
	news = news_collection.find()
	analysed_news = 0
	not_analysed = 0
	for new in news:
		data = {}
		if new["analysis"] == True:
			actual_coin = None
			flag = False
			compounds = []
			for paragraph in new["content"]:
				if re.match("^.*/USD$", paragraph):
					#the analysis of a coin is coming in the next paragraphs
					#if a previous analysis was being read, set the compound average of the last coin
					if actual_coin != None:
						data["sent_comp_"+actual_coin] = sum(compounds)/len(compounds)
						compounds = []
					if paragraph == "BTC/USD":
						flag = True
						actual_coin = "btc"
					elif paragraph == "XRP/USD":
						flag = True
						actual_coin = "xrp"
					elif paragraph == "LTC/USD":
						flag = True
						actual_coin = "ltc"
					elif paragraph == "ETH/USD":
						flag = True
						actual_coin = "eth"
					else:
						actual_coin = None
						flag = False
				elif flag:
					compounds.append(analyzer.polarity_scores(paragraph)["compound"])
		else:
			compounds = []
			for paragraph in new["content"]:
				comp = analyzer.polarity_scores(paragraph)["compound"]
				if comp != 0.0:
					compounds.append(comp)
			data["sent_comp"] = sum(compounds)/len(compounds)
		query = {
					"id_new" : new["id_new"]
				}
		if not data:
			not_analysed += 1
		else:
			news_collection.update_one(query, {"$set": data})
			analysed_news += 1
	logging.info("Done. %d news where analysed. %d news couldn't be analysed", analysed_news, not_analysed)


def add_lm_lexicon():
	positives = {}
	negatives = {}
	with open('../LoughranMcDonald_MasterDictionary_2018.csv', newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if int(row["Positive"]) != 0:
				positives[row["Word"].lower()] = 2
			elif int(row["Negative"]) != 0:
				negatives[row["Word"].lower()] = -2
	print(positives)
	print(negatives)

add_sentiment_news()

