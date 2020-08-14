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
import time
import logging
import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc

import artellapipe
from artellapipe.libs.artella.core import artellalib

LOGGER = logging.getLogger('artellapipe')


class ArtellaSyncSplash(QSplashScreen, object):
    def __init__(self, *args, **kwargs):
        super(ArtellaSyncSplash, self).__init__(*args, **kwargs)

        self.mousePressEvent = self.MousePressEvent
        self._canceled = False

    def MousePressEvent(self, event):
        pass


class ArtellaSyncDialog(QDialog, object):

    doSync = Signal()
    syncFinished = Signal()

    def __init__(self, files, project, recursive=False, force_sync_files=False, parent=None):
        super(ArtellaSyncDialog, self).__init__(parent=parent)

        self._files = files
        self._project = project
        self._recursive = recursive
        self._force_sync_files = force_sync_files

        self._sync_thread = QThread(self)
        self._sync_worker = SyncFileWorker()
        self._sync_worker.moveToThread(self._sync_thread)
        self._sync_worker.syncStarted.connect(self._on_sync_start)
        self._sync_worker.syncFinished.connect(self._on_sync_finish)
        self._sync_worker.syncUpdated.connect(self._on_sync_updated)
        self._sync_worker.syncFailFile.connect(self._on_sync_file_failed)
        self._sync_thread.start()

        self._progress_timer = QTimer(self)

        self._progress_timer.timeout.connect(self._on_update_progress_bar)
        self.doSync.connect(self._sync_worker.run)

        self.ui()

    def ui(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        splash_pixmap = tpDcc.ResourcesMgr().pixmap('sync_splash', key='project')
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

        self._sync_worker.set_files(self._files)
        self._sync_worker.set_assets_path(artellapipe.AssetsMgr().get_assets_path())
        self._sync_worker.set_recursive(self._recursive)
        self._sync_worker.set_force_sync_files(self._force_sync_files)
        self._sync_worker.set_update_progress(artellapipe.project.is_enterprise())

        self.raise_()

        self.doSync.emit()

        self.exec_()

    def _on_sync_start(self):
        if not artellapipe.project.is_enterprise():
            self._progress_timer.start(200)

    def _on_sync_finish(self, error_msg):
        self._progress_timer.stop()
        self.syncFinished.emit()

        if error_msg:
            LOGGER.error(error_msg)

        self.close()

    def _on_sync_updated(self, text, total_done, total_in_progress, total_operations, total_bytes, bytes_to_download):

        progress_status = '{} > {} of {} KiB downloaded ({} of {} files downloaded)'.format(
            text, int(total_bytes / 1024), int(bytes_to_download / 1024), total_in_progress, total_operations)
        self._progress_bar.setValue(total_done)
        self._progress_text.setText(progress_status)

    def _on_sync_file_failed(self, file_path):
        LOGGER.warning('Was not possible to synchronize file from Artella server: {}!'.format(file_path))

    def _on_update_progress_bar(self):
        if self._progress_bar.value() >= self._progress_bar.maximum():
            self._progress_bar.setValue(0)
        self._progress_bar.setValue(self._progress_bar.value() + 1)

    def closeEvent(self, event):
        self.syncFinished.emit()
        self._progress_timer.stop()
        artellalib.pause_synchronization()
        return super(ArtellaSyncDialog, self).closeEvent(event)


class ArtellaSyncFileDialog(ArtellaSyncDialog, object):
    def __init__(self, project, files=None):
        super(ArtellaSyncFileDialog, self).__init__(files=files, force_sync_files=True, project=project)


class ArtellaSyncPathDialog(ArtellaSyncDialog, object):
    def __init__(self, project, paths=None, recursive=False):
        super(ArtellaSyncPathDialog, self).__init__(
            files=paths, project=project, force_sync_files=False, recursive=recursive)


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
            self._progress_timer.stop()
            self.close()

    def _cancel_sync(self):
        self._canceled = True


class SyncFileWorker(QObject, object):

    syncUpdated = Signal(str, int, int, int, int, int)
    syncStarted = Signal()
    syncFinished = Signal(str)
    syncFailFile = Signal(str)

    def __init__(self):
        super(SyncFileWorker, self).__init__()

        self._files = list()
        self._assets_path = ''
        self._recursive = False
        self._force_sync_file = False
        self._update_progress = False

    def set_assets_path(self, assets_path):
        self._assets_path = assets_path

    def set_files(self, files):
        self._files = files

    def set_recursive(self, flag):
        self._recursive = flag

    def set_force_sync_files(self, flag):
        self._force_sync_file = flag

    def set_update_progress(self, flag):
        self._update_progress = flag

    def run(self):
        self.syncStarted.emit()

        if not self._files:
            self.syncFinished.emit('No files to sync')
            return

        for file_path in self._files:
            if not file_path:
                continue
            try:
                file_path_to_sync = os.path.relpath(file_path, self._assets_path)
                msg = '{}'.format(file_path_to_sync)
                self.syncUpdated.emit(msg, 0, 0, 0, 0, 0)
                if self._force_sync_file:
                    valid_sync = artellalib.synchronize_file(file_path)
                else:
                    valid_sync = artellalib.synchronize_path_with_folders(file_path, recursive=self._recursive)
                if not valid_sync:
                    self.syncFailFile.emit(file_path)
                    continue

                if self._update_progress:

                    # We force the waiting to a high value, otherwise Artella Drive Client will return that
                    # no download is being processed
                    time.sleep(2.0)

                    while True:
                        progress, fd, ft, bd, bt = artellalib.get_synchronization_progress()
                        self.syncUpdated.emit(msg, progress, fd, ft, bd, bt)
                        if progress >= 100 or bd == bt:
                            break
            except Exception:
                self.syncFinished.emit(
                    'Unexpected error while synchronizing file from Artella server: {} | {}'.format(
                        file_path, traceback.format_exc()))
                break

        self.syncFinished.emit('')
