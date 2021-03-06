from datetime import datetime, timezone, date, timedelta
from collections import defaultdict
import time
import multiprocessing
import os
import matplotlib.pyplot as plt
import requests
import logging

import numpy as np
import pandas as pd
from scipy.stats import zscore
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_validate, cross_val_predict
from sklearn.metrics import confusion_matrix
from sklearn.metrics import plot_confusion_matrix
from sklearn.preprocessing import StandardScaler



from scripts.twitter.twitter_mongo import MongoConnectionTweets
from pymongo import MongoClient
from settings import LOGGER_NAME

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

def get_historical_data():
	client = MongoClient(os.environ.get("mongo_url"))
	db = client["analytics"]
	collection = db["time_series_1_hour"]

	# just obtain historical data from 2020
	limit_ts = datetime(2020,1,1,0,0,0,tzinfo=timezone.utc).timestamp()
	prices_data = defaultdict(dict)

	coins = ["ETH", "BTC", "LTC", "XRP"]
	for coin in coins:
		last_ts = datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc).timestamp()
		while last_ts > limit_ts:
			first_ts = True
			url = "https://min-api.cryptocompare.com/data/v2/histohour?fsym={coin}&tsym=USD&limit=2000&toTs={last_ts}&api_key={api_key}".format(
				coin = coin,
				last_ts = last_ts,
				api_key = os.environ.get("crypto_compare_api_key")
			)
			response = requests.get(url)
			hourly_data = response.json()["Data"]["Data"]
			for hourly_price in hourly_data:
				ts = hourly_price["time"] #the first object is the earliest
				open_price = hourly_price["open"]
				close_price = hourly_price["close"]
				prices_data[ts]["{}_open".format(coin.lower())] = open_price
				prices_data[ts]["{}_close".format(coin.lower())] = close_price
				if first_ts:
					last_ts = ts
					first_ts = False

			print(last_ts)

	for ts,prices in prices_data.items():
		collection.update_one({"timestamp": ts},{"$set": prices}, upsert=True)

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

	# get closing and opening price
	coins = ["ETH", "BTC", "LTC", "XRP"]
	prices = {}

	for coin in coins:
		url = "https://min-api.cryptocompare.com/data/v2/histohour?fsym={coin}&tsym=USD&limit=1&api_key={api_key}".format(
			coin = coin,
			api_key = os.environ.get("crypto_compare_api_key")
		)
		response = requests.get(url)
		hourly_price = response.json()["Data"]["Data"][1]
		ts = hourly_price["time"] #the first object is the earliest
		open_price = hourly_price["open"]
		close_price = hourly_price["close"]
		prices["{}_open".format(coin.lower())] = open_price
		prices["{}_close".format(coin.lower())] = close_price

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

	time_series_object.update(prices)
	print(time_series_object)

	# save data
	client = MongoClient(os.environ.get("mongo_url"))
	db = client["analytics"]
	collection = db["time_series_1_hour"]
	collection.update_one({"timestamp": start_timestamp}, {"$set": time_series_object}, upsert=True)
	

def get_time_series_dataframe():
	client = MongoClient(os.environ.get("mongo_url"))
	db = client["analytics"]
	collection = db["time_series_1_hour"]
	time_series = collection.find({})
	time_series = pd.DataFrame(time_series)
	return time_series

def visualize_time_series(time_series,y="n_tweets"):
	fig, ax = plt.subplots()
	time_series["datetime"] = time_series["timestamp"].apply(datetime.fromtimestamp)

	ax.plot(time_series["datetime"], time_series[y], 'ro')

def strip_unoperating_hours(dataframe, threshold=5000):
	""" removes data points in which tweets weren't collected correctly """
	logger = logging.getLogger(LOGGER_NAME)
	logger.info("Removing data points where there tweets recollection was not working")
	logger.debug("Shape of dataframe before removing data points: {}".format(dataframe.shape))
	aux = dataframe[dataframe["n_tweets"] >= threshold]
	logger.debug("Shape of dataframe after removing data points: {}".format(aux.shape))
	return aux

def filter_dataframe_range_timestamps(dataframe,from_ts, to_ts):
	logger = logging.getLogger(LOGGER_NAME)
	logger.info("Filtering dataframe by time")
	logger.debug("Shape of dataframe before filtering {}".format(dataframe.shape))
	aux = dataframe[dataframe["timestamp"] >= from_ts]
	aux = aux[aux["timestamp"] < to_ts]
	logger.debug("Shape of dataframe before filtering {}".format(aux.shape))
	return aux

def remove_outliers(dataframe):
	logger = logging.getLogger(LOGGER_NAME)
	logger.info("Removing outliers")
	logger.debug("Shape of dataframe with outliers: {}".format(dataframe.shape))
	z_scores = zscore(dataframe["n_tweets"])
	m = np.array(dataframe["n_tweets"]).argmax()
	z_scores_abs = np.abs(z_scores)
	mask = z_scores_abs <= 3
	aux = dataframe[mask]
	logger.debug("Shape of dataframe without outliers: {}".format(aux.shape))
	return aux

