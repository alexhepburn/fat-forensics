"""
Holds functions responsible for objects validation across FAT-Forensics.
"""
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD

import inspect
import warnings

from typing import Tuple

import numpy as np

from fatf.exceptions import IncorrectShapeError

__all__ = ['is_numerical_dtype',
           'is_numerical_array',
           'is_2d_array',
           'indices_by_type',
           'check_model_functionality']  # yapf: disable

# Boolean, (signed) byte -- Boolean, unsigned integer, (signed) integer,
# floating-point and complex-floating point.
_NUMPY_NUMERICAL_KINDS = set('?buifc')


def is_numerical_dtype(dtype: np.dtype) -> bool:
    """
    Determines whether a numpy dtype object is of numerical type.

    Checks whether the ``dtype`` is of one of the following (numerical) types:
    boolean, (signed) byte -- boolean, unsigned integer, (signed) integer,
    floating-point or complex-floating point.

    Parameters
    ----------
    dtype : numpy.dtype
        The dtype to be checked.

    Raises
    ------
    TypeError
        The input is not a numpy's dtype object.

    Returns
    -------
    is_numerical : boolean
        True if the dtype is of a numerical type, False otherwise.
    """
    if not isinstance(dtype, np.dtype):
        raise TypeError('The input should be a numpy dtype object.')

    is_numerical = dtype.kind in _NUMPY_NUMERICAL_KINDS

    return is_numerical


def is_numerical_array(array: np.ndarray) -> bool:
    """
    Determines whether a numpy array-like object has a numerical data type.

    Checks whether the ``array`` is of one of the following (numerical) types:
    boolean, (signed) byte -- boolean, unsigned integer, (signed) integer,
    floating-point or complex-floating point.

    Parameters
    ----------
    array : numpy.ndarray
        The array to be checked.

    Raises
    ------
    TypeError
        The input array is not a numpy array-like object.

    Returns
    -------
    is_numerical : boolean
        True if the array has a numerical data type, False otherwise.
    """
    if not isinstance(array, np.ndarray):
        raise TypeError('The input should be a numpy array-like.')

    is_numerical = is_numerical_dtype(array.dtype)

    return is_numerical


def is_1d_array(array: np.ndarray) -> bool:
    """
    Determines whether a numpy array-like object is 1-dimension.

    Parameters
    ----------
    array : numpy.ndarray
        The array to be checked.

    Raises
    ------
    TypeError
        The input array is not a numpy array-like object.

    Returns
    -------
    is_1d : boolean
        True if the array is 1-dimensional, False otherwise.
    """
    if not isinstance(array, np.ndarray):
        raise TypeError('The input should be a numpy array-like.')
    
    if is_structured(array):
        is_1d = False
        message = ('Structured numpy arrays cannot be 1-dimensional. Please '
                   'use a classic numpy array with a specified type.')
        warnings.warn(message,category=UserWarning)
    else:
        if len(array.dtype) == 0:
            is_1d = True if len(array.shape) == 1 else False
        else:
            is_1d = True if len(array.shape) == 0 else False
    
    return is_1d


def is_2d_array(array: np.ndarray) -> bool:
    """
    Determines whether a numpy array-like object has 2 dimensions.

    Parameters
    ----------
    array : numpy.ndarray
        The array to be checked.

    Raises
    ------
    TypeError
        The input array is not a numpy array-like object.

    Returns
    -------
    is_2d : boolean
        True if the array is 2-dimensional, False otherwise.
    """
    if not isinstance(array, np.ndarray):
        raise TypeError('The input should be a numpy array-like.')

    if is_numerical_array(array):
        is_2d = len(array.shape) == 2
    else:
        if array.dtype.names:
            is_2d = len(array.shape) == 1
        else:
            is_2d = len(array.shape) == 2

    return is_2d


def is_structured(array: np.ndarray) -> bool:
    """
    Determines whether a numpy array-like object is a structured array
    i.e. contains more than one datatype

    Parameters
    ----------
    array : numpy.ndarray
        The array to be checked.

    Returns
    -------
    is_structured : boolean
        True if the array is a structured array, False otherwise
    """
    return True if len(array.dtype) !=0 else False


