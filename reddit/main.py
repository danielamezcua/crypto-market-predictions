import secret
import praw
import pprint
import pymongo
from datetime import datetime

def is_daily_discussion(id_subreddit, title):
	id_to_name = {"t5_v7civ" : "Daily General Discussion", #r/
				"t5_2r9sg" : "Daily Ripple/XRP Discussion", #r/Ripple
				"t5_2ruj5" : "Daily XRP Discussion Thread", #r/xrp
				"t5_2s3qj" : "Daily Discussion", #r/Bitcoin
				"t5_2yx36": "[Daily Discussion]"} #r/LitecoinMarkets 

	if id_to_name[id_subreddit] in title:
		return True
	return False

#connect to reddit API
reddit = praw.Reddit(client_id=secret.client_id,
 					client_secret=secret.client_secret,
 					user_agent=secret.user_agent)

#connect to database
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
print(myclient.list_database_names())
mydb = myclient["reddit_data"]
submissions_db = mydb["submissions"]
comments_db = mydb["comments"]

#obtain and construct submission object
submission = reddit.submission(id="fnylpq")
submission_obj = {}
submission_obj["category"] = submission.category
submission_obj["created"] = submission.created
submission_obj["created_utc"] = submission.created_utc
dt_object = datetime.fromtimestamp(submission.created_utc)
date = dt_object.strftime("%d/%m/%Y")
submission_obj["date"] = date
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
if submission.num_comments > 0:
	comments_objects_list = []
	for comment in submission.comments.list():
		comment_obj = {}
		comment_obj["body"] = comment.body
		comment_obj["created"] = comment.created
		comment_obj["created_utc"] = comment.created_utc
		dt_object = datetime.fromtimestamp(comment.created_utc)
		date = dt_object.strftime("%d/%m/%Y")
		comment_obj["date"] = date
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
print("done!")