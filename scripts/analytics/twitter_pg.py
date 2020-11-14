from datetime import datetime, timezone, date, timedelta
from collections import defaultdict
import time
from scripts.twitter.twitter_mongo import MongoConnectionTweets
import multiprocessing
from pymongo import MongoClient
import os

def get_tweets_per_hour(tweets):
	""" used to initialize time series data """
	n_tweets = MongoConnectionTweets.count_documents(estimated=True)
	print("Total number of tweets {}".format(n_tweets))
	i = 0
	tweets_per_hour = defaultdict(int)
	for tweet in tweets:
		if i % 100000 == 0:
			print(i)
		tweet_datetime = datetime.fromtimestamp(tweet['created'], tz=timezone.utc)
		date_timestamp = datetime.timestamp(datetime(tweet_datetime.year, tweet_datetime.month, tweet_datetime.day, tweet_datetime.hour,0, tzinfo=timezone.utc))
		tweets_per_hour[date_timestamp] += 1
		i+=1
	return tweets_per_hour

def get_tweets_reach():
	""" add number of tweets per coin, number of people that these tweets reached to each times series object """
	client = MongoClient(os.environ.get("mongo_url"))
	db = client["analytics"]
	collection = db["time_series_1_hour"]
	time_series = collection.find({})
	start = time.time()
	for time_serie in time_series:
		n_btc = 0
		reach_btc = 0
		
		n_eth = 0
		reach_eth = 0

		n_ltc = 0
		reach_ltc = 0

		n_xrp = 0
		reach_xrp = 0

		timestamp = time_serie["timestamp"]
		query = {"created":{"$gte":timestamp, "$lt": timestamp+3599}}
		tweets = MongoConnectionTweets.get_documents(query)
		for tweet in tweets:
			if tweet["btc"]:
				n_btc += 1
				reach_btc += tweet["followers_user"]

			if tweet["eth"]:
			 	n_eth += 1
			 	reach_eth += tweet["followers_user"]

			if tweet["xrp"]:
				n_ltc += 1
				reach_ltc += tweet["followers_user"]

			if tweet["ltc"]:
				n_xrp += 1
				reach_xrp += tweet["followers_user"]

		update = {
			"n_btc" : n_btc,
			"reach_btc" : reach_btc,
			"n_eth" : n_eth,
			"reach_eth" : reach_eth,
			"n_ltc" : n_ltc,
			"reach_ltc" : reach_ltc,
			"n_xrp" : n_xrp,
			"reach_xrp" : reach_xrp
		}

		print(time_serie["_id"])
		collection.update_one({"_id": time_serie["_id"]},{"$set": update})
	end = time.time()
	print("{} seconds".format(end-start))


def dummy_function(x):
	print(x)
	dummy = defaultdict(int)
	for a in x:
		dummy[a] += 1
	return dummy


def main():
	start = time.time()
	query_options = {'projection':['created']}
	tweets = MongoConnectionTweets.get_documents(**query_options)

	chunk_a = tweets[0:100]
	chunk_b = tweets[100:200]
	print(chunk_a[0], chunk_b[0])
	n_tweets = MongoConnectionTweets.count_documents(estimated=True)
	n_cpus = multiprocessing.cpu_count()

	tweets_per_chunk = n_tweets // n_cpus

	p = multiprocessing.Pool(processes=n_cpus)


	end = time.time()

	# plt.plot(list(tweets_per_day.values()))
	# print(n_tweets)
	# print(end-start)

def create_time_series(days=1):
	start = time.time()
	""" creates a collection of time series of <days> days """
	client = MongoClient(os.environ.get("mongo_url"))
	db = client["analytics"]
	collection = db["time_series_1_hour"]
	query_options = {"projection": ["created"]}
	tweets = MongoConnectionTweets.get_documents(**query_options)
	tweets_per_hour = get_tweets_per_hour(tweets)
	objects = [{"timestamp" : key, "n_tweets": value} for key,value in tweets_per_hour.items()]
	collection.insert_many(objects)
	end = time.time()
	print("Total time: {} minutes".format((end-start)/60))


def time_series_last_hour():
	""" queries for the tweets of the last hour, builds a time series object and saves it to the database """

	# get tweets
	utc_now = datetime.utcnow()
	start_datetime = datetime(utc_now.year, utc_now.month, utc_now.day, utc_now.hour, 0, tzinfo=timezone.utc) - timedelta(hours=1)
	end_datetime = start_datetime + timedelta(minutes=59, seconds=59)

	start_timestamp = datetime.timestamp(start_datetime)
	end_timestamp = datetime.timestamp(end_datetime)

	query = {"created":
		{	
			"$gte": start_timestamp,
			"$lt": end_timestamp
		}
	}

	tweets = MongoConnectionTweets.get_documents(query=query)
	n_tweets = 0

	n_btc = 0
	reach_btc = 0
	n_eth = 0
	reach_eth = 0
	n_ltc = 0
	reach_ltc = 0
	n_xrp = 0
	reach_xrp = 0

	# make summary
	for tweet in tweets:
		#TODO: add sentiment average, etc
		for tweet in tweets:
			n_tweets += 1
			if tweet["btc"]:
				n_btc += 1
				reach_btc += tweet["followers_user"]

			if tweet["eth"]:
			 	n_eth += 1
			 	reach_eth += tweet["followers_user"]

			if tweet["xrp"]:
				n_ltc += 1
				reach_ltc += tweet["followers_user"]

			if tweet["ltc"]:
				n_xrp += 1
				reach_xrp += tweet["followers_user"]

	time_series_object = {
		"timestamp" : start_timestamp,
		"n_tweets": n_tweets,
		"n_btc" : n_btc,
		"reach_btc" : reach_btc,
		"n_eth" : n_eth,
		"reach_eth" : reach_eth,
		"n_ltc" : n_ltc,
		"reach_ltc" : reach_ltc,
		"n_xrp" : n_xrp,
		"reach_xrp" : reach_xrp
	}

	print(time_series_object)

	# save data
	client = MongoClient(os.environ.get("mongo_url"))
	db = client["analytics"]
	collection = db["time_series_1_hour"]
	collection.update_one({"timestamp": start_timestamp}, {"$set": time_series_object}, upsert=True)