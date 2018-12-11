"""
Functions for calculating feature importance and 
Individual Conditional Expectation (ICE)
"""

# Author: Alex Hepburn <ah13558@bristol.ac.uk>
# License: BSD Clause 3

from typing import List, Dict, Union, Tuple
import logging

import numpy as np
import scipy

from fatf.utils.validation import (is_2d_array, 
                                   check_model_functionality,
                                   check_indices,
                                   is_numerical_array)
from fatf.exceptions import (MissingImplementationException, CustomValueError,
                            IncompatibleModelException, IncorrectShapeException)

try:
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
except ImportError as e:
    plt = None
    logging.warning(
        'Matplotlib is not installed. You will not be able to use plot_ICE function. To use' 
        'please install matplotlib by: pip install matplotlib')

def _check_input(
    X: np.ndarray, 
    model: object, 
    feature: Union[int, str],
    is_categorical: bool = False,
    check_x: bool = True,
    check_model: bool = True,
    check_feature: bool = True
) -> None:
    if check_x:
        if not is_2d_array(X):
            raise IncorrectShapeException('X must be 2-D array.')
    if check_model:
        if not check_model_functionality(model, require_probabilities=True):
            raise IncompatibleModelException(
                'partial dependence and individal conditional expectiations requires '
                'model object to have method predict_proba().')
    if check_feature:
        print(feature)
        f = np.array([feature], dtype=type(feature))
        invalid_indices = check_indices(X, f)
        if not np.array_equal(invalid_indices, np.array([], dtype=f.dtype)):
            raise CustomValueError(
                'Invalid features %s given' %str(invalid_indices))
    

def _interpolate_array(
    X: np.ndarray,
    feature: int,
    is_categorical: bool,
    steps: int
) -> np.ndarray:
    """Generate array which has interpolated between maximum and minimum
    for feature for every datapoint taking a normal np.ndarray

    Args
    ----
    X: np.ndarray
        Data matrix of all the same dtype and indexed with ints
    feature: int
        Corresponding to column in X to interpolate for
    is_categorical: bool
        If feature is categorical (do not numerically interpolate)
    steps: int
        How many steps to sample with between feature min amd max. Defaults
        to 100.
    
    Return
    ----
    X_sampled: np.array
    """
    feat = X[:, feature]
    if is_categorical:
        values = np.unique(feat)
    else:
        values = np.linspace(min(feat), max(feat), steps)
    X_sampled = np.zeros((X.shape[0], steps, X.shape[1]), dtype=X.dtype)
    for i in range(0, X.shape[0]):
        X_sampled[i, :, :] = np.tile(X[i, :], (steps, 1))
        X_sampled[i, :, feature] = values
    return X_sampled, values

