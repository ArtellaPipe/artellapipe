#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains exceptions functions
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import traceback
from functools import wraps

from tpPyUtils import osplatform

SENTRY_AVAILABLE = True
try:
    from sentry_sdk import push_scope, capture_message as sentry_capture_message, \
        capture_exception as sentry_capture_exception
except ImportError:
    SENTRY_AVAILABLE = False

import artellapipe

LOGGER = logging.getLogger()


def capture_exception(exc):
    """
    Captures given exception
    :param exc: str or Exception, Exception to capture
    """

    if SENTRY_AVAILABLE:
        capture_sentry_exception(exc)
    else:
        if isinstance(exc, (str, unicode)):
            exc = Exception(exc)
        raise exc


def capture_message(msg):
    """
    Captures given message
    :param msg: str
    """

    if SENTRY_AVAILABLE:
        capture_sentry_message(msg)
    else:
        LOGGER.info(msg)


def capture_sentry_exception(exc):
    """
    Captures given exception in sentry server
    :param exc: str or Exception, Exception to capture
    """

    with push_scope() as scope:
        scope.user = {'username': str(osplatform.get_user())}
        if artellapipe.project:
            scope.set_extra('project', artellapipe.project.name.title())

        if isinstance(exc, (str, unicode)):
            exc = Exception(exc)
            sentry_capture_exception(Exception(exc))
        else:
            sentry_capture_exception(exc)

        traceback.print_exc()
        raise exc


def capture_sentry_message(msg):
    """
    Captures given exception in sentry server
    :param msg: str
    """

    with push_scope() as scope:
        scope.user = {'username': str(osplatform.get_user())}
        if artellapipe.project:
            scope.set_extra('project', artellapipe.project.name.title())
        sentry_capture_message(msg)


def sentry_exception(function):
    """
    Decorators that sends exception to sentry server
    """

    @wraps(function)
    def wrapper(*args, **kwargs):
        """

        :param args: list
        :param kwargs: dict
        :return: object
        """

        res = None
        try:
            res = function(*args, **kwargs)
        except RuntimeError as exc:
            if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
                capture_sentry_exception(exc)
            LOGGER.exception(exc, exc_info=True)
        return res
    return wrapper


class ArtellaPipeException(Exception):
    """
    Custom exception that raises Bug Tracker Tool for Artella
    """

    def __init__(self, project, msg=None):
        self._project = project
        if msg is None:
            msg = 'An error ocurred in Artella Project: {}'.format(
                project.name.title())
        LOGGER.exception('%s | &s', (msg, traceback.format_exc()))
        capture_sentry_exception(msg)
        super(ArtellaPipeException, self).__init__(msg)


class RecursiveParserExceptions(ArtellaPipeException, object):
    """
    Custom exception that is raised when a recursive section is found by parser
    """
    def __init__(self, project, msg=None):
        super(RecursiveParserExceptions, self).__init__(project=project,
                                                        msg=msg)


class FileNotFoundException(Exception):
    """
    Exceptions that is raised when a file does not exists on disk
    """

    def __init__(self, *args):
        super(FileNotFoundException, self).__init__(*args)
