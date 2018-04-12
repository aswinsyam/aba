#!/usr/bin/env python
from __future__ import print_function
import numpy as np
from os import path
from classifier_functions import save_model, load_model, print_stats, gen_saved_model_pathname


def parse_csvdataset(filename, attacks, outputs):
    '''Parse a dataset

        Parameters
        ----------
        - filename         filename of the dataset
        - attacks          dictionary that maps attack names to their index
        - outputs          list of output encodings, maps each index to a discrete binary output
    '''

    x_in, y_in = [], []
    with open(filename, 'r') as fd:
        for line in fd:
            tmp = line.strip('\n').split(',')
            x_in.append(tmp[1:-1])
            if tmp[-1] not in attacks: tmp[-1] = "MALIGN" # default
            try:
                y_in.append(outputs[attacks[tmp[-1]]]) # choose result based on label
            except IndexError:
                print("ERROR: Dataset \"%s\" contains more labels than the ones allowed, \"%s\"." % (filename, tmp[-1]))
                exit()
            except KeyError:
                print("ERROR: Dataset \"%s\" contains unknown label \"%s\"." % (filename, tmp[-1]))
                exit()
    return x_in, y_in


def train_new_network(train_filename, attacks, outputs, saved_model_file, node_name, classifier, classifier_module=None, scaler=None, scaler_module=None, regressor=False, verbose=False):
    '''Train a new Neural Network model from given test dataset file

        Parameters
        ----------
        - train_filename      filename of the train dataset
        - attacks             dictionary that maps attack names to their index
        - outputs             list of output encodings, maps each index to a discrete binary output
        - saved_model_file    file path to save the model (including filename)
        - classifier          string to be evaluated as the classifier
        - classifier_module   string containing the classifier module if needed
        - scaler              string to be evaluated as the scaler
        - scaler_module       string containing the scaler module if needed
    '''

    if verbose: print('Reading Training Dataset... (' + train_filename + ')')
    X_train, y_train = parse_csvdataset(train_filename, attacks, outputs)
    X_train = np.array(X_train, dtype='float64')
    y_train = np.array(y_train, dtype='float64')

# scaler setup
    if scaler_module:
        exec('import '+ scaler_module) # import scaler module
    if scaler:
        scaler = eval(scaler).fit(X_train)
        X_train = scaler.transform(X_train) # normalize
        save_model(path.dirname(saved_model_file) + "/scalerX" + node_name,scaler)

# classifier setup
    if classifier_module:
        exec('import '+ classifier_module) # import classifier module
    model = eval(classifier)

# train and save the model
    if verbose: print("Training...")
    if regressor:
        y_train = [np.argmax(x) for x in y_train]
    try:
        model.fit(X_train, y_train)
    except ValueError as err:
        print("\n\033[1;31mERROR\033[m: Problem found when training model in L2.")
        print("This classifier might be a regressor:\n%s\nIf it is use 'regressor' option in configuration file" % model)
        print("ValueError:", err)
        exit()
    save_model(saved_model_file, model)
    return model



def predict(classifier, test_filename, attacks, outputs, node_name, scaler_path=None, verbose=False):
    '''Apply the given classifier model to a test dataset

        Parameters
        ----------
        - classifier          classifier model
        - test_filename       filename of the test dataset
        - attacks             dictionary that maps attack names to their index
        - outputs             list of output encodings, maps each index to a discrete binary output
        - scaler_path         directory path to save the scaler model
        - verbose             print actions
    '''

    if verbose: print('Reading Test Dataset...')
    X_test, y_test = parse_csvdataset(test_filename, attacks, outputs)
    X_test = np.array(X_test, dtype='float64')
    y_test = np.array(y_test, dtype='float64')

    if scaler_path and path.isfile(scaler_path + "/scalerX" + node_name):
        scaler = load_model(scaler_path + "/scalerX" + node_name)
        X_test = scaler.transform(X_test) # normalize

    if verbose: print("Predicting... (" + test_filename + ")\n")
    y_predicted = classifier.predict(X_test)
    return y_test, y_predicted



def classify(train_filename, test_filename, node_name, config, disable_load=False, verbose=False):
    '''Create or load train model from given dataset and apply it to the test dataset

        If there is already a created model with the same classifier and train dataset
            it will be loaded, otherwise a new one is created and saved

        Parameters
        ----------
        - train_filename      filename of the train dataset
        - test_filename       filename of the test dataset
        - node_name           name of this node (used to load config options)
        - config              ConfigParser object to get layer settings
        - disable_load        list of output encodings, maps each index to a discrete binary output
    '''

# set options
    attacks = dict(zip(config.options('labels-l2'), range(len(config.options('labels-l2')))))
    n_labels = len(attacks)
    outputs = [[1 if j == i else 0 for j in range(n_labels)] for i in range(n_labels)]
    use_regressor = config.has_option(node_name, 'regressor')

# generate model filename
    saved_model_file = gen_saved_model_pathname(config.get(node_name, 'saved-model-path'), train_filename, config.get(node_name, 'classifier'))

# train or load the network
    if path.isfile(saved_model_file) and not disable_load and not config.has_option(node_name, 'force_train'):
        classifier = load_model(saved_model_file)
    else: # create a new network
        classifier = train_new_network(train_filename, attacks, outputs, saved_model_file, node_name,
                classifier=config.get(node_name, 'classifier'),
                classifier_module=config.get(node_name, 'classifier-module') if config.has_option(node_name, 'classifier-module') else None,
                scaler=config.get(node_name, 'scaler') if config.has_option(node_name, 'scaler') else None,
                scaler_module=config.get(node_name, 'scaler-module') if config.has_option(node_name, 'scaler-module') else None,
                regressor=use_regressor, verbose=verbose)
        save_model(saved_model_file, classifier)

# apply network to the test data
    y_test, y_predicted = predict(classifier, test_filename, attacks, outputs, node_name, path.dirname(saved_model_file) if config.has_option(node_name, 'scaler') else None, verbose)
    if use_regressor:
        y_test = [np.argmax(x) for x in y_test]
        outputs = [np.argmax(x) for x in outputs]
    print_stats(y_predicted, y_test, n_labels, outputs, lambda i: list(attacks.keys())[i], test_filename, use_regressor=use_regressor)

    # import os
    # from sklearn.metrics import accuracy_score
    # get_class_name = lambda i: list(attacks.keys())[i]
    # y_test = [np.argmax(x) for x in y_test]
    # print('\n'+os.path.basename(test_filename))
    # print("            Type  Predicted / TOTAL")
    # y_predicted = y_predicted.tolist()
    # outputs = [np.argmax(x) for x in outputs]
    # for i in range(n_labels):
    #     predicted, total = y_predicted.count(outputs[i]), y_test.count(outputs[i])
    #     color = '' if predicted == total == 0 else '\033[1;3%dm' % (1 if predicted > total else 2)
    #     print("%s%16s     % 6d / %d\033[m" % (color, get_class_name(i), predicted, total))
    # print('    \033[1;34m->\033[m %f%% [%d/%d]' % (accuracy_score(y_test, y_predicted, normalize=True)*100, accuracy_score(y_test, y_predicted, normalize=False) , len(y_predicted)))
    return y_predicted