def _interpolate_structured_array(
    X: np.ndarray,
    feature: str,
    is_categorical: bool,
    steps: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate array which has interpolated between maximum and minimum
    for feature for every datapoint taking a structured np.ndarray

    Args
    ----
    X: np.ndarray
        Data matrix structured array indexed with strings
    feature: str
        Corresponding to column in X to interpolate for
    is_categorical: bool
        If feature is categorical (do not numerically interpolate)
    steps: int
        How many steps to sample with between feature min amd max. Defaults
        to 100.

    Return
    ----
    X_sampled: np.ndarray (structured array)
        Structured array with shape (n_samples, steps, n_features) with 
        the dataset repeated with different values of for each point
    values: np.ndarray
        Array of values that have been interpolated between the maximum and
        minimum for the feature specified.

    Raises
    ----

    Example
    ----
    >>>
    """
    feat = X[feature]
    if not is_numerical_array(feat) and not is_categorical:
        logging.warning('Feature %s is not numerical and not specified as '
                       'categorical. Samples will be generated by using '
                       'values contained in the dataset.')
        is_categorical = True
    if is_categorical:
        values = np.unique(feat)
    else:
        values = np.linspace(min(feat), max(feat), steps)
    samples = []
    X_sampled = np.zeros((X.shape[0], steps), dtype=X.dtype)
    for i in range(0, X.shape[0]):
        X_sampled[i] = np.repeat(X[np.newaxis, i], steps, axis=0)
        X_sampled[i][feature] = values
    return X_sampled, values


def individual_conditional_expectation(
        X: np.ndarray, 
        model: object, 
        feature: Union[int, str],
        is_categorical: bool = False,
        steps: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Individual Conditional Expectation for all class for feature
    specified.

    Args
    ----
    X: np.ndarray
        Data matrix (can be structured or regular np.ndarray)
    model: object 
        Which is fitted model containing functions fit(X, Y), predict(X)
        and predict_proba(X)
    feature: int or str 
        Corresponding to column in X for feature to compute ICE
    is_categorical: bool
        If feature is categorical (do not numerically interpolate)
    steps: int 
        How many steps to sample with between feature min amd max. Defaults
        to 100. If is_categorical = True then steps is written over by the number
        of unique values in the training data for feature.

    Return
    ----
    probs: np.ndarray
        Shape [n_samples, steps, n_classes] that contains 
    values: np.ndarray
        Shape [steps] specifying the interpolation values that have been tested

    Raises
    ----
    #TODO: exceptions

    Example
    ----
    >>>
    """
    _check_input(X, model, feature, is_categorical)
    n_classes = model.predict_proba(X[0:1]).shape[1]
    is_structured = True if len(X.dtype) != 0 else False
    if is_structured:
        if is_categorical:
            steps = np.unique(X[feature]).shape[0]
        X_sampled, values = _interpolate_structured_array(X, feature, is_categorical, steps)

    else:
        if is_categorical:
            steps = np.unique(X[:, feature]).shape[0]
        X_sampled, values = _interpolate_array(X, feature, is_categorical, steps)
    probs = np.zeros((X.shape[0], steps, n_classes), dtype=np.float)
    for i in range(0, X.shape[0]):
        X_pred = X_sampled[i]
        probas = model.predict_proba(X_pred)
        probs[i, :, :] = probas
    return probs, values

def partial_dependence(
        X: np.ndarray,
        model: object,
        feature: int,
        is_categorical: bool = False,
        steps: int = 100
) -> Tuple[np.ndarray, np.array]:
    """Calculate partial dependence for all classes for feature. Takes the mean of
        the output of individual_conditional_expectation function over all training
        data points.

    Args
    ----
    X: np.ndarray 
        Data matrix (can be structured or regular np.ndarray)
    model: object 
        Which is fitted model containing functions fit(X, Y), predict(X)
        and predict_proba(X)
    feature: int or str 
        Corresponding to column in X for feature to compute ICE
    is_categorical: bool
        If feature is categorical (do not numerically interpolate)
    steps: int 
        How many steps to sample with between feature min amd max. Defaults
        to 100.

    Return
    ----
    probs: np.ndarray
        Shape [steps, n_classes] that contains 
    values: np.ndarray
        Shape [steps] specifying the interpolation values that have been tested

    Raises
    ----
    #TODO: exceptions

    Example
    ----
    >>>
    """
    ice, values = individual_conditional_expectation(X, 
                                                     model, 
                                                     feature, 
                                                     is_categorical=is_categorical,
                                                     steps=steps)
    pd = np.mean(ice, axis=0)
    return pd, values

def plot_ICE(ice: np.ndarray,
             feature_name: str,
             values: np.ndarray,
             category: int,
             category_name: str = '') -> plt.Figure:
    # TODO: return plt.figure but if matplotlib not installed it will fail
    """Plot individual conditional expectations for class

    Args
    ----
    ice: np.ndarray 
        Shape [n_samples, steps, n_classes] containing probabilities
        outputted from ICE
    feature_name: str 
        Specificy which feature was used to calculate the ICE
    values: np.array 
        Containing values of feature tested for ICE
    category: int 
        Which class to plot probabilities for
    category_name: str 
        Name of class chosen. If None then the category_name will be 
        the category integer converted to str. Default: None
    
    Returns
    ----
    ax: plt.Figure
        Figure with individual conditional expectation and partial dependence line
        plotted
    """
    if plt is None:
        raise ImportError('plot_ICE function requires matplotlib package. This can' 
                          'be installed with "pip install matplotlib"')
    if not category_name:
        category_name = str(category)
    ax = plt.subplot(111)
    lines = np.zeros((ice.shape[0], ice.shape[1], 2))
    lines[:, :, 1] = ice[:, :, category]
    lines[:, :, 0] = np.tile(values, (ice.shape[0], 1))
    collect = LineCollection(lines, label='Individual Points', color='black')
    ax.add_collection(collect)
    mean = np.mean(ice[:, :, category], axis=0)
    ax.plot(values, mean, color='yellow', linewidth=10, alpha=0.6, label='Mean')
    ax.legend()
    ax.set_ylabel('Probability of belonging to class %s'%category_name)
    ax.set_xlabel(feature_name)
    ax.set_title('Individual Conditional Expecatation')
    return ax
