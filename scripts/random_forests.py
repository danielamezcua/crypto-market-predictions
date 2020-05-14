import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

dataset = pd.read_csv("./datasets/ETH.csv")
print("--------------------------Ethereum--------------------------")
print("Using the ratio of negative and positive comments:")

n = len(dataset)
x = []
for i in range(0,n):
	if dataset.iloc[i]['close'] >= dataset.iloc[i]['open']:
		x.append(1)
	else:
		x.append(-1)

dataset['status'] = x

#streak
x = []
st = 0

#without considering the scores (17,18,19,20,21)
dataset['number_comments_ns'] = dataset['neg_ns'] + dataset['pos_ns'] + dataset['neutral_ns']
dataset['ratio_pos_ns'] = dataset['pos_ns']/dataset['number_comments_ns']
dataset['ratio_neg_ns'] = dataset['neg_ns']/dataset['number_comments_ns']
dataset['ratio_neu_ns'] = dataset['neutral_ns']/dataset['number_comments_ns']
dataset['avg_compound_ns'] = dataset['comp_ns']/dataset['number_comments_ns']
dataset['ratio_comsub_ns'] = dataset['number_comments_ns']/dataset['submissions']
dataset['sq_avg_compound_ns'] = dataset['avg_compound_ns']**2

# print("Mean avg compound", dataset['avg_compound_ns'].mean())
# print("Variance avg compound", dataset['avg_compound_ns'].var())
# print("Std avg compound", dataset['avg_compound_ns'].std())
# dataset_positive = dataset[dataset['label'] == 1]
# dataset_negative = dataset[dataset['label'] == -1]
# len_pos = len(dataset_positive)
# len_neg = len(dataset_negative)
# print("1: ", len_pos)
# print("-1: ", len_neg)

x = dataset.loc[:, ["status", "sq_avg_compound_ns"]].values
y = dataset.loc[:, "label"].values

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
regressor = RandomForestClassifier(n_estimators=100, random_state=0)
regressor.fit(x_train, y_train)

y_pred = regressor.predict(x_test)


print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))

#considering the scores. 22,23,24,25,26,27

print("Using the score of the comments")
dataset['number_comments_s'] = dataset['neg_s'] + dataset['pos_s'] + dataset['neu_s']
dataset['ratio_pos_s'] = dataset['pos_s']/dataset['number_comments_s']
dataset['ratio_neg_s'] = dataset['neg_s']/dataset['number_comments_s']
dataset['ratio_neu_s'] = dataset['neu_s']/dataset['number_comments_s']
dataset['avg_compound_s'] = ((dataset['comp_s']/dataset['number_comments_s']))
dataset['ratio_comsub_s'] = dataset['number_comments_s']/dataset['submissions']
dataset['sq_avg_compound_s'] = dataset['avg_compound_s']**2


# print("Mean avg compound", dataset['avg_compound_s'].mean())
# print("Variance avg compound", dataset['avg_compound_s'].var())
# print("Std avg compound", dataset['avg_compound_s'].std())

# ax = plt.gca()
# dataset_positive.plot(kind="scatter",x="number_comments_s", y="ratio_pos_s", color="blue", ax=ax)
# dataset_negative.plot(kind="scatter",x="number_comments_s", y="ratio_pos_s", color="red", ax=ax)
# plt.show()

x = dataset.loc[:, ["status", "sq_avg_compound_s"]].values
y = dataset.loc[:, "label"].values

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

regressor = RandomForestClassifier(n_estimators=100, random_state=10)
regressor.fit(x_train, y_train)

y_pred = regressor.predict(x_test)

print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))