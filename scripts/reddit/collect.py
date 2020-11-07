import praw
import pprint
import pymongo
import requests
import json
import sys,os,getopt
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import pytz
import re
from prawcore.exceptions import NotFound
from datetime import datetime,timedelta,date, timezone
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import logging

URL_PUSHSHIFT = "https://api.pushshift.io/reddit/search/submission/"
SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
DATABASE_NAME = "reddit_data"
LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"

#connect to reddit API
reddit = praw.Reddit(
	os.environ.get('reddit_client_id')
	os.environ.get('reddit_client_secret')
	os.environ.get('reddit_user_agent')
)

subreddits = ["xrp","ripple", "bitcoin", "btc", "litecoin", "litecoinmarkets", "ethtrader", "ethfinance"]

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
mydb = myclient[DATABASE_NAME]
submissions_db = mydb[SUBMISSIONS_COLLECTION]
comments_db = mydb[COMMENTS_COLLECTION]

#initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

def is_daily_discussion(id_subreddit, title):
	""" 
	This function tells us if a reddit submission is a Daily Discussion thread
	Parameters: 
	    id_subreddit (String): The id of the subreddit that holds the submission
	    title (String): The title of the submission to be analized.
	Returns: 
	    bool: True indicating it is a daily discussion; False indicating it is not.
	"""

	regex_daily_discussions = {
		"t5_2s3qj": "^Daily Discussion,(.*)", #r/Bitcoin
		"t5_2yx36": "^\\[Daily Discussion\\](.*)", #r/LitecoinMarkets
		"t5_2r9sg": "^Daily Ripple/XRP Discussion Thread(.*)", #r/Ripple
		"t5_2ruj5": "^Daily XRP Discussion Thread(.*)", #r/xrp
		"t5_v7civ": "^Daily General Discussion -(.*)" #r/ethfinance
	}

	if id_subreddit not in regex_daily_discussions:
		return False

	if re.match(regex_daily_discussions[id_subreddit], title):
		return True
	return False

def write_log(msg):
	""" 
	The function that writes to a log file a message
	Parameters: 
	    msg (String): The message to be written into the log file.
	Returns: 
	    void
	"""
	f = open("logs.txt", "a")
	t = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
	f.write(msg + " @ " + t + "\n")
	f.close()

def generate_dates(start,end):
	""" 
	Generator that yields pairs of dates corresponding to a period of time of one day. 
	Parameters: 
	    start (date): The start date
	    end (date): The end date
	Returns: 
	    int, int: the start date and end date as timestamp
	"""
	n_days = (end-start).days
	for i in range(0,n_days):
		day = start+timedelta(i)
		start_epoch = int(datetime(day.year,day.month,day.day,0,0,0).timestamp())
		end_epoch = int(datetime(day.year,day.month,day.day,23,59,59).timestamp())
		yield start_epoch, end_epoch

def daily_collect(shift=1):
	""" 
	Triggers the fecthing of the data posted on the day that this
	function is called. 
	Parameters: 
	   shift (int) : 1 for midnight shift, 2 for afternoon shift
	Returns: 
	    void
	"""

	day = date.today()
	if shift == 1:
		start_date = int(datetime(day.year,day.month,day.day,0,0,0).timestamp())
		end_date = int(datetime(day.year,day.month,day.day,23,59,59).timestamp())
	else:
		start_date = int(datetime(day.year,day.month,day.day,0,0,0,tzinfo=timezone.utc).timestamp())
		end_date = int(datetime(day.year,day.month,day.day, 23,59,59, tzinfo=timezone.utc).timestamp())
	
	fetch_data(start_date,end_date)

def construct_submission_obj(submission, submission_obj):
	""" 
	Extracts the relevant data from the submission object received from the api 
	and adds sentiment to it.
	Parameters: 
	   submission (dict) : submission object received by api
	   submission_obj (dict) : target dictionary where the relevant info is to be stored
	Returns: 
	    void
	"""
	daily_discussion = is_daily_discussion(submission.subreddit_id, submission.title)
	submission_obj["category"] = submission.category
	submission_obj["created"] = submission.created
	submission_obj["created_utc"] = submission.created_utc
	dt_object = datetime.fromtimestamp(submission.created_utc)
	date_aux = dt_object.strftime("%d/%m/%Y")
	submission_obj["date"] = date_aux
	submission_obj["downs"] = submission.downs
	submission_obj["_id"] = submission.id
	submission_obj["num_comments"] = submission.num_comments
	submission_obj["score"] = submission.score
	submission_obj["selftext"] = submission.selftext
	submission_obj["subrreddit_id"] = submission.subreddit_id
	submission_obj["subreddit_name_prefixed"] = submission.subreddit_name_prefixed
	submission_obj["title"] = submission.title
	submission_obj["ups"] = submission.ups
	submission_obj["url"] = submission.url
	submission_obj["daily_discussion"] = daily_discussion

	#add sentiment
	scores = get_sentiment(submission_obj["title"])
	submission_obj["compound_title"] = scores["compound"]
	submission_obj["neg_title"] = scores["neg"]
	submission_obj["neu_title"] = scores["neu"]
	submission_obj["pos_title"] = scores["pos"]

	scores = get_sentiment(submission_obj["selftext"])
	submission_obj["compound_selftext"] = scores["compound"]
	submission_obj["neg_selftext"] = scores["neg"]
	submission_obj["neu_selftext"] = scores["neu"]
	submission_obj["pos_selftext"] = scores["pos"]

