"""
Tests custom warnings, errors and exceptions.
"""
# Author: Kacper Sokol <k.sokol@bristol.ac.uk>
# License: new BSD

import pytest

import fatf.exceptions


def test_fatfexception():
    """
    Tests :class:`fatf.exceptions.FATFException`.
    """
    default_message = ''
    # Custom exception without a message
    with pytest.raises(fatf.exceptions.FATFException) as exception_info:
        raise fatf.exceptions.FATFException()
    assert str(exception_info.value) == default_message

    # Custom exception without a message
    with pytest.raises(fatf.exceptions.FATFException) as exception_info:
        raise fatf.exceptions.FATFException
    assert str(exception_info.value) == default_message

    # Custom exception with a message
    custom_message = 'Custom message.'
    with pytest.raises(fatf.exceptions.FATFException) as exception_info:
        raise fatf.exceptions.FATFException(custom_message)
    assert str(exception_info.value) == custom_message


def test_missingimplementationerror():
    """
    Tests :class:`fatf.exceptions.MissingImplementationError`.
    """
    default_message = ''
    # Custom exception without a message
    with pytest.raises(fatf.exceptions.MissingImplementationError) as exin:
        raise fatf.exceptions.MissingImplementationError()
    assert str(exin.value) == default_message

    # Custom exception without a message
    with pytest.raises(fatf.exceptions.MissingImplementationError) as exin:
        raise fatf.exceptions.MissingImplementationError
    assert str(exin.value) == default_message

    # Custom exception with a message
    custom_message = 'Custom message.'
    with pytest.raises(fatf.exceptions.MissingImplementationError) as exin:
        raise fatf.exceptions.MissingImplementationError(custom_message)
    assert str(exin.value) == custom_message


def test_incorrectshapeerror():
    """
    Tests :class:`fatf.exceptions.IncorrectShapeError`.
    """
    default_message = ''
    # Custom exception without a message
    with pytest.raises(fatf.exceptions.IncorrectShapeError) as exin:
        raise fatf.exceptions.IncorrectShapeError()
    assert str(exin.value) == default_message

    # Custom exception without a message
    with pytest.raises(fatf.exceptions.IncorrectShapeError) as exin:
        raise fatf.exceptions.IncorrectShapeError
    assert str(exin.value) == default_message

    # Custom exception with a message
    custom_message = 'Custom message.'
    with pytest.raises(fatf.exceptions.IncorrectShapeError) as exin:
        raise fatf.exceptions.IncorrectShapeError(custom_message)
    assert str(exin.value) == custom_message


def test_incompatiblemodelerror():
    """
    Tests :class:`fatf.exceptions.IncompatibleModelError`.
    """
    default_message = ''
    # Custom exception without a message
    with pytest.raises(fatf.exceptions.IncompatibleModelError) as exin:
        raise fatf.exceptions.IncompatibleModelError()
    assert str(exin.value) == default_message

    # Custom exception without a message
    with pytest.raises(fatf.exceptions.IncompatibleModelError) as exin:
        raise fatf.exceptions.IncompatibleModelError
    assert str(exin.value) == default_message

    # Custom exception with a message
    custom_message = 'Custom message.'
    with pytest.raises(fatf.exceptions.IncompatibleModelError) as exin:
        raise fatf.exceptions.IncompatibleModelError(custom_message)
    assert str(exin.value) == custom_message
