import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import numpy as np
dataset = pd.read_csv("./datasets/eth_news.csv")
#dataset = dataset[dataset["n_news"] != 0]
print("--------------------------ETHEREUM--------------------------")


#add computed features to the data
n = len(dataset)
x = []
for i in range(0,n):
	if dataset.iloc[i]['close'] >= dataset.iloc[i]['open']:
		x.append(1)
	else:
		x.append(-1)

dataset['status'] = x
dataset['number_comments_ns'] = dataset['neg_ns'] + dataset['pos_ns'] + dataset['neutral_ns']
dataset['ratio_pos_ns'] = dataset['pos_ns']/dataset['number_comments_ns']
dataset['ratio_neg_ns'] = dataset['neg_ns']/dataset['number_comments_ns']
dataset['ratio_neu_ns'] = dataset['neutral_ns']/dataset['number_comments_ns']
dataset['avg_compound_ns'] = dataset['comp_ns']/dataset['number_comments_ns']
dataset['ratio_comsub_ns'] = dataset['number_comments_ns']/dataset['submissions']
dataset['sq_avg_compound_ns'] = dataset['avg_compound_ns']**2

#train model and make test it
print("Without comment scores")

x = dataset.loc[:, ["avg_news_compound","avg_compound_ns","number_comments_ns"]].values
y = dataset.loc[:, "label"].values

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
regressor = RandomForestClassifier(n_estimators=100, random_state=0)
regressor.fit(x_train, y_train)
y_pred = regressor.predict(x_test)
print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))

#Considering comment scores
print("Using the score of the comments")

#add computed features
dataset['number_comments_s'] = dataset['neg_s'] + dataset['pos_s'] + dataset['neu_s']
dataset['ratio_pos_s'] = dataset['pos_s']/dataset['number_comments_s']
dataset['ratio_neg_s'] = dataset['neg_s']/dataset['number_comments_s']
dataset['ratio_neu_s'] = dataset['neu_s']/dataset['number_comments_s']
dataset['avg_compound_s'] = ((dataset['comp_s']/dataset['number_comments_s']))
dataset['ratio_comsub_s'] = dataset['number_comments_s']/dataset['submissions']
dataset['sq_avg_compound_s'] = dataset['avg_compound_s']**2


x = dataset.loc[:, ["avg_news_compound","avg_compound_s","number_comments_s"]].values
y = dataset.loc[:, "label"].values

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

regressor = RandomForestClassifier(n_estimators=100, random_state=0)
regressor.fit(x_train, y_train)

y_pred = regressor.predict(x_test)

print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))