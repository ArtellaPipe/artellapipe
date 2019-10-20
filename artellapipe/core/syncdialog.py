#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog used to synchronize info from Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import threading
import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *

from artellapipe.core import artellalib
from artellapipe.utils import resource

LOGGER = logging.getLogger()


class ArtellaSyncSplash(QSplashScreen, object):
    def __init__(self, *args, **kwargs):
        super(ArtellaSyncSplash, self).__init__(*args, **kwargs)

        self.mousePressEvent = self.MousePressEvent
        self._canceled = False

    def MousePressEvent(self, event):
        pass


class ArtellaSyncDialog(QDialog, object):

    syncFinished = Signal()

    def __init__(self, project, parent=None):
        super(ArtellaSyncDialog, self).__init__(parent=parent)

        self._project = project

        self.ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_update_progress_bar)

    def ui(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        splash_pixmap = resource.ResourceManager().pixmap('sync_splash', key='project')
        splash = ArtellaSyncSplash(splash_pixmap)
        self._splash_layout = QVBoxLayout()
        self._splash_layout.setAlignment(Qt.AlignBottom)
        splash.setLayout(self._splash_layout)
        self.main_layout.addWidget(splash)

        self.extended_layout = QVBoxLayout()
        self.extended_layout.setContentsMargins(2, 2, 2, 2)
        self.extended_layout.setSpacing(2)
        self._splash_layout.addLayout(self.extended_layout)

        self._progress_bar = self._project.get_progress_bar()
        self._progress_bar.setMaximum(50)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setTextVisible(False)
        self._splash_layout.addWidget(self._progress_bar)

        self._progress_text = QLabel('Synchronizing Artella Files ... Please wait!')
        self._progress_text.setAlignment(Qt.AlignCenter)
        self._progress_text.setStyleSheet("QLabel { background-color : rgba(0, 0, 0, 180); color : white; }")
        font = self._progress_text.font()
        font.setPointSize(10)
        self._progress_text.setFont(font)
        self._splash_layout.addWidget(self._progress_text)

        self.setFixedSize(splash_pixmap.size())

    def sync(self):
        """
        Starts the sync process
        """

        self.raise_()
        self._timer.start(200)

    def _on_update_progress_bar(self):

        if self._progress_bar.value() >= self._progress_bar.maximum():
            self._progress_bar.setValue(0)
        self._progress_bar.setValue(self._progress_bar.value() + 1)

    def closeEvent(self, event):
        self.syncFinished.emit()
        self._timer.stop()
        return super(ArtellaSyncDialog, self).closeEvent(event)


class ArtellaSyncFileDialog(ArtellaSyncDialog, object):
    def __init__(self, project, files=None):

        self._files = files

        super(ArtellaSyncFileDialog, self).__init__(project=project)

    def _on_update_progress_bar(self):
        super(ArtellaSyncFileDialog, self)._on_update_progress_bar()

        if self._event.is_set():
            self._timer.stop()
            self.close()

    def sync(self):
        if not self._files:
            self.close()
        super(ArtellaSyncFileDialog, self).sync()
        self._event = threading.Event()
        try:
            threading.Thread(target=self.sync_files, args=(self._event,), name='ArtellaSyncFilesThread').start()
        except Exception as e:
            LOGGER.debug(str(e))
            LOGGER.debug(traceback.format_exc())
        self.exec_()

    def sync_files(self, event):
        for p in self._files:
            if not p:
                continue
            file_path = os.path.relpath(p, self._project.get_assets_path())
            self._progress_text.setText('Syncing file: {0} ... Please wait!'.format(file_path))
            valid_sync = artellalib.synchronize_file(p)
            if valid_sync is None or valid_sync == {}:
                event.set()
        event.set()


class ArtellaSyncPathDialog(ArtellaSyncDialog, object):
    def __init__(self, project, paths=None):

        self._paths = paths

        super(ArtellaSyncPathDialog, self).__init__(project=project)

    def _on_update_progress_bar(self):
        super(ArtellaSyncPathDialog, self)._on_update_progress_bar()

        if self._event.is_set():
            self._timer.stop()
            self.close()

    def sync(self):
        if not self._paths:
            self.close()
        super(ArtellaSyncPathDialog, self).sync()
        self._event = threading.Event()
        try:
            threading.Thread(target=self.sync_files, args=(self._event,), name='ArtellaSyncPathsThread').start()
        except Exception as e:
            LOGGER.debug(str(e))
            LOGGER.debug(traceback.format_exc())
        self.exec_()

    def sync_files(self, event):
        for p in self._paths:
            file_path = os.path.relpath(p, self._project.get_assets_path())
            self._progress_text.setText('Syncing files of folder: {0} ... Please wait!'.format(file_path))
            try:
                artellalib.synchronize_path(p)
            except Exception as e:
                LOGGER.error('Impossible to sync files ... Maybe Artella is down! Try it later ...')
                LOGGER.error(str(e))
                event.set()
        event.set()


class ArtellaSyncGetDepsDialog(ArtellaSyncDialog, object):
    def __init__(self, project):
        super(ArtellaSyncGetDepsDialog, self).__init__(project=project)

    def ui(self):
        super(ArtellaSyncGetDepsDialog, self).ui()

        self._splash_layout.addItem(QSpacerItem(0, 5))

        cancel_btn_layout = QHBoxLayout()
        cancel_btn_layout.setContentsMargins(0, 0, 0, 0)
        cancel_btn_layout.setSpacing(0)
        self._splash_layout.addLayout(cancel_btn_layout)
        cancel_btn_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self._cancel_btn = QPushButton('Cancel')
        self._cancel_btn.setVisible(False)
        self._cancel_btn.setMaximumWidth(100)
        cancel_btn_layout.addWidget(self._cancel_btn)
        cancel_btn_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self._cancel_btn.clicked.connect(self._cancel_sync)

    def _update_progress_bar(self):
        super(ArtellaSyncGetDepsDialog, self)._update_progress_bar()

        if self._canceled:
            self._event.set()

        if self._event.is_set():
            self._timer.stop()
            self.close()

    def _cancel_sync(self):
        self._canceled = True
