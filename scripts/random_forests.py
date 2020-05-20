import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import numpy as np

dataset_btc = pd.read_csv("./datasets/eth_news.csv")
n = len(dataset_btc)
x = []
for i in range(0,n):
	if dataset_btc.iloc[i]['close'] >= dataset_btc.iloc[i]['open']:
		x.append(1)
	else:
		x.append(-1)

dataset_btc['status'] = x

dataset_btc['number_comments_ns'] = dataset_btc['neg_ns'] + dataset_btc['pos_ns'] + dataset_btc['neutral_ns']
dataset_btc['ratio_pos_ns'] = dataset_btc['pos_ns']/dataset_btc['number_comments_ns']
dataset_btc['ratio_neg_ns'] = dataset_btc['neg_ns']/dataset_btc['number_comments_ns']
dataset_btc['ratio_neu_ns'] = dataset_btc['neutral_ns']/dataset_btc['number_comments_ns']
dataset_btc['avg_compound_ns'] = (dataset_btc['comp_ns']/dataset_btc['number_comments_ns'])
dataset_btc['avg_pos_ns'] = (dataset_btc['sum_pos_ns']/dataset_btc['pos_ns']).replace((np.nan,np.inf, -np.inf), (0,0,0))
dataset_btc['avg_neg_ns'] = (dataset_btc['sum_neg_ns']/dataset_btc['neg_ns']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))

x = dataset_btc.loc[:, ["avg_news_compound", "avg_pos_ns","open","low","high", "close"]].values
y = dataset_btc.loc[:, "label"].values


print("Without comment scores")
accuracies = []
for i in range(100):
	x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
	regressor = RandomForestClassifier(n_estimators=100)
	regressor.fit(x_train, y_train)

	y_pred = regressor.predict(x_test)

	accuracies.append(accuracy_score(y_test, y_pred))

print("Accuracies mean:", np.mean(accuracies))
print("Accuracies var:", np.var(accuracies))
print("Accuracies std:", np.std(accuracies))

print("Sample")
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
regressor = RandomForestClassifier(n_estimators=100,random_state=0)
regressor.fit(x_train, y_train)
y_pred = regressor.predict(x_test)
print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))


#considering the scores. 
dataset_btc['number_comments_s'] = dataset_btc['neg_s'] + dataset_btc['pos_s'] + dataset_btc['neu_s']
dataset_btc['ratio_pos_s'] = dataset_btc['pos_s']/dataset_btc['number_comments_s']
dataset_btc['ratio_neg_s'] = dataset_btc['neg_s']/dataset_btc['number_comments_s']
dataset_btc['ratio_neu_s'] = dataset_btc['neu_s']/dataset_btc['number_comments_s']
dataset_btc['avg_compound_s'] = ((dataset_btc['comp_s']/dataset_btc['number_comments_s']))**2
dataset_btc['avg_pos_s'] = (dataset_btc['sum_pos_s']/dataset_btc['pos_s']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))
dataset_btc['avg_neg_s'] = (dataset_btc['sum_neg_s']/dataset_btc['neg_s']).replace((np.nan, np.inf, -np.inf), (0, 0, 0))

# ax = plt.gca()
# dataset_positive.plot(kind="scatter",x="number_comments_s", y="ratio_pos_s", color="blue", ax=ax)
# dataset_negative.plot(kind="scatter",x="number_comments_s", y="ratio_pos_s", color="red", ax=ax)

# plt.show()

#Features
# print(dataset_btc['avg_compound_s'])
# print("mean of the aveage compound_s", dataset_btc['avg_compound_s'].mean())
# print("Variance of the average compound_s", dataset_btc['avg_compound_s'].var())
x = dataset_btc.loc[:, ["avg_pos_s", "avg_news_compound","open","low","high", "close"]].values
y = dataset_btc.loc[:, "label"].values

print("With comment scores")
accuracies = []
for i in range(100):
	x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

	regressor = RandomForestClassifier(n_estimators=100)
	regressor.fit(x_train, y_train)

	y_pred = regressor.predict(x_test)
	accuracies.append(accuracy_score(y_test, y_pred))

print("Accuracies mean:", np.mean(accuracies))
print("Accuracies var:", np.var(accuracies))
print("Accuracies std:", np.std(accuracies))

print("Sample")
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
regressor = RandomForestClassifier(n_estimators=100,random_state=0)
regressor.fit(x_train, y_train)
y_pred = regressor.predict(x_test)
print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))