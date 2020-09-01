#LEFT FILE FOR LOGGING REFERENCE
#LEFT FILE FOR LOGGING REFERENCE
#LEFT FILE FOR LOGGING REFERENCE
#LEFT FILE FOR LOGGING REFERENCE
#LEFT FILE FOR LOGGING REFERENCE


import sys,os

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import secret
import logging
logging.basicConfig(filename='./logs.txt', level=logging.INFO, format='%(name)s@%(asctime)s - %(message)s')

def get_sentiment(text):
	""" 
	Sentiment analysis on a text.
	This analysis is performed using the VADER tool.
	Parameters: 
	   text (string) :	text to be analysed
	Returns: 
	   vs (dictionary) : polarity scores calculated in the analysis
	"""
	return analyzer.polarity_scores(text)

def add_missing_posts(id_posts):
	logging.info("Collecting missing posts")
	
	logging.info("Done. " + str(total_submissions) + " submissions and " + str(total_comments) + " comments where obtained from missing posts")