def construct_comment_obj(comment, comment_obj, is_daily_discussion):
	""" 
	Extracts the relevant data from the comment object received from the api 
	and adds sentiment to it.
	Parameters: 
	   comment (dict) : comment object received by api
	   comment_obj (dict) : target dictionary where the relevant info is to be stored
	   is_daily_discussion (boolean): 	whether the comment belongs to a daily discussion
	   									thread
	Returns: 
	    void
	"""

	comment_obj["body"] = comment.body
	comment_obj["created"] = comment.created
	comment_obj["created_utc"] = comment.created_utc
	dt_object = datetime.fromtimestamp(comment.created_utc)
	date_aux = dt_object.strftime("%d/%m/%Y")
	comment_obj["date"] = date_aux
	comment_obj["depth"] = comment.depth
	comment_obj["downs"] = comment.downs
	comment_obj["link_id"] = comment.link_id
	comment_obj["name"] = comment.name
	comment_obj["parent_id"] = comment.parent_id
	comment_obj["subreddit_id"] = comment.subreddit_id
	comment_obj["subreddit_name_prefixed"] = comment.subreddit_name_prefixed
	comment_obj["score"] = comment.score
	comment_obj["ups"] = comment.ups

	comment_obj["_id"] = comment.id
	comment_obj["from_daily_disc"] = is_daily_discussion

	#add sentiment
	scores = get_sentiment(comment_obj["body"])
	comment_obj.update(scores)

def get_sentiment(text):
	""" 
	Sentiment analysis on a text.
	This analysis is performed using the VADER tool.
	Parameters: 
	   text (string) :	text to be analysed
	Returns: 
	   vs (dictionary) : polarity scores calculated in the analysis
	"""
	return analyzer.polarity_scores(text)

def bulk_collect():
	""" 
	Collects all data posted between two dates
	Parameters: 
	    
	Returns: 
	    void
	"""
	start_date_query = date(2020,8,8)
	end_date_query = date(2020,8,11)
	for start_date, end_date in generate_dates(start_date_query,end_date_query):
		print(date.fromtimestamp(start_date))
		fetch_data(start_date,end_date)

def fetch_data(start_date,end_date):
	""" 
	Fetches data between two dates from the reddit api and saves it to the database. 
	Parameters: 
	    start (date): The start date
	    end (date): The end date
	Returns: 
	    void
	"""
	for subreddit in subreddits:
		write_log("Collecting submissions and comments from " + subreddit + "...")
		total_submissions = 0
		total_comments = 0
		#make request to the pushshift API
		
		params = {
					"sort": "desc", 
					"sort_type": "created_utc", 
					"subreddit": subreddit, 
					"size": 1000,
					"after": start_date-1, 
					"before": end_date
				}
		while True:
			response = requests.get(url=URL_PUSHSHIFT,params=params)
			try:
				data = response.json()
				break
			except json.decoder.JSONDecodeError:
				print(response.status_code)
				

		#now that we have the data of the submissions of a day, 
		#obtain the comments of each one
		total_submissions += len(data["data"])
		for sub in data["data"]:
			try:

				#construct submission object
				submission = reddit.submission(id = sub["id"])
				submission_obj = {}
				construct_submission_obj(submission, submission_obj)
				is_daily_discussion = submission_obj["daily_discussion"]

				#save submission object
				submissions_db.update_one({"_id": sub["id"], "created_utc": submission_obj.created_utc}, {"$set" :submission_obj}, upsert=True)
				total_submissions+=1

				#obtain and construct comment objects
				submission.comments.replace_more(limit=None)
				list_comments = submission.comments.list()
				if len(list_comments) > 0:
					total_comments+= len(list_comments)
					comments_operations_list = []
					for comment in list_comments:
						comment_obj = {}
						construct_comment_obj(comment, comment_obj, is_daily_discussion)
						comments_operations_list.append(pymongo.UpdateOne({"_id": comment.id, "created_utc": comment.created_utc}, {"$set": comment_obj}, upsert=True))

					#save comments objects
					comments_db.bulk_write(comments_operations_list)
			except NotFound:
				write_log("Unexpected error on subrredit " + subreddit + " and submission "+ sub["id"] + ": " + str(sys.exc_info()[0]))
				continue

		write_log("Done. " + str(total_submissions) + " submissions and " + str(total_comments) + " comments from " + subreddit + " where obtained.")