def get_labels(dataframe):
	""" current: check how much needs to be invested in order to gain minimum_profit.	
	If investement <= maximum_investment, tag as positive
	"""

	minimum_profit = 0.5
	eth = []
	btc = []
	ltc = []
	xrp = []

	investments = dataframe["eth_close"] - dataframe["eth_open"]
	investments.replace(0,-1, inplace=True)
	investments = dataframe["eth_close"]*minimum_profit/investments
	eth = [1 if 0 < investment <= 200 else -1 for investment in investments]

	investments = dataframe["btc_close"] - dataframe["btc_open"]
	investments.replace(0,-1, inplace=True)
	investments = dataframe["btc_close"]*minimum_profit/investments
	btc = [1 if 0 < investment <= 200 else -1 for investment in investments]

	investments = dataframe["ltc_close"] - dataframe["ltc_open"]
	investments.replace(0,-1, inplace=True)
	investments = dataframe["ltc_close"]*minimum_profit/investments
	ltc = [1 if 0 < investment <= 200  else -1 for investment in investments]

	investments = dataframe["xrp_close"] - dataframe["xrp_open"]
	investments.replace(0,-1, inplace=True)
	investments = dataframe["xrp_close"]*minimum_profit/investments
	xrp = [1 if 0 < investment <= 200 else -1 for investment in investments]
	
	return (btc,eth,xrp,ltc)

def discover():
	def undersample(time_series, label):
		logger.info("{}: Initial number of data points: {}. Count of labels {}".format(
			label, time_series.shape[0], time_series[label].value_counts()
		))
		invest_raw = time_series[time_series[label] == 1]
		no_invest_raw = time_series[time_series[label] == -1]

		# Since there are less risky loans than safe loans, find the ratio of the sizes
		# and use that percentage to undersample the safe loans.
		percentage = len(invest_raw)/float(len(no_invest_raw))
		no_invest = no_invest_raw.sample(frac=percentage)
		invest = invest_raw
		new_ts = invest.append(no_invest)

		logger.debug("{}: Percentage of profitable investment {}:".format(label,len(invest) / float(len(new_ts))))
		logger.debug("{}: Percentage of no profitable investment {}:".format(label,len(no_invest) / float(len(new_ts))))
		logger.info("{}: New number of data points: {}".format(label,new_ts.shape[0]))

		return new_ts
		
	logger = logging.getLogger(LOGGER_NAME)
	time_series_df = get_time_series_dataframe()
	min_timestamp = datetime(2020,6,23,0,0,0, tzinfo=timezone.utc).timestamp()
	max_timestamp = datetime(2020,11,25,0,0,0, tzinfo=timezone.utc).timestamp()
	time_series_df = filter_dataframe_range_timestamps(time_series_df, min_timestamp, max_timestamp)
	time_series_df.set_index("timestamp")	

	#add labels
	btc_label, eth_label, xrp_label, ltc_label = get_labels(time_series_df)

	time_series_df = time_series_df.assign(
		eth_label=eth_label, btc_label=btc_label, xrp_label=xrp_label, ltc_label=ltc_label
	)

	time_series_df = strip_unoperating_hours(time_series_df)
	time_series_df = remove_outliers(time_series_df)

	btc_time_series = undersample(time_series_df, "btc_label")
	eth_time_series = undersample(time_series_df, "eth_label")
	xrp_time_series = undersample(time_series_df, "xrp_label")
	ltc_time_series = undersample(time_series_df, "ltc_label")

	label = ["btc_label"]
	features_sets = [["n_btc"], ["reach_btc"], ["n_btc", "reach_btc"], ["n_btc", "reach_btc","btc_open"]]

	y = btc_time_series.loc[:, label].values.ravel()
	scoring = ["precision_micro", "recall_micro"]

	

	n_estimators = [int(n) for n in np.logspace(1,3)]
	fig, axes = plt.subplots(1,2)
	for features in features_sets:
		precision_scores = []
		precision_scores_std = []

		recall_scores = []
		recall_scores_std = []
		for n in n_estimators:
			estimator = RandomForestClassifier(n_estimators = n)
			# scale data
			x = btc_time_series.loc[:, features].values
			sc = StandardScaler()
			x = sc.fit_transform(x)

			scores = cross_validate(estimator=estimator, cv=5, X=x, y=y, scoring=scoring, return_train_score=True)

			precision_scores.append(np.average(scores["test_precision_micro"]))
			precision_scores_std.append(np.std(scores["test_precision_micro"]))

			recall_scores.append(np.std(scores["test_recall_micro"]))
			recall_scores_std.append(np.std(scores["test_recall_micro"]))
			print(n)

		axes[0].errorbar(n_estimators, precision_scores, precision_scores_std, linestyle="solid", label=str(features))
		axes[1].errorbar(n_estimators, recall_scores, recall_scores_std, linestyle="solid", label=str(features))
		fig.show()
		print(features)

	fig.show()

