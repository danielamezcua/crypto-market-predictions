#!/bin/zsh -l
say -v Jorge Empezando
PATH="/Users/daniel2/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.6/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/daniel2/commands:/Applications/Racket v7.0/bin:/usr/local/share/dotnet:/opt/X11/bin:~/.dotnet/tools:/Library/Frameworks/Mono.framework/Versions/Current/Commands:/Applications/Wireshark.app/Contents/MacOS"

now="$(date)"
echo "Fetching data form Reddit... @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt
python3 /Users/daniel2/Desktop/ISC/crypto-market-predictions/scripts/reddit/collect.py
now="$(date)"
echo "Done collecting data from Reddit @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt

echo "Crawling Coin Telegraph... @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt
cd /Users/daniel2/Desktop/ISC/crypto-market-predictions/scripts/crawlers
scrapy crawl coin_telegraph
now="$(date)"
echo "Done collecting data from Coin Telegraph @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt

say -v Jorge AAAAAAAAAAAAAAAcabé                 
