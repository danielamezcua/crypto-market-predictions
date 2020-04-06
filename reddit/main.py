import secret
import praw
import pprint
import pymongo
import requests
import sys
from prawcore.exceptions import NotFound
from datetime import datetime,timedelta,date
URL_PUSHSHIFT = "https://api.pushshift.io/reddit/search/submission/"
SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
DATABASE_NAME = "reddit_data"
LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"

def is_daily_discussion(id_subreddit, title):
	""" 
	This function tells us if a reddit submission is a Daily Discussion thread
	Parameters: 
	    id_subreddit (String): The id of the subreddit that holds the submission
	    title (String): The title of the submission to be analized.
	Returns: 
	    bool: True indicating it is a daily discussion; False indicating it is not.
	"""
	id_to_name = {"t5_v7civ" : "Daily General Discussion", #r/
				"t5_2r9sg" : "Daily Ripple/XRP Discussion", #r/Ripple
				"t5_2ruj5" : "Daily XRP Discussion Thread", #r/xrp
				"t5_2s3qj" : "Daily Discussion", #r/Bitcoin
				"t5_2yx36": "[Daily Discussion]"} #r/LitecoinMarkets 
	if id_subreddit not in id_to_name:
		return False
	if id_to_name[id_subreddit] in title:
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
	Generator that yields range of dates from the starting date to the end date in epoch format
	Parameters: 
	    start (date): The start date
	    end (date): The end date
	Returns: 
	    int, int: the start date and end date in epoch
	"""
	n_days = (end-start).days
	for i in range(0,n_days):
		day = start+timedelta(i)
		start_epoch = int(datetime(day.year,day.month,day.day,0,0,0).timestamp())
		end_epoch = int(datetime(day.year,day.month,day.day,23,59,59).timestamp())
		yield start_epoch, end_epoch


#connect to reddit API
reddit = praw.Reddit(client_id=secret.client_id,
 					client_secret=secret.client_secret,
 					user_agent=secret.user_agent)

subreddits = ["ethtrader", "ethfinance"]#["xrp","ripple", "bitcoin", "btc", "litecoin", "litecoinmarkets", "ethtrader", "ethfinance"]

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
mydb = myclient[DATABASE_NAME]
submissions_db = mydb[SUBMISSIONS_COLLECTION]
comments_db = mydb[COMMENTS_COLLECTION]

write_log("Starting the collection of data from the start date to today")
for subreddit in subreddits:
	write_log("Collecting submissions and comments from " + subreddit + "...")
	total_submissions = 0
	total_comments = 0
	#make request to the pushshift API
	for start_date, end_date in generate_dates(date(2020,3,30), date.today()):
		params = {
					"sort": "desc", 
					"sort_type": "created_utc", 
					"subreddit": subreddit, 
					"size": 1000,
					"after": start_date, 
					"before": end_date
				}
		response = requests.get(url=URL_PUSHSHIFT,params=params)
		print(date.fromtimestamp(start_date))
		data = response.json()

		#now that we have the data of the submissions of a day, 
		#obtain the comments of each one
		total_submissions += len(data["data"])
		for sub in data["data"]:
			if submissions_db.count_documents({"_id" : sub["id"]}) == 0:
				try:
					submission = reddit.submission(id = sub["id"])
					submission_obj = {}
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
					submission_obj["daily_discussion"] = is_daily_discussion(submission.subreddit_id, submission.title)

					#save submission object
					submissions_db.insert_one(submission_obj)

					#obtain and construct comment objects
					submission.comments.replace_more(limit=None)
					list_comments = submission.comments.list()
					if len(list_comments) > 0:
						total_comments+= len(list_comments)
						comments_objects_list = []
						for comment in list_comments:
							comment_obj = {}
							comment_obj["body"] = comment.body
							comment_obj["created"] = comment.created
							comment_obj["created_utc"] = comment.created_utc
							dt_object = datetime.fromtimestamp(comment.created_utc)
							date_aux = dt_object.strftime("%d/%m/%Y")
							comment_obj["date"] = date_aux
							comment_obj["depth"] = comment.depth
							comment_obj["downs"] = comment.downs
							comment_obj["_id"] = comment.id
							comment_obj["link_id"] = comment.link_id
							comment_obj["name"] = comment.name
							comment_obj["parent_id"] = comment.parent_id
							comment_obj["subreddit_id"] = comment.subreddit_id
							comment_obj["subreddit_name_prefixed"] = comment.subreddit_name_prefixed
							comment_obj["score"] = comment.score
							comment_obj["ups"] = comment.ups

							comments_objects_list.append(comment_obj)

						#save comments object
						comments_db.insert_many(comments_objects_list)
				except NotFound:
					write_log("Unexpected error on subrredit " + subreddit + " and submission "+ sub["id"] + ": " + str(sys.exc_info()[0]))
					continue

	write_log("Done. " + str(total_submissions) + " submissions and " + str(total_comments) + " comments from " + subreddit + " where obtained.")