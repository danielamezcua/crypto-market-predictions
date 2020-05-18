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

#just subreddits with daily dicussions
crypto_subreddits = {
	"BTC":["r\/bitcoin"],
	"LTC":["r\/litecoinmarkets"],
	"XRP":["r\/ripple","r\/xrp"],
	"ETH":["r\/ethfinance"]
}

regex_daily_discussions = {
	"r\/bitcoin": "^Daily Discussion,(.*)",
	"r\/litecoinmarkets": "^\\[Daily Discussion\\](.*)",
	"r\/ripple": "^Daily Ripple/XRP Discussion Thread(.*)",
	"r\/xrp": "^Daily XRP Discussion Thread(.*)",
	"r\/ethfinance": "^Daily General Discussion -(.*)"
}

def parse_date(title,subreddit):
	if subreddit == "r\/bitcoin":
		#format: Daily Discussion, March 13, 2020
		str_time = title[18:].strip()
		parse_format = "%B %d, %Y"
	elif subreddit == "r\/litecoinmarkets":
		#format: [Daily Discussion] Wednesday, May 08, 2019
		str_time = title[18:].strip()
		parse_format = "%A, %B %d, %Y"
	elif subreddit == "r\/ripple":
		#format: Daily Ripple/XRP Discussion Thread 04/20/20 [Join Our Discord] invite link: discord.gg/7Bv2rYf
		str_time = title[35:43]
		parse_format = "%m/%d/%y"
	elif subreddit == "r\/xrp":
		#format: Daily XRP Discussion Thread 01/10/20 [Join Our Discord] invite link: discord.gg/7Bv2rYf
		str_time = title[28:36]
		parse_format = "%m/%d/%y"
	elif subreddit == "r\/ethfinance":
		#format: Daily General Discussion - February 15, 2020
		str_time = title.split('-')[1].strip()
		parse_format = "%B %d, %Y"

	return datetime.strptime(str_time,parse_format).replace(tzinfo=timezone.utc).timestamp()

def init_data(data,time,coin):
	#add market data
	market_data = prices_db.find_one({
		"timestamp": time,
		"coin": coin
	})

	op = market_data["open"]
	close = market_data["close"]
	high = market_data["high"]
	low = market_data["low"]

	data[time] = {
		"time": time,
		"neg_ns":0,
		"pos_ns":0,
		"sum_pos_ns":0,
		"sum_neg_ns":0,
		"neutral_ns":0,
		"comp_ns":0,
		"neg_s":0,
		"pos_s":0,
		"neu_s":0,
		"sum_pos_s":0,
		"sum_neg_s":0,
		"comp_s":0,
		"coin":coin,
		"open": op,
		"close": close,
		"high": high,
		"low": low
	}

def obtain_ids_discussions(subreddit, crypto):
	s = []
	regx_title = re.compile(subreddit, re.IGNORECASE)
	regx_discussion = re.compile(regex_daily_discussions[subreddit])
	results = submissions_db.find({
		"subreddit_name_prefixed": regx_title,
		"title": regx_discussion
	}).sort([("created_utc",1)])
	for result in results:
		s.append((result["title"], "t3_"+result["_id"]))
	return s

def write_from_db():
	query_start_date = datetime(2019,9,1).replace(tzinfo=timezone.utc).timestamp()
	query_end_date =datetime(2020,5,1).replace(tzinfo=timezone.utc).timestamp()
	file = open('./datasets/dataset.csv', 'w', newline='')
	field_names = ["time", "neg_ns", "pos_ns", "neutral_ns","sum_pos_ns","sum_neg_ns",
	"sum_pos_s","sum_neg_s","comp_ns","neg_s", "pos_s", "neu_s","comp_s","coin","open",
	"close", "high", "low"]
	writer = csv.DictWriter(file,field_names)
	#iterate every cryptocoin over every day in timespan
	for crypto in crypto_subreddits.keys():
		data = {}
		for subreddit in crypto_subreddits[crypto]:
			#find all daily discussions
			submissions = obtain_ids_discussions(subreddit, crypto)
			for submission in submissions:
				title = submission[0]
				id = submission[1]
				#parse the datetime of the submission's title
				time = parse_date(title, subreddit)

				#obtain the comments and add them to the data of this day
				comments = comments_db.find({
					"link_id": id
				})


				if time not in data:
					init_data(data,time,crypto)

				data_row = data[time]

				for comment in comments:
					if "compound" not in comment:
						continue
					compound = comment["compound"]
					data_row["comp_ns"] += compound
					if compound >= 0.05:
						data_row["pos_ns"] += 1
						data_row["sum_pos_ns"] += compound
					elif compound <= -0.05:
						data_row["neg_ns"] += 1
						data_row["sum_neg_ns"] += compound
					else:
						data_row["neutral_ns"] += 1

					#considering the score of the comment:
					score = comment["score"]
					if score >= -10:
						if score > 0:
							if compound >= 0.05:
								data_row["pos_s"] += score
								data_row["sum_pos_s"] += compound*score
							elif compound <= -0.05:
								data_row["neg_s"] += score
								data_row["sum_neg_s"] += compound*score
							else:
								data_row["neu_s"] += score
							data_row["comp_s"] += compound * score

						if compound >= 0.05:
							data_row["pos_s"] += 1
							data_row["sum_pos_s"] += compound
						elif compound <= -0.05:
							data_row["neg_s"] += 1
							data_row["sum_neg_ns"] += compound
						else:
							data_row["neu_s"] += 1
						data_row["comp_s"] += compound
		#write rows to csv file
		for key in data.keys():
			writer.writerow(data[key])
	file.close()

def add_labels():
	df = pandas.read_csv('./datasets/datasets.csv')
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