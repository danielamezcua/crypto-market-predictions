	#script to collect the market data
import secret
from requests import get
from datetime import datetime,date
import pymongo

DATABASE_NAME = "market_data"
PRICES_COLLECTION = "prices"
URL_CRYPTOCOMPARE_DAILY_PRICE = "https://min-api.cryptocompare.com/data/v2/histoday?&tsym=USD&limit=730&api_key="+secret.api_key_cryptocompare
CRYPTO_COINS = ['ETH', 'BTC', 'XRP', 'LTC']
MONGO_SERVICE = "mongodb://localhost:27017/"

#connect to database
myclient = pymongo.MongoClient(MONGO_SERVICE)
mydb = myclient[DATABASE_NAME]
prices_db = mydb[PRICES_COLLECTION]

prices_info = []
for coin in CRYPTO_COINS:
	url = URL_CRYPTOCOMPARE_DAILY_PRICE + "&fsym="+ coin
	response = get(url=url)
	if response.status_code == 200:
		for item in response.json()['Data']['Data']:
			#do not include the info of today
			timestamp = item['time']
			if datetime.fromtimestamp(timestamp).date() == date.today():
				continue
			new_item = {}
			new_item["timestamp"] = timestamp
			new_item["high"] = item['high']
			new_item["low"] = item['low']
			new_item["open"] = item['open']
			new_item["close"] = item['close']
			new_item["coin"] = coin
			new_item["volumefrom"] = item['volumefrom']
			new_item["volumeto"] = item['volumeto']


			prices_info.append(new_item)

prices_db.insert_many(prices_info)