#!/bin/zsh -l
now="$(date)"
echo "Executing bash shell to collect data from reddit @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt
python3 /Users/daniel2/Desktop/ISC/crypto-market-predictions/reddit/daily_collect.py
now="$(date)"
echo "Done @ $now" >> /Users/daniel2/Desktop/ISC/crypto-market-predictions/logs.txt