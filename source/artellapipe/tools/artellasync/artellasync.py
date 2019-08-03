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

from artellapipe.gui import window

from artellapipe.tools.artellasync.widgets import pathsync, synctree


class ArtellaSyncerMode(object):
    ALL = 'all'
    PATH = 'path'
    TREE = 'tree'


class ArtellaSyncer(window.ArtellaWindow, object):

    LOGO_NAME = 'syncer_logo'

    def __init__(self, project, mode=ArtellaSyncerMode.ALL):

        self._mode = mode

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

        if self._mode == ArtellaSyncerMode.ALL:
            self._tab = QTabWidget()
            self.main_layout.addWidget(self._tab)
            self._local_widget = pathsync.ArtellaPathSyncWidget(self._project)
            self._server_widget = synctree.ArtellaSyncWidget()

            self._tab.addTab(self._local_widget, 'Local')
            self._tab.addTab(self._server_widget, 'Server')
        elif self._mode == ArtellaSyncerMode.PATH:
            self._local_widget = pathsync.ArtellaPathSyncWidget(project=self._project)
            self._server_widget = None
            self.main_layout.addWidget(self._local_widget)
        else:
            self._local_widget = None
            self._server_widget = synctree.ArtellaSyncTree()
            self.main_layout.addWidget(self._server_widget)

    def setup_signals(self):
        if self._local_widget:
            self._local_widget.syncOk.connect(self._on_local_sync_completed)
            self._local_widget.syncWarning.connect(self._on_local_sync_warning)
            self._local_widget.syncFailed.connect(self._on_local_sync_failed)

    def _on_local_sync_completed(self, ok_msg):
        self.show_ok_message(ok_msg)

    def _on_local_sync_warning(self, warning_msg):
        self.show_warning_message(warning_msg)

    def _on_local_sync_failed(self, error_msg):
        self.show_error_message(error_msg)


def run(project):
    win = ArtellaSyncer(project=project)
    win.show()

    return win