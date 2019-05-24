"""
Blimey implementation.
"""
# Author: Alex Hepburn <ah13558@bristol.ac.uk>
# License: new BSD

from typing import Dict, Union, Optional, List
import warnings

import numpy as np

import fatf.utils.data.augmentation as fuda
import fatf.utils.data.discretization as fudd

import fatf.utils.array.validation as fuav
import fatf.utils.models.validation as fumv
import fatf.utils.array.tools as fuat
import fatf.utils.data.similarity_binary_mask as fuds

from fatf.exceptions import IncompatibleModelError, IncorrectShapeError

__all__ = ['Blimey']

Index = Union[int, str]


def _input_is_valid(dataset: np.ndarray,
                    augmentor: fuda.Augmentation,
                    discretizer: fudd.Discretization,
                    explainer: object,
                    global_model: object,
                    local_model: object,
                    categorical_indices: Optional[List[Index]] = None,
                    class_names: Optional[List[str]] = None,
                    feature_names: Optional[List[str]] = None) -> bool:
    """
    Validates the input parameters of Blimey class.

    For the input parameter description, warnings and exceptions please see
    the documentation of the :func`fatf.transparency.models.blimey.Blimey.
    __init__` function.

    Returns
    -------
    is_input_ok : boolean
        ``True`` if input is valid, ``False`` otherwise.
    """
    is_input_ok = False

    if not fuav.is_2d_array(dataset):
        raise IncorrectShapeError('The input dataset must be a 2-dimensional '
                                  'array.')

    if not fuav.is_base_array(dataset):
        raise TypeError('The input dataset must only contain base types '
                        '(textual and numerical).')

    if not fumv.check_model_functionality(
            global_model, require_probabilities=True, suppress_warning=True):
        raise IncompatibleModelError(
            'This functionality requires the global model to be capable of '
            'outputting probabilities via predict_proba method.')

    if not fumv.check_model_functionality(
            local_model, require_probabilities=False, suppress_warning=True,
            is_instance=False):
        raise IncompatibleModelError(
            'This functionality requires the local model to be capable of '
            'outputting probabilities via predict_proba method.')

    #TODO: check explainer is valid once we have explainer abstract class

    if categorical_indices is not None:
        if isinstance(categorical_indices, list):
            invalid_indices = fuat.get_invalid_indices(
                dataset, np.asarray(categorical_indices))
            if invalid_indices.size:
                raise IndexError('The following indices are invalid for the '
                                 'input dataset: {}.'.format(invalid_indices))
        else:
            raise TypeError('The categorical_indices parameter must be a '
                            'Python list or None.')

    if not issubclass(augmentor, fuda.Augmentation):
        raise TypeError('The augmentor object must inherit from abstract '
                        'class fatf.utils.augmentation.Augmentation.')

    if not issubclass(discretizer, fudd.Discretization):
        raise TypeError('The discretizer object must inherit from abstract '
                        'class fatf.utils.discretization.Discretization.')

    if class_names is not None:
        if not isinstance(class_names, list):
            raise TypeError('The class_names parameter must be None or a '
                            'list.')
        else:
            for class_name in class_names:
                if (class_name is not None and not
                        isinstance(class_name, str)):
                    raise TypeError('The class_name has to be either None or '
                                    'a string or a list of strings.')

    if fuav.is_structured_array(dataset):
        features_number = len(dataset.dtype.names)
    else:
        features_number = dataset.shape[1]

    if feature_names is not None:
        if not isinstance(feature_names, list):
            raise TypeError('The feature_names parameter must be None or a '
                            'list.')
        else:
            if len(feature_names) != features_number:
                raise ValueError('The length of feature_names must be equal '
                                 'to the number of features in the dataset.')
            for feature in feature_names:
                if (feature is not None and not isinstance(feature, str)):
                    raise TypeError('The feature name has to be either None '
                                    'or a string or a list of strings.')

    is_input_ok = True
    return is_input_ok


