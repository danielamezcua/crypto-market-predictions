import pymongo
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import logging


SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
DATABASE_NAME = "reddit_data"
LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"

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
