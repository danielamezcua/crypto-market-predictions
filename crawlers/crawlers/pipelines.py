# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
import pymongo

class CrawlersPipeline(object):
    def process_item(self, item, spider):
        return item

class MongoDBPipeline(object):
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
		if item.get('status') == 1:
			if self.coin_telegraph_collection.count_documents({"id_new" : item.get("id_new")}) == 0:
				item['analysis'] = "Price Analysis" in item.get('title')
				#add column tags
				item['btc'] = "#Bitcoin News" in item.get('tags')
				item['ltc'] = "#Litecoin News" in item.get('tags')
				item['eth'] = "#Ethereum News" in item.get('tags')
				item['xrp'] = "#Ripple News" in item.get('tags')
				self.coin_telegraph_collection.insert_one(dict(item))
				return item
			else:
				raise DropItem("Item with id %d already exists" % item.get('id_new'))
		else:
			raise DropItem("Couldn't fetch item because of response status: %d" % item.get('status'))