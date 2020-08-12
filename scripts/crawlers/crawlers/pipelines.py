# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem

import pymongo
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from crawlers.misc import lm_positive, lm_negative

class CrawlersPipeline(object):
    def process_item(self, item, spider):
        return item

class StatusPipeLine(object):
	def process_item(self, item, spider):
		if item.get('status') == 1:
			return item
		else:
			if item.get('status') == 0:
				raise DropItem("Couldn't fetch item because of response status: %d" % item.get('status'))
			else:
				raise DropItem("Couldn't crawl the new with id because it doesn't follow the known structure")

class DuplicatePipeLine(object):
	collection_name = "coin_telegraph_news"
	def __init__(self, mongo_uri, mongo_db):
		self.mongo_uri = mongo_uri
		self.mongo_db = mongo_db

	@classmethod
	def from_crawler(cls,crawler):
		return cls(
			mongo_uri = crawler.settings.get("MONGO_URI"),
			mongo_db = crawler.settings.get("MONGO_DATABASE", 'items')
		)

	def open_spider(self,spider):
		#connect to database
		self.client = pymongo.MongoClient(self.mongo_uri)
		self.db = self.client[self.mongo_db]
		self.coin_telegraph_collection = self.db[self.collection_name]

	def close_spider(self, spider):
		self.client.close()

	def process_item(self,item,spider):
		#check if the item was retrieved correctly
		if self.coin_telegraph_collection.count_documents({"id_new" : item.get("id_new")}) == 0:
			return item
		else:
			raise DropItem("Item with id %d already exists" % item.get('id_new'))

class ProcessItemPipeLine(object):
	def open_spider(self,spider):
		#initialize sentiment analyzer
		self.analyzer = SentimentIntensityAnalyzer()
		self.analyzer.lexicon.update(lm_positive)
		self.analyzer.lexicon.update(lm_negative)

	def process_item(self,item,spider):
		item['analysis'] = "Price Analysis" in item.get('title')
		#add column tags
		item['btc'] = "#Bitcoin News" in item.get('tags') or "#Bitcoin" in item.get('tags')
		item['ltc'] = "#Litecoin News" in item.get('tags') or "#Litecoin" in item.get('tags')
		item['eth'] = "#Ethereum News" in item.get('tags') or "#Ethereum" in item.get('tags')
		item['xrp'] = "#Ripple News" in item.get('tags') or "#Ripple" in item.get('tags')

		if not (item['btc'] or item['ltc'] or item['eth'] or item['xrp']):
			raise DropItem("Item with id %d is not related to any currency" % item.get('id_new'))
		
		#add sentiment
		if item["analysis"] == True:
			pass #TODO
		else:
			compounds = []
			for paragraph in item["content"]:
				comp = self.analyzer.polarity_scores(paragraph)["compound"]
				if comp != 0.0:
					compounds.append(comp)
			if len(compounds) != 0:
				item["sent_comp"] = sum(compounds)/len(compounds)
			else:
				item["sent_comp"] = 0
		return item

class MongoDBPipeLine(object):
	collection_name = "coin_telegraph_news"
	def __init__(self, mongo_uri, mongo_db):
		self.mongo_uri = mongo_uri
		self.mongo_db = mongo_db

	@classmethod
	def from_crawler(cls,crawler):
		return cls(
			mongo_uri = crawler.settings.get("MONGO_URI"),
			mongo_db = crawler.settings.get("MONGO_DATABASE", 'items')
		)

	def open_spider(self,spider):
		#connect to database
		self.client = pymongo.MongoClient(self.mongo_uri)
		self.db = self.client[self.mongo_db]
		self.coin_telegraph_collection = self.db[self.collection_name]

	def close_spider(self, spider):
		self.client.close()

	def process_item(self,item,spider):
		self.coin_telegraph_collection.insert_one(dict(item))
		return item
	