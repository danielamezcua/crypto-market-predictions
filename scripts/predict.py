from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.model_selection import cross_validate
from sklearn import metrics

RANDOM_FOREST = 1
SUPPORT_VECTOR_CLASSIFIER = 2
MULTILAYER_PERCEPTRON = 3
DATASETS_PATH = "../datasets/"

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

def get_estimator(selection):
	if selection == RANDOM_FOREST:
		return RandomForestClassifier(n_estimators=100)
	elif selection == SUPPORT_VECTOR_CLASSIFIER:
		return svm.SVC()
	elif selection == MULTILAYER_PERCEPTRON:
		return MLPClassifier(hidden_layer_sizes=(10,), learning_rate="adaptive", alpha=0.002,activation = 'tanh',solver='sgd',random_state=1)

def input_estimator():
	print("Selecciona un algoritmo para desarrollar los modelos: ")
	print("1. RANDOM FOREST")
	print("2. SUPPORT VECTOR MACHINE")
	print("3. MULTILAYER PERCEPTRON")
	selected = input().strip()
	while selected.strip() != "1" and selected != "2" and selected != "3":
		print("Opción inválida. Selecciona 1, 2 ó 3")
		selected = input().strip()
	return int(selected)


cryptos = {
	"btc": "BITCOIN",
	"xrp": "RIPPLE",
	"ltc": "LITECOIN",
	"eth": "ETHEREUM"
}

estimator_names = {
	MULTILAYER_PERCEPTRON:  "mlp",
	RANDOM_FOREST: "rf",
	SUPPORT_VECTOR_CLASSIFIER: "svm"
}

scoring = ['accuracy','f1_macro','precision_macro','recall_macro']
label = "label"
sc = StandardScaler()

# with comment scores
# features_selection = [["number_comments_s"],["avg_compound_s"],["avg_compound_s","number_comments_s"],
# ["avg_pos_s"],["ratio_pos_s","ratio_neg_s"],["avg_news_compound"],["avg_news_compound", "avg_compound_s"],
# ["number_comments_s","avg_news_compound","avg_compound_s"],["avg_pos_s","avg_news_compound"],
# ["ratio_pos_s","ratio_neg_s","avg_news_compound"], ["avg_news_compound","avg_compound_s","open","close","high","low"],
# ["avg_news_compound","avg_pos_s","open","close","high","low"]]

# without comment scores
features_selection = [["number_comments_ns"],["avg_compound_ns"],["avg_compound_ns","number_comments_ns"],
["avg_pos_ns"],["ratio_pos_ns","ratio_neg_ns"],["avg_news_compound"],["avg_news_compound", "avg_compound_ns"],
["number_comments_ns","avg_news_compound","avg_compound_ns"],["avg_pos_ns","avg_news_compound"],
["ratio_pos_ns","ratio_neg_ns","avg_news_compound"], ["avg_news_compound","avg_compound_ns","open","close","high","low"],
["avg_news_compound","avg_pos_ns","open","close","high","low"], ["avg_pos_ns","avg_neg_ns","high","low","close","open"]]

selected_estimator = input_estimator()
estimator_name = estimator_names[selected_estimator]

for crypto in cryptos.keys():
	#desired filename example: eth_mlp_ns.txt
	suffix_result_filename = "_"+estimator_name+"_ns.txt"
	filename_dataset = crypto+"_news.csv"
	filename_result = crypto+suffix_result_filename

	#open result file
	f = open("../results/"+estimator_name+"/"+filename_result,"w")
	f.write("Results for " + estimator_name +  "applied filtered reddit data, news data and market data\n")
	f.write("The models are cross validated using Time Series Split\n")
	f.write(cryptos[crypto] + "\n")

	#load dataset and add extra features
	dataset = pd.read_csv(DATASETS_PATH + crypto + "_news.csv")
	print(crypto)
	print(len(dataset[dataset["label"] == 1]))
	add_extra_features(dataset)

	#for each selection of features, train and validate the model
	for features in features_selection:
		f.write("\tFEATURES: " + ','.join(feature for feature in features) + "\n")
		x = dataset.loc[:, features].values
		y = dataset.loc[:, label].values

		#scale data
		x = sc.fit_transform(x)

		#using time series split for cross validation
		tscv = TimeSeriesSplit(n_splits=5)
		
		estimator = get_estimator(selected_estimator)
		scores = cross_validate(estimator, x, y, scoring=scoring,cv=tscv,return_estimator=True)
		f.write("\t\tAccuracies through iterations: " + ",".join("%0.3f" % acc for acc in scores['test_accuracy']) + "\n")
		for met in scores.keys():
			if met != "estimator":
				f.write("\t\t" + met + ": %0.2f (+/- %0.2f)\n" % (scores[met].mean(), scores[met].std() * 2))
		f.write("\n")
	f.close()