#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to easily sync files from Artella server
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import python

from tpQtLib.widgets import lightbox

from artellapipe.gui import window

import artellapipe
from artellapipe.tools.bugtracker import bugtracker
from artellapipe.tools.artellamanager.widgets import localsync, serversync, urlsync, newassetdialog


class ArtellaSyncerMode(object):
    ALL = 'all'
    LOCAL = 'local'
    SERVER = 'server'
    URL = 'url'


class ArtellaSyncer(window.ArtellaWindow, object):

    LOGO_NAME = 'manager_logo'

    def __init__(self, project, mode=ArtellaSyncerMode.ALL):

        self._mode = python.force_list(mode)
        self._local_widget = None
        self._server_widget = None
        self._url_widget = None

        super(ArtellaSyncer, self).__init__(
            project=project,
            name='SyncerWindow',
            title='Artella Syncer',
            size=(800, 1100)
        )

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ArtellaSyncer, self).ui()

        self._tab = QTabWidget()
        self.main_layout.addWidget(self._tab)

        if ArtellaSyncerMode.ALL in self._mode:
            self._local_widget = localsync.ArtellaPathSyncWidget(project=self._project)
            self._server_widget = serversync.ArtellaSyncWidget(project=self._project)
            self._url_widget = urlsync.ArtellaURLWidget(project=self._project)
            self._tab.addTab(self._local_widget, 'Local')
            self._tab.addTab(self._server_widget, 'Server')
            self._tab.addTab(self._url_widget, 'URL')
        else:
            widgets_to_add = list()
            if ArtellaSyncerMode.LOCAL in self._mode:
                self._local_widget = localsync.ArtellaPathSyncWidget(project=self._project)
                widgets_to_add.append(('Local', self._local_widget))
            if ArtellaSyncerMode.SERVER in self._mode:
                self._server_widget = serversync.ArtellaSyncWidget(project=self._project)
                widgets_to_add.append(('Server', self._server_widget))
            if ArtellaSyncerMode.URL in self._mode:
                self._url_widget = urlsync.ArtellaURLWidget(project=self._project)
                widgets_to_add.append(('URL', self._url_widget))

            for widget in widgets_to_add:
                self._tab.addTab(widget[1], widget[0])

    def setup_signals(self):
        if self._local_widget:
            self._local_widget.syncOk.connect(self._on_local_sync_completed)
            self._local_widget.syncWarning.connect(self._on_local_sync_warning)
            self._local_widget.syncFailed.connect(self._on_local_sync_failed)
        if self._server_widget:
            self._server_widget.workerFailed.connect(self._on_server_worker_failed)
            self._server_widget.syncOk.connect(self._on_server_sync_completed)
            self._server_widget.syncWarning.connect(self._on_server_sync_warning)
            self._server_widget.syncFailed.connect(self._on_server_sync_failed)
            self._server_widget.createAsset.connect(self._on_create_new_asset)
        if self._url_widget:
            self._url_widget.syncOk.connect(self._on_url_sync_completed)
            self._url_widget.syncWarning.connect(self._on_url_sync_warning)
            self._url_widget.syncFailed.connect(self._on_url_sync_failed)

    def closeEvent(self, event):
        if self._server_widget:
            if self._server_widget.worker_is_running():
                self._server_widget.stop_artella_worker()
        event.accept()

    def _on_local_sync_completed(self, ok_msg):
        self.show_ok_message(ok_msg)

    def _on_local_sync_warning(self, warning_msg):
        self.show_warning_message(warning_msg)

    def _on_local_sync_failed(self, error_msg):
        self.show_error_message(error_msg)

    def _on_server_worker_failed(self, error_msg, trace):
        self.show_error_message(error_msg)
        artellapipe.logger.error(trace)
        bugtracker.ArtellaBugTracker.run(self._project, '{} | {}'.format(error_msg, trace))
        self.close()

    def _on_server_sync_completed(self, ok_msg):
        self.show_ok_message(ok_msg)

    def _on_server_sync_warning(self, warning_msg):
        self.show_warning_message(warning_msg)

    def _on_server_sync_failed(self, error_msg):
        self.show_error_message(error_msg)

    def _on_url_sync_completed(self, ok_msg):
        self.show_ok_message(ok_msg)

    def _on_url_sync_warning(self, warning_msg):
        self.show_warning_message(warning_msg)

    def _on_url_sync_failed(self, error_msg):
        self.show_error_message(error_msg)

    def _on_create_new_asset(self, item):
        new_asset_dlg = newassetdialog.ArtellaNewAssetDialog(project=self._project, asset_path=item.get_path())
        self._lightbox = lightbox.Lightbox(self)
        self._lightbox.set_widget(new_asset_dlg)
        self._lightbox.show()
        new_asset_dlg.show()


def run(project, mode=ArtellaSyncerMode.ALL):
    win = ArtellaSyncer(project=project, mode=mode)
    win.show()

    return win
