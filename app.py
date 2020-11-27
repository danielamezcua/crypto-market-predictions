from scripts.analytics import twitter_pg
import argparse
import logging
import settings

LOGGING_FORMAT = '%(name)s @ %(asctime)-15s %(message)s'
LOGGING_FILE = './logs.log'

""" this file is the entry point for all the functions this package provides """
def main():
	""" maps command input to package actions """
	parser = argparse.ArgumentParser(description="Cryptocurrency market price movement predictions.")
	parser.add_argument('--time_series',action="store_true", help='construct time series object of the last hour')
	
	args = parser.parse_args()

	if args.time_series:
		store_time_series_data()
	else:
		# modify when running other custom operatiosdasns
		twitter_pg.discover()

def store_time_series_data():
	""" summarizes twitter data from the last hour """
	twitter_pg.time_series_last_hour()

if __name__ == "__main__":
	logging.basicConfig(filename=LOGGING_FILE,format=LOGGING_FORMAT)
	logging.getLogger(settings.LOGGER_NAME).setLevel(logging.DEBUG)
	main()