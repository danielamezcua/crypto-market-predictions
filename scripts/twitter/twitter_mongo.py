import os
import threading
from pymongo import MongoClient
import pymongo

class MongoConnectionTweets():

	_lock = threading.Lock() #lock for creating _collection_instance
	_collection_instance = None
	_database_instance = None
	_mongo_service = os.environ.get('mongo_url')
	_database_tweets = "twitter_data"
	_collection_tweets = "tweets"

	@classmethod
	def get_collection(cls):
		if MongoConnectionTweets._collection_instance == None:
			with MongoConnectionTweets._lock:
				if MongoConnectionTweets._collection_instance == None:
					MongoConnectionTweets._client_instance = MongoClient(MongoConnectionTweets._mongo_service)
					MongoConnectionTweets._database_instance = MongoConnectionTweets._client_instance[MongoConnectionTweets._database_tweets]
					MongoConnectionTweets._collection_instance = MongoConnectionTweets._database_instance[MongoConnectionTweets._collection_tweets]

		return MongoConnectionTweets._collection_instance


	@classmethod
	def count_documents(cls,query=dict(), estimated=False):
		tweets = MongoConnectionTweets.get_collection()
		if estimated:
			return tweets.estimated_document_count()
		return tweets.count_documents(query)

	@classmethod
	def insert_tweet(cls, tweet):
		tweets = MongoConnectionTweets.get_collection()
		try:
			tweets.insert_one(tweet)
		except pymongo.errors.DuplicateKeyError:
			pass

	@classmethod
	def get_documents(cls,query=dict(), **query_options):
		tweets = MongoConnectionTweets.get_collection()
		return tweets.find(query, **query_options)
