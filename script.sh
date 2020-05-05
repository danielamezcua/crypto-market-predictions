#!/bin/zsh -l
now="$(date)"
echo "Executing bash shell to collect data from reddit @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt
python3 /Users/daniel2/Desktop/ISC/crypto-market-predictions/scripts/reddit/daily_collect.py
now="$(date)"
echo "Done collecting data from reddit @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt

echo "Executing bash shell to collect data from Coin Telegraph @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt
cd /Users/daniel2/Desktop/ISC/crypto-market-predictions/scripts/crawlers
scrapy crawl coin_telegraph
now="$(date)"
echo "Done collecting data from coin telegraph @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt