from scripts.analytics import twitter_pg
import argparse

""" this file is the entry point for all the functions this package provides """
def main():
	""" maps command input to package actions """
	parser = argparse.ArgumentParser(description="Cryptocurrency market price movement predictions.")
	parser.add_argument('--time_series',action="store_true", help='construct time series object of the last hour')
	
	args = parser.parse_args()

	if args.time_series:
		store_time_series_data()
	else:
		twitter_pg.create_time_series()

def store_time_series_data():
	""" summarizes twitter data from the last hour """
	twitter_pg.time_series_last_hour()

if __name__ == "__main__":
	main()

