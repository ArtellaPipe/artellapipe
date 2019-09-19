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

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import qtutils
from tpQtLib.widgets import splitters, stack

import artellapipe
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
        self._asset_layout = QVBoxLayout()
        self._asset_layout.setContentsMargins(2, 2, 2, 2)
        self._asset_layout.setSpacing(2)
        asset_widget.setLayout(self._asset_layout)

        asset_name_lbl = QLabel('Asset Name')
        self._asset_name_line = QLineEdit()
        self._asset_layout.addWidget(asset_name_lbl)
        self._asset_layout.addWidget(self._asset_name_line)

        self._asset_layout.addLayout(splitters.SplitterLayout())

        folders_lbl = QLabel('Asset Folders')
        self._asset_layout.addWidget(folders_lbl)
        asset_files = self._project.asset_files
        for f in asset_files:
            new_cbx = QCheckBox(f)
            new_cbx.setChecked(True)
            self._folders_to_create[f] = new_cbx
            self._asset_layout.addWidget(new_cbx)

        self._asset_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        self._create_asset_btn = QPushButton('Create')
        self._create_asset_btn.setEnabled(False)
        self._cancel_btn = QPushButton('Cancel')
        self._cancel_btn.setMaximumWidth(100)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        buttons_layout.addWidget(self._create_asset_btn)
        buttons_layout.addWidget(self._cancel_btn)
        self._asset_layout.addLayout(buttons_layout)

        self._stack.addWidget(asset_widget)
        self._stack.addWidget(self._waiter)

    def setup_signals(self):
        self._create_asset_btn.clicked.connect(self._on_create_asset)
        self._cancel_btn.clicked.connect(self.fade_close)
        self._asset_name_line.textChanged.connect(self._on_update_text)
        self._stack.animFinished.connect(self._on_stack_anim_finished)

    def get_asset_folders(self):
        """
        Returns a list with all the folders that a specific asset needs
        :return: list(str)
        """

        folders_to_create = list()
        for folder_name, cbx in self._folders_to_create.items():
            if cbx.isChecked():
                folders_to_create.append(folder_name)

        return folders_to_create

    def _create_new_asset(self, data=None):
        """
        Internal function that creates a new asset in Artella
        """

        asset_name = self._asset_name_line.text()
        if not asset_name:
            return

        # self._project.create_asset(asset_name, self._asset_path)
        folders_to_create = self.get_asset_folders()
        valid_create = self._project.create_asset_in_artella(asset_name, self._asset_path, folders_to_create=folders_to_create)

        return valid_create

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
