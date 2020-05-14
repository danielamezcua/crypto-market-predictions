"""this script takes data stored from the database and creates a csv file containing the following
information for each day:
	number of negative comments (without score)
	number of positive comments (without score)
	number of neutral comments (without score)
	number of negative comments (including score)
	number of positive comments (including score)
	number of neutral comments (including score)
	average compound of the comments (without score)
	average compound of the comments(including score)
	total number of comments
	opening price
	closing price
	highest price
	lowest price
	cryptocurrency involved
	date
"""

#a comment will be discarded if it's score is less than -10
#if a comment has a positive score, it will count as if the comment is posted <score> times.

import csv
import pymongo
import logging
import re
from datetime import datetime,timezone
import pandas
import numpy as np

SUBMISSIONS_COLLECTION = "submissions"
COMMENTS_COLLECTION = "comments"
PRICES_COLLECTION = "prices"
DATABASE_REDDIT_NAME = "reddit_data"
DATABASE_MARKET_NAME = "market_data"

LOG_FILE = "./logs.txt"
MONGO_SERVICE = "mongodb://localhost:27017/"

#set  logger
logging.basicConfig(filename='./logs.txt', level=logging.INFO, format='%(name)s@%(asctime)s - %(message)s')

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
reddit_db = myclient[DATABASE_REDDIT_NAME]
market_db = myclient[DATABASE_MARKET_NAME]
submissions_db = reddit_db[SUBMISSIONS_COLLECTION]
comments_db = reddit_db[COMMENTS_COLLECTION]
prices_db = market_db[PRICES_COLLECTION]


crypto_subreddits = {
	"BTC":["r\/btc","r\/bitcoin"],
	"LTC":["r\/litecoin","r\/litecoinmarkets"],
	"XRP":["r\/ripple","r\/xrp"],
	"ETH":["r\/ethtrader","r\/ethfinance"]
}

#open destination file

def write_from_db():
	query_start_date = datetime(2019,9,1).replace(tzinfo=timezone.utc).timestamp()
	query_end_date =datetime(2020,5,1).replace(tzinfo=timezone.utc).timestamp()
	file = open('dataset.csv', 'w', newline='')
	writer = csv.writer(file)
	writer.writerow(["time", "neg_ns", "pos_ns", "neutral_ns", "comp_ns","neg_s", "pos_s", "neu_s","comp_s","coin","open", "close", "high", "low"])
	#iterate every cryptocoin over every day in timespan
	for crypto in crypto_subreddits.keys():
		for start_time in range(int(query_start_date), int(query_end_date), 86400):
			negative_comments_ns = 0
			positive_comments_ns = 0
			neutral_comments_ns = 0
			sum_compound_ns = 0
			negative_comments_s = 0
			positive_comments_s = 0
			neutral_comments_s = 0
			sum_compound_s = 0

			for subreddit_regex in crypto_subreddits[crypto]:
				#query for all the comments
				regx = re.compile(subreddit_regex, re.IGNORECASE)
				comments = comments_db.find({
					"created_utc" : {
										"$gt" : start_time,
										"$lt": start_time + 86400
									},
					"subreddit_name_prefixed": regx
				})
				for comment in comments:
					compound = comment["compound"]
					sum_compound_ns += compound
					if compound >= 0.05:
						positive_comments_ns += 1
					elif compound <= -0.05:
						negative_comments_ns += 1
					else:
						neutral_comments_ns += 1

					#considering the score of the comment:
					score = comment["score"]
					if score >= -10:
						if score > 0:
							if compound >= 0.05:
								positive_comments_s += score
							elif compound <= -0.05:
								negative_comments_s += score
							else:
								neutral_comments_s += score
							sum_compound_s += compound * score

						if compound >= 0.05:
							positive_comments_s += 1
						elif compound <= -0.05:
							negative_comments_s += 1
						else:
							neutral_comments_s += 1
						sum_compound_s += compound

			#add market data
			market_data = prices_db.find_one({
				"timestamp": start_time,
				"coin": crypto
			})

			op = market_data["open"]
			close = market_data["close"]
			high = market_data["high"]
			low = market_data["low"]
			
			writer.writerow([start_time, negative_comments_ns, positive_comments_ns, neutral_comments_ns, sum_compound_ns, negative_comments_s, positive_comments_s, neutral_comments_s, sum_compound_s, crypto,op,close,high,low,number_of_submissions])
	file.close()

def add_number_of_submissions():
	df = pandas.read_csv('./datasets/dataset.csv')
	n = len(df)
	submissions = []
	for i in range(0,n):
		crypto = df.iloc[i]['coin']
		time = int(df.iloc[i]['time'])
		no_submissions = 0
		for subreddit_regex in crypto_subreddits[crypto]:
			regx = re.compile(subreddit_regex, re.IGNORECASE)
			no_submissions += submissions_db.find({
				"created_utc" : {
									"$gt" : time,
									"$lt": time + 86400
								},
				"subreddit_name_prefixed": regx
			}).count()
		submissions.append(no_submissions)
	df['submissions'] = submissions
	df.to_csv('./datasets/dataset_s.csv')

	print(df)

def add_labels():
	df = pandas.read_csv('./datasets/dataset_s.csv')
	for crypto in crypto_subreddits.keys():
		subset = df[df['coin'] == crypto]
		subset.sort_values(by=['time'], inplace=True)
		n = len(subset)
		labels = []
		for i in range(0,n-1):
			if subset.iloc[i]['close'] <= subset.iloc[i+1]['close']:
				labels.append(+1)
			else:
				labels.append(-1)
		subset = subset[:-1]
		subset['label'] = labels
		
		filename = "./datasets/" + crypto + ".csv"
		subset.to_csv(filename, index=False)


add_labels()