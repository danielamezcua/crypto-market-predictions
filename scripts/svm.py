from sklearn import svm
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
import numpy as np

COINS = ["btc", "xrp","ltc","eth"]
def predict(coin):
	filename = "./datasets/"+coin+"_news.csv"
	dataset_btc = pd.read_csv(filename)

	sc = StandardScaler()

	n = len(dataset_btc)
	x = []
	for i in range(0,n):
		if dataset_btc.iloc[i]['close'] >= dataset_btc.iloc[i]['open']:
			x.append(1)
		else:
			x.append(-1)

	dataset_btc['status'] = x

	#add computed features
	dataset_btc['number_comments_ns'] = dataset_btc['neg_ns'] + dataset_btc['pos_ns'] + dataset_btc['neutral_ns']
	dataset_btc['ratio_pos_ns'] = dataset_btc['pos_ns']/dataset_btc['number_comments_ns']
	dataset_btc['ratio_neg_ns'] = dataset_btc['neg_ns']/dataset_btc['number_comments_ns']
	dataset_btc['ratio_neu_ns'] = dataset_btc['neutral_ns']/dataset_btc['number_comments_ns']
	dataset_btc['avg_compound_ns'] = (dataset_btc['comp_ns']/dataset_btc['number_comments_ns'])
	dataset_btc['avg_pos_ns'] = (dataset_btc['sum_pos_ns']/dataset_btc['pos_ns']).replace((np.nan,np.inf, -np.inf), (0,0,0))
	dataset_btc['avg_neg_ns'] = (dataset_btc['sum_neg_ns']/dataset_btc['neg_ns']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))

	#define the vectors that are going to be feeded to the model
	x = dataset_btc.loc[:, ["avg_news_compound"]].values
	y = dataset_btc.loc[:, "label"].values

	print("Without comment scores")
	#train one hundred models
	accuracies = []
	for i in range(100):
		x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
		x_train = sc.fit_transform(x_train)
		x_test = sc.transform(x_test)
		clf = svm.SVC()
		clf.fit(x_train, y_train)

		y_pred = clf.predict(x_test)

		accuracies.append(accuracy_score(y_test, y_pred))

	print("Accuracies mean:", np.mean(accuracies))
	print("Accuracies var:", np.var(accuracies))
	print("Accuracies std:", np.std(accuracies))

	#train a model and output it's score
	print("Sample")
	x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
	x_train = sc.fit_transform(x_train)
	x_test = sc.transform(x_test)
	clf = svm.SVC()
	clf.fit(x_train, y_train)
	y_pred = clf.predict(x_test)
	print(confusion_matrix(y_test,y_pred))
	print(classification_report(y_test,y_pred))
	print(accuracy_score(y_test, y_pred))


	print("With comment scores")

	#add computed features
	dataset_btc['number_comments_s'] = dataset_btc['neg_s'] + dataset_btc['pos_s'] + dataset_btc['neu_s']
	dataset_btc['ratio_pos_s'] = dataset_btc['pos_s']/dataset_btc['number_comments_s']
	dataset_btc['ratio_neg_s'] = dataset_btc['neg_s']/dataset_btc['number_comments_s']
	dataset_btc['ratio_neu_s'] = dataset_btc['neu_s']/dataset_btc['number_comments_s']
	dataset_btc['avg_compound_s'] = ((dataset_btc['comp_s']/dataset_btc['number_comments_s']))**2
	dataset_btc['avg_pos_s'] = (dataset_btc['sum_pos_s']/dataset_btc['pos_s']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))
	dataset_btc['avg_neg_s'] = (dataset_btc['sum_neg_s']/dataset_btc['neg_s']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))

	#define features to be used in the training
	x = dataset_btc.loc[:, ["avg_news_compound"]].values
	y = dataset_btc.loc[:, "label"].values

	#train 100 models
	accuracies = []
	for i in range(100):
		x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
		x_train = sc.fit_transform(x_train)
		x_test = sc.transform(x_test)

		clf = svm.SVC()
		clf.fit(x_train, y_train)

		y_pred = clf.predict(x_test)
		accuracies.append(accuracy_score(y_test, y_pred))

	print("Accuracies mean:", np.mean(accuracies))
	print("Accuracies var:", np.var(accuracies))
	print("Accuracies std:", np.std(accuracies))

	#for one model, output its score
	print("Sample")
	x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
	x_train = sc.fit_transform(x_train)
	x_test = sc.transform(x_test)
	clf = svm.SVC()
	clf.fit(x_train, y_train)
	y_pred = clf.predict(x_test)
	print(confusion_matrix(y_test,y_pred))
	print(classification_report(y_test,y_pred))
	print(accuracy_score(y_test, y_pred))

for coin in COINS:
	print("---------------------------------"+coin+"---------------------------------")
	predict(coin)