def indices_by_type(array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Identifies indices of columns with numerical and non-numerical values.

    Checks whether a numpy array is purely numerical or a structured array
    and returns two numpy arrays: the first-one with indices of numerical
    columns and the second-one with indices of non-numerical columns.

    Parameters
    ----------
    array : numpy.ndarray
        A numpy array to be checked (it has to be a 2-dimensional array).

    Raises
    ------
    TypeError
        The input array is not a numpy array-like object.
    IncorrectShapeError
        The input array is not 2-dimensional.

    Returns
    -------
    numerical_indices : numpy.ndarray
        A numpy array containing indices of the numerical columns of the input
        array.
    non_numerical_indices : numpy.ndarray
        A numpy array containing indices of the non-numerical columns of the
        input array.
    """
    if not isinstance(array, np.ndarray):
        raise TypeError('The input should be a numpy array-like.')

    if not is_2d_array(array):
        raise IncorrectShapeError('The input array should be 2-dimensional.')
    if not is_structured(array):
        if is_numerical_array(array):
            numerical_indices = np.array(range(array.shape[1]))
            non_numerical_indices = np.empty((0,), dtype='i8')
        else:
            numerical_indices = np.empty((0,), dtype='i8')
            non_numerical_indices = np.array(range(array.shape[1]))
    else:
        if array.dtype.names:
            numerical_indices_list = []
            non_numerical_indices_list = []

            for column_name in array.dtype.names:
                column_dtype = array.dtype[column_name]
                if is_numerical_dtype(column_dtype):
                    numerical_indices_list.append(column_name)
                else:
                    non_numerical_indices_list.append(column_name)

            numerical_indices = np.array(numerical_indices_list)
            non_numerical_indices = np.array(non_numerical_indices_list)
        else:
            # If it's not numerical and it's of a single type, all the columns
            # are non-numerical.
            numerical_indices = np.empty((0, ))
            non_numerical_indices = np.array(range(array.shape[1]))

    return numerical_indices, non_numerical_indices


def check_indices(array: np.ndarray,
                  indices: np.ndarray) -> np.ndarray:
    """Check if indices are valid and return a list of indices that are not found
    in the array

    Args
    ----
    array : np.ndarray
        The array to be checked
    indices : np.ndarray
        1-D array of indices corresponding to features in array
    
    Returns
    ----
    invalid_indices : np.ndarray
        Array of indices that are not found in array
    """
    if not is_1d_array(indices):
        invalid_ind = indices
    else:
        numerical_indices, categorical_indices = indices_by_type(array)
        valid_indices = np.hstack([numerical_indices, categorical_indices])
        #TODO: np.in1d raises internal numpy FutureWarning, not sure how to get around it
        invalid_ind = indices[~np.in1d(indices, valid_indices)]
    return invalid_ind

def check_valid_indices(array: np.array, 
                        indices: np.array) -> bool:
    """Check whether indices given in indices are valid indices for
    array.

    Args
    ----
    array : np.array
        The array to be checked.
    categorical_indices : np.array
        1-D array of indices corresponding to features in array

    Returns
    ----
    is_valid : bool
        A Boolean variable that indicates whether the entries of indices
        are valid indices in array 
    """
    is_valid = True
    invalid_indices = check_indices(array, indices)
    if not np.array_equal(invalid_indices, np.array([], dtype=indices.dtype)):
        is_valid = False
    return is_valid

def check_model_functionality(model_object: object,
                              require_probabilities: bool = False,
                              suppress_warning: bool = False) -> bool:
    """
    Checks whether a model object has all the required functionality.

    Examines a ``model_object`` and ensures that it has all the required
    methods with the correct number of parameters (excluding ``self``):
    ``__init__`` (at least 0), ``fit`` (at least 2), ``predict`` (at least 1)
    and, if required (``require_probabilities=True``), ``predict_proba`` (at
    least 1).

    Parameters
    ----------
    model_object : object
        A Python object that represents a predictive model.
    require_probabilities : boolean, optional (default=False)
        A boolean parameter that indicates whether the model object should
        contain a ``predict_proba`` method. Defaults to False.
    suppress_warning : boolean, optional (default=False)
        A boolean parameter that indicates whether the function should suppress
        its warning message. Defaults to False.

    Warns
    -----
    UserWarning
        Warns about the required functionality that the model object lacks.

    Returns
    -------
    is_functional : boolean
        A Boolean variable that indicates whether the model object has all the
        desired functionality.
    """
    is_functional = True

    methods = {'fit': 2, 'predict': 1}
    if require_probabilities:
        methods['predict_proba'] = 1

    message_strings = []
    for method in methods:
        if not hasattr(model_object, method):
            is_functional = False
            message_strings.append(
                'The model class is missing \'{}\' method.'.format(method))
        else:
            method_object = getattr(model_object, method)
            required_param_n = 0
            params = inspect.signature(method_object).parameters
            for param in params:
                if params[param].default is params[param].empty:
                    required_param_n += 1
            if required_param_n != methods[method]:
                is_functional = False
                message_strings.append(
                    ('The \'{}\' method of the class has incorrect number '
                     '({}) of the required parameters. It needs to have '
                     'exactly {} required parameters. Try using optional '
                     'parameters if you require more functionality.').format(
                         method, required_param_n, methods[method]))

    if not is_functional and not suppress_warning:
        message = '\n'.join(message_strings)
        warnings.warn(message, category=UserWarning)

    return is_functional
