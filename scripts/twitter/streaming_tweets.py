from TwitterAPI import TwitterAPI, TwitterRequestError, TwitterConnectionError
from twitter_mongo import MongoConnectionTweets
from datetime import datetime
import re
import sys,os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

api = TwitterAPI(
    os.environ.get('twitter_api_key'), 
    os.environ.get('twitter_api_secret'), 
    os.environ.get('twitter_access_token_key'), 
    os.environ.get('twitter_access_token_secret'),
)

TRACK_TERMS = 'btc,xrp,ltc,eth,#btc,#ltc,#xrp,#eth,ethereum,bitcoin,ripple,litecoin,#bitcoin,#litecoin,#ethereum,#ripple'
"Tue Jun 23 00:17:53 +0000 2020"
DATE_FORMAT_TWEETS = "%a %b %d %H:%M:%S %z %Y"

def parse_retweet(item):
    tweet = {}
    tweet["_id"] = item["id"]
    if 'extended_tweet' not in item["retweeted_status"]:
        tweet["content"] = item["retweeted_status"]["text"]
    else:
        tweet["content"] = item["retweeted_status"]["extended_tweet"]["full_text"]

    dt = datetime.strptime(item["created_at"], DATE_FORMAT_TWEETS).timestamp()
    tweet["created"] = dt

    tweet["user"] = item["user"]["id"]
    tweet["followers_user"] = item["user"]["followers_count"]
    tweet["location"] = item["user"]["location"]
    tweet["retweeted"] = True
    tweet["lang"] = item["lang"]

    tweet["retweet_id"] = item["retweeted_status"]["id"]

    #look if id of the original tweets is already in the database
    query = {"_id": tweet["retweet_id"]}
    n = MongoConnectionTweets.count_documents(query) 
    if n == 0:
        #if not, add the retweeted tweet to the database
        process_item(item["retweeted_status"])
    return tweet

def parse_tweet(item):
    tweet = {}
    tweet["_id"] = item["id"]

    #check if this tweet isn't 
    if 'extended_tweet' not in item:
        tweet["content"] = item["text"]
    else:
        tweet["content"] = item["extended_tweet"]["full_text"]

    dt = datetime.strptime(item["created_at"], DATE_FORMAT_TWEETS).timestamp()
    tweet["created"] = dt

    tweet["user"] = item["user"]["id"]
    tweet["followers_user"] = item["user"]["followers_count"]
    tweet["location"] = item["user"]["location"]
    tweet["retweeted"] = False
    tweet["lang"] = item["lang"]
       
    return tweet

def insert_tweet(item):
	MongoConnectionTweets.insert_tweet(item)

def process_tweet(item):
    #add related curreny to tweet item
    item["btc"] = False
    item["xrp"] = False
    item["eth"] = False
    item["ltc"] = False

    text_tweet = item["content"]
    if re.search("bitcoin|btc",text_tweet,re.IGNORECASE):
        item["btc"] = True
    if re.search("ethereum|#eth",text_tweet,re.IGNORECASE):
        item["eth"] = True
    if re.search("litecoin|#ltc",text_tweet,re.IGNORECASE):
        item["ltc"]= True
    if re.search("ripple|#xrp",text_tweet,re.IGNORECASE):
        item["xrp"] = True

def process_item(item):
	if 'retweeted_status' in item:
	    tweet = parse_retweet(item)
	else:
	    tweet = parse_tweet(item)
	process_tweet(tweet)
	insert_tweet(tweet)

while True:
    counter = 0
    try:
        iterator = api.request('statuses/filter', {'track': TRACK_TERMS}).get_iterator()
        for item in iterator:
            if 'disconnect' in item:
                event = item['disconnect']
                if event['code'] in [2,5,6,7]:
                    # something needs to be fixed before re-connecting
                    raise Exception(event['reason'])
                else:
                    # temporary interruption, re-try request
                    break
            if 'id' in item:
                if counter == 100:
                    print(item)
                    counter = 0
                process_item(item)
            else:
                print("--------------------------- ERROR ---------------------------")
                print(item)
                print("-------------------------------------------------------------")
            counter+=1
            

    except TwitterRequestError as e:
        if e.status_code < 500:
            # something needs to be fixed before re-connecting
            raise
        else:
            # temporary interruption, re-try request
            pass
    except TwitterConnectionError:
        # temporary interruption, re-try request
        pass