class Blimey(object):
    """
    Blimey class

    Parameters
    ----------
    dataset : numpy.ndarray
        A 2-dimensional numpy array with the dataset.
    augmentor : fatf.utils.data.augmentation.Augmentation,
        An object refence which is a subclass of :class:`fatf.utils.data.
        augmentation.Augmentation` which the data will be augmented using.
    discretizer : fatf.utils.data.discretization.Discretization
        An object reference which is a subclass of :class:`fatf.utils.data.
        discretization.Discretization` which will discretize the data for use
        in the local model.
    explainer : object
        An object reference which will explain an instance by training a
        `local_model` on locally augmentated data.
    global_model : object
        A pretrained global model. This must contain method ``predict_proba``
        that will return a numpy array for probabilities of instances belonging
        to each of the classses.
    local_model : object
        An object reference used for prediction in the `explainer` object.
        Must be compatible with the chosen explainer.
    categorical_indices : List[column indices]
        A list of column indices that should be treat as categorical features.
    class_names : List[string], optional (default=None)
        A list of strings defining the names of classes.
    feature_names : List[string], optional (default=None)
        A list of strings defining the names of the features.

    Warns
    -----
    UserWarning
        If some of the string-based columns in the input data array were not
        indicated to be categorical features by the user (via the
        ``categorical_indices`` parameter) the user is warned that they will be
        added to the list of categorical features.

    Raises
    ------
    IncorrectShapeError
        The parameter ``dataset`` is not a 2-dimensional numpy array.
    TypeError
        The parameter ``dataset`` is not of base (numerical and/or string)
        type. The ``categorical_indices`` parameter is neither a list nor
        ``None``. The parameter ``augmentor`` is not a subclass of
        :class:`fatf.utils.data.augmentation.Augmentation`. The parameter
        ``discretizer`` is not a subclass of
        :class:`fatf.utils.data.discretization.Discretization`. The
        ``feature_names`` parameter is neither a list nor ``None``. One of the
        values in ``feature_names`` is neither a string nor ``None``. The
        ``class_names`` parameter is neither a list nor ``None``. One of the
        values in ``class_names`` is neither a string nor ``None``.
    IndexError
        Some of the column indices given in the ``categorical_indices``
        parameter are not valid for the input ``dataset``.
    IncompatibleModelError
        The parameter ``global_model`` does not have required functionality
        -- it needs to be able to output probabilities via ``predict_proba``
        method. The parameter ``local_model`` does not have required
        functionality -- it needs to be able to output predictions via
        ``predict``.
    ValueError
        The length of parameter ``feature_names`` is not the same as the number
        of features in ``dataset``.

    Attributes
    ----------
    dataset : numpy.ndarray
        A 2-dimensional numpy array with the dataset.
    is_structured : boolean
        ``True`` if the ``dataset`` is a structured numpy array, ``False``
        otherwise.
    discretized_dataset : numpy.ndarray
        A 2-dimensional numpy array with the discretized dataset.
    augmentor : fatf.utils.data.augmentation.Augmentation,
        An object refence which is a subclass of :class:`fatf.utils.data.
        augmentation.Augmentation` which the data will be augmented using.
    discretizer : fatf.utils.data.discretization.Discretization
        An object reference which is a subclass of :class:`fatf.utils.data.
        discretization.Discretization` which will discretize the data for use
        in the local model.
    explainer : object
        An object reference which will explain an instance by training a
        `local_model` on locally augmentated data.
    global_model : object
        A pretrained global model. This must contain method ``predict_proba``
        that will return a numpy array for probabilities of instances belonging
        to each of the classses.
    local_model : object
        An object reference used for prediction in the `explainer` object.
        Must be compatible with the chosen explainer.
    categorical_indices : List[column indices]
        A list of column indices that should be treat as categorical features.
    class_names : List[string]
        A list of strings defining the names of classes.
    feature_names : List[string]
        A list of strings defining the names of the features.
    n_classes : integer
        Number of classes that ``global_model`` produces prediction
        probabilities for.
    indices : List[column indices]
        A list of all indices in ``dataset``.
    """
    def __init__(self,
                 dataset: np.ndarray,
                 augmentor: fuda.Augmentation,
                 discretizer: fudd.Discretization,
                 explainer: object,
                 global_model: object,
                 local_model: object,
                 categorical_indices: Optional[List[Index]] = None,
                 class_names: Optional[List[str]] = None,
                 feature_names: Optional[List[str]] = None,
                 **kwargs):
        """
        Constructs an ``Blimey`` class.
        """
        assert _input_is_valid(dataset, augmentor, discretizer, explainer,
                               global_model, local_model, categorical_indices,
                               class_names, feature_names), \
                               'Input is not valid.'

        self.kwargs = kwargs
        self.dataset = dataset
        self.is_structured = fuav.is_structured_array(dataset)

        # Sort out column indices
        indices = fuat.indices_by_type(dataset)
        cat_indices = set(indices[1])

        if categorical_indices is None:
            self.categorical_indices = list(cat_indices)
        else:
            if cat_indices.difference(categorical_indices):
                msg = ('Some of the string-based columns in the input dataset '
                       'were not selected as categorical features via the '
                       'categorical_indices parameter. String-based columns '
                       'cannot be treated as numerical features, therefore '
                       'they will be also treated as categorical features '
                       '(in addition to the ones selected with the '
                       'categorical_indices parameter).')
                warnings.warn(msg, UserWarning)
            self.categorical_indices = list(cat_indices.union(
                categorical_indices))

        # Initialise objects
        self.global_model = global_model
        self.augmentor = augmentor(
            dataset, categorical_indices=self.categorical_indices, **kwargs)
        self.discretizer = discretizer(
            dataset, categorical_indices=self.categorical_indices,
            feature_names=feature_names, **kwargs)
        self.discretized_dataset = self.discretizer.discretize(self.dataset)
        self.explainer_class = explainer
        self.n_classes = self.global_model.predict_proba(
            dataset).shape[1]
        self.local_model = local_model

        if fuav.is_structured_array(self.dataset):
            self.indices = self.dataset.dtype.names
        else:
            self.indices = np.arange(0, self.dataset.shape[1], 1)

        # pre-process class_names and feature_names
        if feature_names is None:
            feature_names = [None] * self.dataset.shape[1]
        self.feature_names = []
        for i, feature_name in enumerate(feature_names):
            if feature_name is None:
                self.feature_names.append('feature {}'.format(i))
            else:
                self.feature_names.append(feature_name)

        if class_names is None:
            class_names = [None] * self.n_classes
        self.class_names = []
        for i, class_name in enumerate(class_names):
            if class_name is None:
                self.class_names.append('class {}'.format(i))
            else:
                self.class_names.append(class_name)

    def _explain_instance_is_input_valid(self,
                                         data_row: np.ndarray,
                                         samples_number: Optional[int] = 100
                                         ) -> bool:
        """
        Validates input parameters for ``explain_insatnce``.

        For the input parameter description, warnings and exceptions please see
        the documentation of the :func`fatf.transparency.models.blimey.Blimey.
        explain_instance` function.

        Returns
        -------
        is_input_ok : boolean
            ``True`` if input is valid, ``False`` otherwise.

        """
        input_is_ok = False

        if not fuav.is_1d_array(data_row):
            raise IncorrectShapeError('data_row must be a 1-dimensional array')
        are_similar = fuav.are_similar_dtype_arrays(
            self.dataset, np.array(data_row), strict_comparison=True)
        if not are_similar:
            raise TypeError('The dtype of the data is different to '
                            'the dtype of the data array used to '
                            'initialise this class.')
        if not self.is_structured:
            if data_row.shape[0] != self.dataset.shape[1]:
                raise IncorrectShapeError(
                    'The data must contain the same number of features as '
                    'the dataset used to initialise this class.')

        if isinstance(samples_number, int):
            if samples_number < 1:
                raise ValueError('The samples_number parameter must be a '
                                 'positive integer.')
        else:
            raise TypeError('The samples_number parameter must be an integer.')

        input_is_ok = True
        return input_is_ok

    def explain_instance(self,
                         data_row: np.ndarray = None,
                         samples_number: Optional[int] = 50
                         ) -> Dict[str, Dict[Index, np.float64]]:
        """
        Generates explanations for data_row.


        Parameters
        ----------
        data_row : Union[numpy.ndarray, numpy.void], optional (default=None)
            A data point. If given, the sample will be generated around that
            point.
        samples_number : integer, optional (default=50)
            The number of samples to be generated.

        Raises
        ------
        IncorrectShapeError
            The ``data_row`` array is not a 1-dimensional numpy array. The
            ``data_row`` array does not contain the same number of features
            as the dataset used to initialise the class.
        TypeError
            The ``data_row`` array has a different dtype to the dataset used to
            initialise the class. The ``samples_number`` is not an integer.
        ValueError:
            The ``samples_number`` parameter is a negative integer.

        Returns
        -------
        blimey_explanation : Dictionary[str, Dictionary[Index, np.float64]]
            A dictionary where the key is a class name and the value is another
            dictionary that maps feature index to a feature importance.
        """
        assert self._explain_instance_is_input_valid(
            data_row, samples_number), 'Input is not valid.'
        discretized_data_row = self.discretizer.discretize(data_row)

        sampled_data = self.augmentor.sample(
            data_row, samples_number=samples_number, **self.kwargs)
        prediction_probabilities = self.global_model.predict_proba(
            sampled_data)
        discretized_sampled_data = self.discretizer.discretize(sampled_data)

        binary_data = fuds.similarity_binary_mask(
            discretized_sampled_data, discretized_data_row)

        discretized_value_names = self.discretizer.feature_value_names
        discretized_feature_names = []
        for i, index in enumerate(self.indices):
            data_row_discretized_value = int(discretized_data_row[index])
            if index in discretized_value_names.keys():
                discretized_feature_names.append(
                    discretized_value_names[index][data_row_discretized_value])
            else:
                discretized_feature_names.append(self.feature_names[i])

        blimey_explanation = {}
        for i in range(self.n_classes):
            local_model = self.local_model(**self.kwargs)
            local_model.fit(binary_data, prediction_probabilities[:, i])
            explainer = self.explainer_class(
                self.dataset,
                local_model=local_model,
                feature_names=discretized_feature_names,
                categorical_indices=self.categorical_indices,
                **self.kwargs)
            explanation = explainer.explain_instance(discretized_data_row,
                                                     **self.kwargs)

            blimey_explanation[self.class_names[i]] = explanation

        return blimey_explanation
        