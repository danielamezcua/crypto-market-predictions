from datetime import datetime, timezone, date
from collections import defaultdict
import matplotlib.pyplot as plt

from scripts.twitter.twitter_mongo import MongoConnectionTweets

def main():
	tweets = MongoConnectionTweets.get_documents()
	tweets_per_day = defaultdict(int)
	for tweet in tweets:
		tweet_datetime = datetime.fromtimestamp(tweet['created'], tz=timezone.utc)
		tweet_date = date(tweet_datetime.year, tweet_datetime.month, tweet_datetime.day)
		tweets_per_day[tweet_date] += 1
	
	print("yo")
	plt.plot(tweets_per_day.values())