from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

import pandas as pd
import numpy as np

def add_extra_features(dataset):
	dataset['number_comments_ns'] = dataset['neg_ns'] + dataset['pos_ns'] + dataset['neutral_ns']
	dataset['ratio_pos_ns'] = dataset['pos_ns']/dataset['number_comments_ns']
	dataset['ratio_neg_ns'] = dataset['neg_ns']/dataset['number_comments_ns']
	dataset['ratio_neu_ns'] = dataset['neutral_ns']/dataset['number_comments_ns']
	dataset['avg_compound_ns'] = (dataset['comp_ns']/dataset['number_comments_ns'])
	dataset['avg_pos_ns'] = (dataset['sum_pos_ns']/dataset['pos_ns']).replace((np.nan,np.inf, -np.inf), (0,0,0))
	dataset['avg_neg_ns'] = (dataset['sum_neg_ns']/dataset['neg_ns']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))

	dataset['number_comments_s'] = dataset['neg_s'] + dataset['pos_s'] + dataset['neu_s']
	dataset['ratio_pos_s'] = dataset['pos_s']/dataset['number_comments_s']
	dataset['ratio_neg_s'] = dataset['neg_s']/dataset['number_comments_s']
	dataset['ratio_neu_s'] = dataset['neu_s']/dataset['number_comments_s']
	dataset['avg_compound_s'] = ((dataset['comp_s']/dataset['number_comments_s']))**2
	dataset['avg_pos_s'] = (dataset['sum_pos_s']/dataset['pos_s']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))
	dataset['avg_neg_s'] = (dataset['sum_neg_s']/dataset['neg_s']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))

mlp = MLPClassifier(max_iter=500)
parameter_space = {
    'hidden_layer_sizes': [(5,), (10,), (20,), (30,),(100,)],
    'activation': ['tanh', 'logistic'],
    'solver': ['sgd', 'adam'],
    'alpha': [0.0001, 0.0002,0.05],
    'learning_rate': ['constant','adaptive'],
    'alpha':[0.0001,0.0002,0.0003],
    'momentum': [0.1,0.5,0.9]
}

features_selection = [["number_comments_ns"],["avg_compound_ns"],["avg_compound_ns","number_comments_ns"],
["avg_pos_ns"],["ratio_pos_ns","ratio_neg_ns"],["avg_news_compound"],["avg_news_compound", "avg_compound_ns"],
["number_comments_ns","avg_news_compound","avg_compound_ns"],["avg_pos_ns","avg_news_compound"],
["ratio_pos_ns","ratio_neg_ns","avg_news_compound"], ["avg_news_compound","avg_compound_ns","open","close","high","low"],
["avg_news_compound","avg_pos_ns","open","close","high","low"], ["avg_pos_ns","avg_neg_ns","high","low","close","open"]]

dataset = pd.read_csv("./datasets/btc_news.csv")
add_extra_features(dataset)
label = "label"
sc = StandardScaler()
f = open("./mlp_discover.txt", "w")
for features in features_selection:
	msg = "FEATURES" + str(features) + "\n"

	f.write(msg)
	x = dataset.loc[:, features].values
	y = dataset.loc[:, label].values

	#scale data
	x = sc.fit_transform(x)

	#using time series split for cross validation
	tscv = TimeSeriesSplit(n_splits=5)
	mlp = MLPClassifier(max_iter=300)
	clf = GridSearchCV(mlp, parameter_space, n_jobs=-1, cv=3)
	clf.fit(x,y)

	# Best paramete set
	msg = 'Best parameters found:\n' + str(clf.best_params_) + "\n"
	f.write(msg)
f.close()
