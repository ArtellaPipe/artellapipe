#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains dialog to create new Artella assets for current project
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import path as path_utils

from tpQtLib.core import qtutils
from tpQtLib.widgets import splitters, stack

import  artellapipe
from artellapipe.core import defines, artellalib
from artellapipe.gui import dialog, waiter, spinner
from artellapipe.utils import worker


class ArtellaNewAssetDialog(dialog.ArtellaDialog, object):
    def __init__(self, project, asset_path, parent=None):

        self._project = project
        self._asset_path = asset_path
        self._folders_to_create = dict()

        self._artella_worker = worker.Worker(app=QApplication.instance())
        self._artella_worker.workCompleted.connect(self._on_artella_worker_completed)
        self._artella_worker.workFailure.connect(self._on_artella_worker_failed)
        self._artella_worker.start()

        super(ArtellaNewAssetDialog, self).__init__(
            name='ArtellaNewAssetDialog',
            title='Artella - New Asset',
            show_dragger=False,
            fixed_size=True,
            parent=parent
        )

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        return main_layout

    def ui(self):
        super(ArtellaNewAssetDialog, self).ui()

        self.resize(400, 350)

        self.setAttribute(Qt.WA_TranslucentBackground)
        if qtutils.is_pyside2():
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        self._waiter = waiter.ArtellaWaiter(spinner_type=spinner.SpinnerType.Thumb)

        asset_widget = QWidget()
        asset_layout = QVBoxLayout()
        asset_layout.setContentsMargins(2, 2, 2, 2)
        asset_layout.setSpacing(2)
        asset_widget.setLayout(asset_layout)

        asset_name_lbl = QLabel('Aset Name')
        self._asset_name_line = QLineEdit()
        asset_layout.addWidget(asset_name_lbl)
        asset_layout.addWidget(self._asset_name_line)

        asset_layout.addLayout(splitters.SplitterLayout())

        folders_lbl = QLabel('Asset Folders')
        asset_layout.addWidget(folders_lbl)
        asset_files = self._project.asset_files
        for f in asset_files:
            new_cbx = QCheckBox(f)
            new_cbx.setChecked(True)
            self._folders_to_create[f] = new_cbx
            asset_layout.addWidget(new_cbx)

        asset_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        self._create_asset_btn = QPushButton('Create')
        self._create_asset_btn.setEnabled(False)
        asset_layout.addWidget(self._create_asset_btn)

        self._stack.addWidget(asset_widget)
        self._stack.addWidget(self._waiter)

    def setup_signals(self):
        self._create_asset_btn.clicked.connect(self._on_create_asset)
        self._asset_name_line.textChanged.connect(self._on_update_text)
        self._stack.animFinished.connect(self._on_stack_anim_finished)

    def _create_new_asset(self, data=None):
        """
        Internal function that creates a new asset in Artella
        """

        asset_name = self._asset_name_line.text()
        if not asset_name:
            return

        artellalib.create_asset(asset_name, self._asset_path)

        for file_name, cbx in self._folders_to_create.items():
            if cbx.isChecked():
                file_path = path_utils.clean_path(os.path.join(self._asset_path, asset_name, defines.ARTELLA_WORKING_FOLDER))
                artellalib.new_folder(file_path, file_name)

        return True

    def _on_create_asset(self):
        """
        Internal callback function that is called when Create button is called
        """

        self._stack.slide_in_index(1)

    def _on_update_text(self, text):
        self._create_asset_btn.setEnabled(bool(text))

    def _on_stack_anim_finished(self):
        """
        Internal callback function that is called when stack animation finish
        """

        self._artella_worker.queue_work(self._create_new_asset, {})

    def _on_artella_worker_completed(self, uid, asset_widget):
        """
        Internal callback function that is called when worker finishes its job
        """

        try:
            self.parent().close()
        except Exception:
            self.close()

    def _on_artella_worker_failed(self, uid, msg, trace):
        """
        Internal callback function that is called when the Artella worker fails
        :param uid: str
        :param msg: str
        :param trace: str
        """

        artellapipe.logger.error('{} | {} | {}'.format(uid, msg, trace))

        try:
            self.parent().close()
        except Exception:
            self.close()
