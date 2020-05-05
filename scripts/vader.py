import pymongo
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
DATABASE_NAME = "reddit_data"
LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
mydb = myclient[DATABASE_NAME]
submissions_db = mydb[SUBMISSIONS_COLLECTION]
comments_db = mydb[COMMENTS_COLLECTION]

query_start_date = datetime(2019,9,2).replace(tzinfo=timezone.utc).timestamp()
query_end_date =datetime(2019,9,3).replace(tzinfo=timezone.utc).timestamp()
comments = comments_db.find({
	"created_utc" : {
						"$gt" : query_start_date,
						"$lt": query_end_date
					},
	"subreddit_name_prefixed": "r/btc"
})

0.46

analyzer = SentimentIntensityAnalyzer()
positives = 0
negatives = 0
neutral = 0
for comment in comments:
	com = comment["body"]
	#print(com)
	vs = analyzer.polarity_scores(com)
	#print(vs)
	if vs['compound'] == 0:
		neutral+=1
	elif vs['compound'] > 0.05:
		positives += 1
	else:
		negatives += 1
	#print(comment["body"])

print("negatives: ", negatives)
print("positives: ", positives)
print("neutral: ", neutral)