import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

dataset_btc = pd.read_csv("./datasets/BTC.csv")


#without considering the scores (17,18,19,20,21)
dataset_btc['number_comments_ns'] = dataset_btc['neg_ns'] + dataset_btc['pos_ns'] + dataset_btc['neutral_ns']
dataset_btc['ratio_pos_ns'] = dataset_btc['pos_ns']/dataset_btc['number_comments_ns']
dataset_btc['ratio_neg_ns'] = dataset_btc['neg_ns']/dataset_btc['number_comments_ns']
dataset_btc['ratio_neu_ns'] = dataset_btc['neutral_ns']/dataset_btc['number_comments_ns']
dataset_btc['avg_compound_ns'] = dataset_btc['comp_ns']/dataset_btc['number_comments_ns']

# #x = dataset_btc.iloc[:, 17:21].values
# print(dataset_btc["avg_compound_ns"])
# #using just the number of comments
# x = dataset_btc.iloc[:, [11,12,16,17,18,19,20]].values
# y = dataset_btc.iloc[:, 15].values

# x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=10)
# regressor = RandomForestClassifier(n_estimators=100, random_state=0)
# regressor.fit(x_train, y_train)

# y_pred = regressor.predict(x_test)


# print(confusion_matrix(y_test,y_pred))
# print(classification_report(y_test,y_pred))
# print(accuracy_score(y_test, y_pred))

#considering the scores. 22,23,24,25,26,27

dataset_positive = dataset_btc[dataset_btc['label'] == 1]
dataset_negative = dataset_btc[dataset_btc['label'] == -1]
len_pos = len(dataset_positive)
len_neg = len(dataset_negative)

print("majority classifier: %f", len_pos/(len_pos+len_neg))
print("majority classifier: %f", len_neg/(len_pos+len_neg))
dataset_btc['number_comments_s'] = dataset_btc['neg_s'] + dataset_btc['pos_s'] + dataset_btc['neu_s']
dataset_btc['ratio_pos_s'] = dataset_btc['pos_s']/dataset_btc['number_comments_s']
dataset_btc['ratio_neg_s'] = dataset_btc['neg_s']/dataset_btc['number_comments_s']
dataset_btc['ratio_neu_s'] = dataset_btc['neu_s']/dataset_btc['number_comments_s']
dataset_btc['avg_compound_s'] = ((dataset_btc['comp_s']/dataset_btc['number_comments_s']))**2
dataset_btc['sq_number_comments_s'] = dataset_btc['number_comments_s']**2


# ax = plt.gca()
# dataset_positive.plot(kind="scatter",x="number_comments_s", y="ratio_pos_s", color="blue", ax=ax)
# dataset_negative.plot(kind="scatter",x="number_comments_s", y="ratio_pos_s", color="red", ax=ax)

# plt.show()

#Features
print(dataset_btc['avg_compound_s'])
print("mean of the aveage compound_s", dataset_btc['avg_compound_s'].mean())
print("Variance of the average compound_s", dataset_btc['avg_compound_s'].std())
x = dataset_btc.iloc[:, [15, 22,26]].values
y = dataset_btc.iloc[:, 16].values

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

regressor = RandomForestClassifier(n_estimators=40, random_state=0)
regressor.fit(x_train, y_train)

y_pred = regressor.predict(x_test)

print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))