def add_discussion_comments():
	""" 
	Function used to add an attribute to the comment objects from the comments collection
	to indicate whether the comment belongs to a daily discussion. This function is no longer
	needed because this information is now added to the object when retrieving it from reddit api.
	Parameters: 
	    
	Returns: 
	    void
	"""
	subreddits_with_discussions = ["xrp", "ripple", "bitcoin", "litecoinmarkets", "ethfinance"]
	regex_daily_discussions = {
		"bitcoin": "^Daily Discussion,(.*)", #r/Bitcoin
		"litecoinmarkets": "^\\[Daily Discussion\\](.*)", #r/LitecoinMarkets
		"ripple": "^Daily Ripple/XRP Discussion Thread(.*)", #r/Ripple
		"xrp": "^Daily XRP Discussion Thread(.*)", #r/xrp
		"ethfinance": "^Daily General Discussion -(.*)" #r/ethfinance
	}
	for subreddit in subreddits:
		print("Processing " + subreddit + " comments")
		if subreddit in subreddits_with_discussions:
			subreddit_pattern = "r\/" + subreddit
			regex_subreddit = re.compile(subreddit_pattern, re.IGNORECASE)
			regex_daily_discussion = re.compile(regex_daily_discussions[subreddit])
			submissions = submissions_db.find(
				{
					"subreddit_name_prefixed": regex_subreddit,
					"title": regex_daily_discussion
				}
			)
			for submission in submissions:
				comments_db.update(
					{
						"link_id": "t3_" + submission["_id"]					
					},
					{ 
						"$set": {
							"from_daily_disc" : True
						}
					}, 
					multi=True
				)
		print("Done")

def add_posts(id_posts):
	""" 
	Collects data from specific posts
	Parameters: 
	    id_posts (list): a list of the id strings of the posts to collect
	Returns: 
	    void
	"""
	total_submissions = 0
	total_comments = 0
	for id in id_posts:
		try:
			#construct submission object
			submission = reddit.submission(id = id)
			submission_obj = {}
			construct_submission_obj(submission, submission_obj)
			is_daily_discussion = submission_obj["daily_discussion"]

			#save submission object
			submissions_db.update_one({"_id": id, "created_utc": submission_obj.created_utc}, {"$set" :submission_obj}, upsert=True)
			total_submissions+=1

			#obtain and construct comment objects
			submission.comments.replace_more(limit=None)
			list_comments = submission.comments.list()
			if len(list_comments) > 0:
				total_comments+= len(list_comments)
				comments_operations_list = []
				for comment in list_comments:
					comment_obj = {}
					construct_comment_obj(comment, comment_obj, is_daily_discussion)
					comments_operations_list.append(pymongo.UpdateOne({"_id": comment.id}, {"$set": comment_obj}, upsert=True))

				#save comments objects
				comments_db.bulk_write(comments_operations_list)

		except NotFound:
			print("skipping %s" % id)
			#logging.info("Unexpected error on submission" + id + ": " + str(sys.exc_info()[0]))
			continue

def main():
	""" 
	Main function. Triggers the start of the reddit collect process.
	    
	Returns:
	    int : the exit status
	"""

	#parse command-line arguments		
	argv = sys.argv[1:]

	if not argv:
		print("Usage: python3 collect.py [--shift 1(midnight)| 2(afternoon)] [--bulk] [--posts id_post1,id_post2]")
		return 2

	try:
		opts, args = getopt.getopt(argv,"", ["shift=", "bulk", "posts="])
	except:
		print("Usage: python3 collect.py [--shift 1(midnight)| 2(afternoon)] [--bulk] [--posts id_post1,id_post2]")
		return 2

	bulk = False
	shift = None
	id_posts = None

	for opt,arg in opts:
		if opt in ['--shift']:
			shift = int(arg)
		elif opt in ['--bulk']:
			#TODO: recieve bulk dates
			bulk = True
		elif opt in['--posts']:
			id_posts = arg.split(',')
		else:
			print("Usage: python3 collect.py [--shift 1(midnight)| 2(afternoon)] [--bulk] [--posts id_post1,id_post2]")
			return 2

	#trigger actions based on arguments
	if bulk:
		bulk_collect()

	if shift is not None:
		daily_collect(shift)

	if id_posts is not None:
		add_posts(id_posts)

if __name__ == "__main__":
	sys.exit(main())
