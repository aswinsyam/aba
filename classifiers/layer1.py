#!/usr/bin/env python
from __future__ import print_function
import numpy as np
from os import path
from classifier_functions import *


def process_dataset(data, attacks, outputs):
    '''Process a dataset

        Parameters
        ----------
        - data             tuple with data input and data labels
        - attacks          dictionary that maps attack names to their index
        - outputs          list of output encodings, maps each index to a discrete binary output
    '''
    x_in, y_in = data
    y_in_encoded = []
    for i, label in enumerate(y_in):
        if label == "BENIGN": y_in[i] = "dos" # FIXME testing benign, we need to assign a known label
        if label in ("ftpbruteforce", "sshbruteforce", "telnetbruteforce"): y_in[i] = "bruteforce"
        if "dos" in label: y_in[i] = "dos"
        y_in_encoded.append(outputs[attacks[y_in[i]]]) # choose result based on label
    x_in = np.array(x_in, dtype='float64')
    y_in_encoded = np.array(y_in_encoded, dtype='float64')
    return x_in, y_in_encoded


def classify(train_data, test_data, train_filename, config, disable_load=False, verbose=False):
    '''Create or load train model from given dataset and apply it to the test dataset

        If there is already a created model with the same classifier and train dataset
            it will be loaded, otherwise a new one is created and saved

        Parameters
        ----------
        - train_data          tuple with data input and data labels
        - test_data           tuple with data input and data labels
        - train_filename      filename of the train dataset
        - config              ConfigParser object to get layer settings
        - disable_load        list of output encodings, maps each index to a discrete binary output
    '''

# get options
    attack_keys = config.options('labels-l1')
    attacks = dict(zip(attack_keys, range(len(attack_keys))))
    n_labels = len(attacks)
    outputs = [[1 if j == i else 0 for j in range(n_labels)] for i in range(n_labels)]

# generate model filename
    saved_model_file = gen_saved_model_pathname(config.get('l1', 'saved-model-path'), train_filename, config.get('l1', 'classifier'))

# train or load the network
    if path.isfile(saved_model_file) and not disable_load and not config.has_option('l1', 'force_train'):
        classifier = load_model(saved_model_file)
    else: # create a new network
        classifier = train_new_network(process_dataset(train_data, attacks, outputs), saved_model_file, 'l1',
                classifier=config.get('l1', 'classifier'),
                classifier_module=config.get('l1', 'classifier-module') if config.has_option('l1', 'classifier-module') else None,
                scaler=config.get('l1', 'scaler') if config.has_option('l1', 'scaler') else None,
                scaler_module=config.get('l1', 'scaler-module') if config.has_option('l1', 'scaler-module') else None,
                verbose=verbose)
        # save_model(saved_model_file, classifier)

# apply network to the test data
    y_test, y_predicted = predict(classifier, process_dataset(test_data, attacks, outputs), 'l1', path.dirname(saved_model_file), verbose)

    print_stats(y_predicted, y_test, n_labels, outputs, lambda i: attack_keys[i])
    return y_predicted

