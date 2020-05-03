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

from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs.python import osplatform
from tpDcc.libs.qt.widgets import label, buttons, dividers, message

SENTRY_AVAILABLE = True
try:
    from sentry_sdk import push_scope, capture_message as sentry_capture_message, \
        capture_exception as sentry_capture_exception
except ImportError:
    SENTRY_AVAILABLE = False

import artellapipe

from Qt.QtCore import *
from Qt.QtWidgets import *

if tp.is_maya():
    import tpDcc.dccs.maya as maya


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
    if QApplication.instance() is not None:
        error_box = ArtellaExceptionDialog(exc_text, exc_trace)
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


class ArtellaExceptionDialog(tp.Dialog):
    def __init__(self, exc_text, exc_trace):
        self._text = exc_text
        self._trace = exc_trace
        super(ArtellaExceptionDialog, self).__init__(title='Artella-Error', show_on_initialize=False)

        self.setWindowIcon(tp.ResourcesMgr().icon('artella'))

    def ui(self):
        super(ArtellaExceptionDialog, self).ui()

        text_lbl = label.BaseLabel(str(self._text) if self._text else '')
        self._error_text = QPlainTextEdit(str(self._trace) if self._trace else '')
        self._error_text.setReadOnly(True)
        self._error_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout.addWidget(text_lbl)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addWidget(self._error_text)

        buttons_lyt = QHBoxLayout()
        self._copy_to_clipboard_btn = buttons.BaseButton('Copy to Clipboard')
        self._hide_details_btn = buttons.BaseButton('Hide Details...')
        buttons_lyt.addStretch()
        buttons_lyt.addWidget(self._copy_to_clipboard_btn)
        buttons_lyt.addWidget(self._hide_details_btn)
        self.main_layout.addStretch()
        self.main_layout.addLayout(buttons_lyt)

    def setup_signals(self):
        self._hide_details_btn.clicked.connect(self._on_toggle_details)
        self._copy_to_clipboard_btn.clicked.connect(self._on_copy_to_clipboard)

    def _on_toggle_details(self):
        self._error_text.setVisible(not self._error_text.isVisible())
        if self._error_text.isVisible():
            self._hide_details_btn.setText('Hide Error Trace')
        else:
            self._hide_details_btn.setText('Show Error Trace')

    def _on_copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._error_text.toPlainText(), QClipboard.Clipboard)
        if clipboard.supportsSelection():
            clipboard.setText(self._error_text.toPlainText(), QClipboard.Selection)
        message.PopupMessage.success(text='Error message copied to clipboard!.', parent=self)


class ArtellaExceptionHook(QObject):
    _exception_caught = Signal(object, object)

    def __init__(self, *args, **kwargs):
        super(ArtellaExceptionHook, self).__init__(*args, **kwargs)

        # this registers the exception_hook() function as hook with the Python interpreter
        sys.excepthook = self.exception_hook

        if tp.is_maya():
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
