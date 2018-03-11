#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import sys, argparse
from classifier_functions import save_model, load_model, print_stats
from sklearn.neural_network import MLPClassifier

# USAGE: layer2-classifier training_dataset.csv testing_dataset.csv
#        layer2-classifier neural_network2.sav testing_dataset.csv

# =====================
#   ARGUMENT PARSING
# =====================

op = argparse.ArgumentParser( description="Classify MALIGN / BENIGN flows")
op.add_argument('files', metavar='file', nargs='+', help='train and test data files, if "-l | --load" option is given then just give the test data')
op.add_argument('-l', '--load', dest='load', nargs=1, metavar='NN_FILE', help="load neural network")
args = op.parse_args()

if not args.load and len(args.files) != 2:
    op.print_usage(file=sys.stderr)
    print('train and test data must be given', file=sys.stderr)
    sys.exit(1)

# =====================
#     CONFIGURATION
# =====================

LABELS = 2
ATTACK_TYPES = ("DoS-Attack", "PortScan", "FTP-Patator", "SSH-Patator", "Bot", "Infiltration", "Heartbleed", "DoS Hulk", "DoS GoldenEye", "DoS slowloris", "DoS Slowhttptest", "DDoS")
CLASSIFICATIONS = {"BENIGN": 0, "MALIGN": 1}
OUTPUTS = [[1 if j == i else 0 for j in range(LABELS)] for i in range(LABELS)]
PARAM_GRID = [{
    'activation' : ['identity', 'logistic', 'tanh', 'relu'],
    'solver' : ['lbfgs', 'sgd', 'adam'],
    'hidden_layer_sizes': [
    (1,),(2,),(3,),(4,),(5,),(6,),(7,),(8,),(9,),(10,),(11,),(12,),(13,),(14,),(15,),(16,),(17,),(18,),(19,),(20,),(21,)]}]

# =====================
#       FUNCTIONS
# =====================

def parse_csvdataset(filename):
    x_in = []
    y_in = []
    with open(filename, 'r') as fd:
        for line in fd:
            tmp = line.strip('\n').split(',')
            x_in.append(tmp[1:-1])
            if tmp[-1] in ATTACK_TYPES: tmp[-1] = "MALIGN"
            try:
                y_in.append(OUTPUTS[CLASSIFICATIONS[tmp[-1]]]) # choose result based on label
            except IndexError:
                print("ERROR: Dataset \"%s\" contains more labels than the ones allowed, \"%s\"." % (filename, tmp[-1]), file=sys.stderr)
                sys.exit(1)
            except KeyError:
                print("ERROR: Dataset \"%s\" contains unknown label \"%s\"." % (filename, tmp[-1]), file=sys.stderr)
                sys.exit(1)
    return x_in, y_in

def train_new_network(filename):
    print('Reading Training Dataset...')
    X_train, y_train = parse_csvdataset(filename)
    label_count = [y_train.count(OUTPUTS[i]) for i in range(LABELS)]
    X_train = np.array(X_train, dtype='float64')
    y_train = np.array(y_train, dtype='float64')
    #scaler = preprocessing.StandardScaler().fit(X_train)
    #X_train = scaler.transform(X_train)    # normalize
    neural_network2 = MLPClassifier(activation='logistic', solver='adam', alpha=1e-5, hidden_layer_sizes=(64), random_state=1)
    print("Training... (" + sys.argv[1] + ")")
    neural_network2.fit(X_train, y_train)
    return label_count, neural_network2

def predict(neural_network2, filename):
    print('Reading Test Dataset...')
    X_test, y_test = parse_csvdataset(filename)
    X_test = np.array(X_test, dtype='float64')
    y_test = np.array(y_test, dtype='float64')
    #X_test = scaler.transform(X_test)      # normalize
    print("Predicting... (" + filename + ")\n")
    y_predicted = neural_network2.predict(X_test)
    return y_test, y_predicted

if __name__ == '__main__':
    if args.load:
        neural_network2 = load_model(args.load.pop())
    else:
        label_count, neural_network2 = train_new_network(args.files[0])
        save_model('neurals/neural_network2.sav', neural_network2)

    y_test, y_predicted = predict(neural_network2, args.files[-1])

    print_stats(y_predicted, y_test, LABELS, OUTPUTS,
                lambda i: CLASSIFICATIONS.keys()[i],
                None if args.load else label_count)

# train_test_split is not working as expected
    # X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size=0.25, random_state=42,stratify=y_train)

# FIND THE BEST PARAMETERS BASED ON TRAINING INPUT USING A GRID_SEARCH
    #MultilayerPerceptron = MLPClassifier()
    #print("Searching Grid")
    #clf = GridSearchCV(MultilayerPerceptron, PARAM_GRID, cv=3, scoring='accuracy')

    #print("Best parameters set found on development set:")
    #print(clf)