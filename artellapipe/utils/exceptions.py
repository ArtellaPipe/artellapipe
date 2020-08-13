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
import sys
import traceback
from functools import wraps

import tpDcc as tp
from tpDcc.libs.python import osplatform

SENTRY_AVAILABLE = True
try:
    from sentry_sdk import push_scope, capture_message as sentry_capture_message, \
        capture_exception as sentry_capture_exception
except ImportError:
    SENTRY_AVAILABLE = False

import artellapipe

from Qt.QtCore import *
from Qt.QtWidgets import *


# TODO: Move this into a project specific configuration file
EXCEPTIONS_TO_SKIP = [
    'was not found in MAYA_PLUG_IN_PATH'
]


def capture_exception(exc):
    """
    Captures given exception
    :param exc: str or Exception, Exception to capture
    """

    if isinstance(exc, (str, unicode)):
        exc = Exception(exc)

    if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
        if SENTRY_AVAILABLE:
            capture_sentry_exception(exc)
        else:
            raise exc
    else:
        raise exc


def capture_message(msg):
    """
    Captures given message
    :param msg: str
    """

    if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
        if SENTRY_AVAILABLE:
            capture_sentry_message(msg)
        else:
            artellapipe.logger.info(msg)
    else:
        artellapipe.logger.info(msg)


def capture_sentry_exception(exc):
    """
    Captures given exception in sentry server
    :param exc: str or Exception, Exception to capture
    """

    if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
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
    else:
        artellapipe.logger.error('{} | {}'.format(exc, traceback.format_exc()))


def capture_sentry_message(msg):
    """
    Captures given exception in sentry server
    :param msg: str
    """

    if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
        with push_scope() as scope:
            scope.user = {'username': str(osplatform.get_user())}
            if artellapipe.project:
                scope.set_extra('project', artellapipe.project.name.title())
            sentry_capture_message(msg)
    else:
        artellapipe.logger.info(msg)


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
            artellapipe.logger.exception(exc, exc_info=True)
        return res
    return wrapper


def show_exception_box(exc_text, exc_trace):
    from artellapipe.widgets import exceptions
    if QApplication.instance() is not None:
        error_box = exceptions.ArtellaExceptionDialog(exc_text, exc_trace)
        error_box.exec_()


class ArtellaProjectUndefinedException(Exception):
    """
    Exception that is raised when project is not defined
    """

    pass


class ArtellaPipeException(Exception):
    """
    Custom exception that raises Bug Tracker Tool for Artella
    """

    def __init__(self, project, msg=None):
        self._project = project
        if msg is None:
            msg = 'An error ocurred in Artella Project: {}'.format(
                project.name.title())
        artellapipe.logger.exception('%s | &s', (msg, traceback.format_exc()))
        if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
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


class ArtellaExceptionHook(QObject):
    _exception_caught = Signal(object, object)

    def __init__(self, *args, **kwargs):
        super(ArtellaExceptionHook, self).__init__(*args, **kwargs)

        # this registers the exception_hook() function as hook with the Python interpreter
        sys.excepthook = self.exception_hook

        if tp.is_maya():
            import tpDcc.dccs.maya as maya
            maya.utils.formatGuiException = self.exception_hook

        # connect signal to execute the message box function always on main thread
        self._exception_caught.connect(show_exception_box)

    def exception_hook(self, exc_type, exc_value, exc_traceback, detail=2):
        """Function handling uncaught exceptions.
        It is triggered each time an uncaught exception occurs.
        """

        if issubclass(exc_type, KeyboardInterrupt):
            # ignore keyboard interrupt to support console applications
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            log_msg = '\n'.join([''.join(traceback.format_tb(exc_traceback)),
                                 '{0}: {1}'.format(exc_type.__name__, exc_value)])

            if 'SKIP_SENTRY_EXCEPTIONS' not in os.environ:
                if SENTRY_AVAILABLE:
                    capture_sentry_exception(Exception(log_msg))

            # trigger message box show
            skip_exception_box = self._should_skip_exception_box(exc_value, log_msg)
            if not skip_exception_box:
                self._exception_caught.emit(exc_value, log_msg)

            if tp.is_maya():
                import tpDcc.dccs.maya as maya
                return maya.utils._formatGuiException(exc_type, exc_value, exc_traceback, detail)

    def _should_skip_exception_box(self, exc_value, log_msg):
        """
        Internal function that returns whether or not exception message box should be show or not
        :param exc_value: str
        :param log_msg: str
        :return: bool
        """

        exc_value = str(exc_value) or ''
        log_msg = str(exc_value) or ''

        for skip_exc_msg in EXCEPTIONS_TO_SKIP:
            if skip_exc_msg in exc_value or skip_exc_msg in log_msg:
                return True

        return False
