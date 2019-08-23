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

import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import base

import artellapipe
from artellapipe.core import defines, artellalib
from artellapipe.gui import progressbar
from artellapipe.tools.bugtracker import bugtracker


class ArtellaURLWidget(base.BaseWidget, object):

    syncOk = Signal(str)
    syncFailed = Signal(str)
    syncWarning = Signal(str)

    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaURLWidget, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaURLWidget, self).ui()

        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(2, 2, 2, 2)
        url_layout.setSpacing(2)
        self.main_layout.addLayout(url_layout)

        url_lbl = QLabel('URL: ')
        url_layout.addWidget(url_lbl)
        self._url_line = QLineEdit()
        url_layout.addWidget(self._url_line)

        self._progress = progressbar.ArtellaProgressBar(project=self._project)
        self._progress.setVisible(False)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        self._sync_subfolders_cbx = QCheckBox('Sync Subfolders?')
        self._sync_subfolders_cbx.setMaximumWidth(110)
        self._sync_btn = QPushButton('Sync')
        self._sync_btn.setIcon(artellapipe.resource.icon('sync'))
        buttons_layout.addWidget(self._sync_subfolders_cbx)
        buttons_layout.addWidget(self._sync_btn)

        self.main_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        self.main_layout.addWidget(self._progress)
        self.main_layout.addLayout(buttons_layout)

    def setup_signals(self):
        self._sync_btn.clicked.connect(self._on_sync)

    def _on_sync(self):
        """
        Internal callback function that is called when the user presses Sync button
        """

        url_to_sync = self._url_line.text()
        if not url_to_sync:
            self.syncWarning.emit('Type URL before syncing.')
            return

        if not url_to_sync.startswith('https://'):
            url_to_sync = 'https://' + url_to_sync

        root_url = '{}/project/{}/files'.format(defines.ARTELLA_WEB, self._project.id)
        base_url = url_to_sync.replace(root_url, '')
        url_to_sync = url_to_sync.replace(root_url, self._project.get_path())

        self._progress.set_minimum(0)
        self._progress.set_maximum(2)
        self._progress.setVisible(True)
        self._progress.set_text('Syncing URL: {}. Please wait ...'.format(base_url))
        self._progress.set_value(1)
        self.repaint()

        try:
            valid_sync = artellalib.synchronize_path_with_folders(url_to_sync, self._sync_subfolders_cbx.isChecked())
            if valid_sync:
                self.syncOk.emit('URL {} synced successfully!'.format(base_url))
            else:
                self.syncFailed.emit('Error while syncing URL {} from Artella server!'.format(base_url))
        except Exception as e:
            self.repaint()
            msg = 'Error while syncing URL: {}'.format(base_url)
            artellapipe.logger.error(msg)
            artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))
            bugtracker.ArtellaBugTracker.run(self._project, traceback.format_exc())
            self._progress.set_value(0)
            self._progress.set_text('')
            self.syncFailed.emit(msg)

        self._progress.set_value(0)
        self._progress.set_text('')
        self._progress.setVisible(False)
