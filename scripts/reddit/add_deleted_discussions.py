import praw
import pymongo
import sys,os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import secret
from prawcore.exceptions import NotFound
from datetime import datetime,timedelta,date
from deleted_eth_finance import deleted_posts
SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
DATABASE_NAME = "reddit_data"
LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"

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

#connect to reddit API
reddit = praw.Reddit(client_id=secret.client_id,
 					client_secret=secret.client_secret,
 					user_agent=secret.user_agent)

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
mydb = myclient[DATABASE_NAME]
submissions_db = mydb[SUBMISSIONS_COLLECTION]
comments_db = mydb[COMMENTS_COLLECTION]

write_log("Collecting deleted posts from ethfinance")
total_submissions = 0
total_comments = 0

#now that we have the data of the submissions of a day, 
#obtain the comments of each one
deleted_posts = [x for x in deleted_posts if "#" not in x]
for id in deleted_posts:
	if submissions_db.count_documents({"_id" : id}) == 0:
		try:
			submission = reddit.submission(id = id)
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
			submission_obj["daily_discussion"] = True

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

write_log("Done. " + str(total_submissions) + " submissions and " + str(total_comments) + " where obtained from deleted posts.")
myclient.close()