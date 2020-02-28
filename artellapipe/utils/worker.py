#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for background workers
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import uuid
import logging
import traceback
from threading import Lock, Condition

from Qt.QtCore import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import qtutils

import artellapipe

LOGGER = logging.getLogger()


class Worker(QThread, object):
    workCompleted = Signal(str, dict)
    workFailure = Signal(str, str, str)

    def __init__(self, app, parent=None):
        super(Worker, self).__init__(parent=parent)

        self._execute_tasks = True
        self._app = app

        self._queue_mutex = Lock()

        self._queue = list()
        self._receivers = dict()

        self._wait_condition = Condition(self._queue_mutex)

    def stop(self, wait_for_completion=True):
        """
        Stops the worker, run this before shutdown
        """

        with self._queue_mutex:
            self._execute_tasks = False
            self._wait_condition.notifyAll()

        if wait_for_completion:
            self.wait()

    def clear(self):
        """
        Empties the queue
        """

        with self._queue_mutex:
            self._queue = list()

    def queue_work(self, worker_fn, params=None, asap=False):
        """
        Queues up some work returning a unique id to identify this worker
        :param worker_fn:
        :param params:
        :param asap:
        :return:
        """

        uid = uuid.uuid4().hex
        if params:
            work = {'id': uid, 'fn': worker_fn, 'params': params}
        else:
            work = {'id': uid, 'fn': worker_fn}
        with self._queue_mutex:
            if asap:
                self._queue.insert(0, work)
            else:
                self._queue.append(work)

            self._wait_condition.notifyAll()

        return uid

    def run(self):
        while self._execute_tasks:
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                if self.isInterruptionRequested():
                    return
            with self._queue_mutex:
                if len(self._queue) == 0:
                    self._wait_condition.wait()
                    if len(self._queue) == 0:
                        continue
                item_to_process = self._queue.pop()

            if not self._execute_tasks:
                break

            try:
                if item_to_process.get('params', None):
                    data = item_to_process['fn'](item_to_process['params'])
                else:
                    data = item_to_process['fn']()
            except Exception as e:
                if self._execute_tasks:
                    import traceback
                    self.workFailure.emit(
                        item_to_process['id'], 'An error ocurred: {}'.format(str(e)), str(traceback.format_exc()))
            else:
                if self._execute_tasks:
                    data = data if data is not None else dict()
                    self.workCompleted.emit(item_to_process['id'], data)


class QtWorker(QThread, object):

    """
    Qt based worker
    """

    workCompleted = Signal(str, object)
    workFailure = Signal(str, str)

    def __init__(self, app, parent=None):
        super(QtWorker, self).__init__(parent)

        self._execute_tasks = True
        self._app = app
        self._queue_mutex = QMutex()
        self._queue = list()
        self._receivers = dict()

    def stop(self):
        """
        Stops the worker, run this before shutdown
        """

        self._execute_tasks = False

    def clear(self):
        """
        Empties the queue
        """

        self._queue_mutex.lock()
        try:
            self._queue = list()
        finally:
            self._queue_mutex.unlock()

    def queue_work(self, worker_fn, params, asap=False):
        """
        Queues up some work
        :param worker_fn: fn
        :param params: dict
        :param asap: bool
        :return: uid, unique identifier to identify the work
        """

        uid = uuid.uuid4().hex
        work = {"id": uid, "fn": worker_fn, "params": params}
        self._queue_mutex.lock()
        try:
            if asap:
                self._queue.insert(0, work)
            else:
                self._queue.append(work)
        finally:
            self._queue_mutex.unlock()

        return uid

    def run(self):
        while self._execute_tasks:
            self._queue_mutex.lock()
            try:
                queue_len = len(self._queue)
            finally:
                self._queue_mutex.unlock()

            if queue_len == 0:
                self.msleep(200)
            else:
                self._queue_mutex.lock()
                try:
                    item_to_process = self._queue.pop(0)
                finally:
                    self._queue_mutex.unlock()

                try:
                    data = item_to_process['fn'](item_to_process['params'])
                except Exception as e:
                    if self._execute_tasks:
                        self.workFailure.emit(
                            item_to_process['id'], 'An error ocurred: {} | {}'.format(e, traceback.format_exc()))
                else:
                    if self._execute_tasks:
                        data = data if data is not None else dict()
                        self.workCompleted.emit(item_to_process['id'], data)


class ThumbDownloaderWorker(QRunnable, object):

    class ThumbDownloaderWorkerSignals(QObject, object):
        triggered = Signal(object)

    def __init__(self, *args):
        super(ThumbDownloaderWorker, self).__init__(*args)

        self._path = None
        self._preview_id = None
        self._force = False
        self.signals = ThumbDownloaderWorker.ThumbDownloaderWorkerSignals()

    def set_preview_id(self, preview_id):
        """
        Sets the preview ID linked to Kitsu project
        :param preview_id: str
        """

        self._preview_id = preview_id

    def set_path(self, path):
        """
        Sets the path where image should be downloaded
        :param path: str
        """

        self._path = path

    def set_force(self, flag):
        """
        Sets whether thumb should be downloaded even if it exists
        :param flag: bool
        """

        self._force = flag

    def run(self):
        try:
            if self._preview_id and self._path:
                if not os.path.isfile(self._path) or self._force:
                    artellapipe.Tracker().download_preview_file_thumbnail(self._preview_id, self._path)
                if not self._path or not os.path.isfile(self._path):
                    icon = QIcon()
                else:
                    icon_pixmap = QPixmap(self._path)
                    icon = QIcon(icon_pixmap)
                self.signals.triggered.emit(icon)
        except Exception as exc:
            LOGGER.error('Cannot load thumbnail image: {}!'.format(exc))
