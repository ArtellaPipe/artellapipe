#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for assets list
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe


class ShotAssets(base.BaseWidget, object):

    updateHierarchy = Signal(QObject)

    def __init__(self, project, parent=None):

        self._project = project
        self._file_types = dict()
        self.widgets = list()

        super(ShotAssets, self).__init__(parent=parent)

        self._update_menu()

    def ui(self):
        super(ShotAssets, self).ui()

        self.setMouseTracking(True)

        self._add_btn = QPushButton('Add Asset File')
        self._add_btn.setIcon(artellapipe.resource.icon('add'))
        self.main_layout.addWidget(self._add_btn)
        self.main_layout.addLayout(splitters.SplitterLayout())

        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self._grid_layout)

        scroll_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(scroll_widget)

        self._assets_layout = QVBoxLayout()
        self._assets_layout.setContentsMargins(1, 1, 1, 1)
        self._assets_layout.setSpacing(0)
        self._assets_layout.addStretch()
        scroll_widget.setLayout(self._assets_layout)
        self._grid_layout.addWidget(scroll_area, 1, 0, 1, 4)

    def set_file_types(self, file_types):
        """
        self._setup_menubar()
        :param file_types: list
        :return:
        """

        self._file_types = file_types
        self._update_menu()

    def all_assets(self):
        """
        Returns a list with all assets added in the assets list
        :return: list
        """

        all_assets = list()
        for i in range(self._assets_layout.count()):
            child = self._assets_layout.itemAt(i)
            if child.widget() is not None:
                all_assets.append(child.widget())

        return all_assets

    def clear_assets(self):
        """
        Clears all the assets from the list
        """

        del self.widgets[:]
        while self._assets_layout.count():
            child = self._assets_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        self._assets_layout.setSpacing(0)
        self._assets_layout.addStretch()

    def add_asset(self, asset):
        """
        Adds a new asset into the list
        :param asset:
        :return:
        """

        self.widgets.append(asset)
        self._assets_layout.insertWidget(0, asset)
        self.updateHierarchy.emit(asset)

    def load_shot_files(self, shot_files):
        """
        Loads given files into the Shot Assets List
        :param shot_files: list
        :return: list
        """

        assets_added = False
        for file_name, file_info in shot_files.items():
            file_path = os.path.join(self._project.get_path(), file_name)
            if not os.path.isfile(file_path):
                artellapipe.logger.warning('Asset File "{}" does not exists in your computer!'.format(file_path))
                continue
            file_data = file_info.get('data', None)
            if not file_data:
                file_data = file_info
                extra_data = None
            else:
                extra_data = file_info.get('extra', None)
            if not file_data:
                artellapipe.logger.warning('Asset File "{}" does not contains any data!'.format(file_path))
                continue
            file_extension = os.path.splitext(file_path)[-1]
            for _, file_type in reversed(self._file_types.items()):
                if file_type and file_type.FILE_EXTENSION == file_extension:
                    new_asset_file = file_type(asset_file=file_path, asset_data=file_data, extra_data=extra_data)
                    if not new_asset_file:
                        artellapipe.logger.warning('Impossible to generate {} asset from {}! Skipping ...'.format(file_type, file_path))
                        break
                    assets_added = True
                    self.add_asset(new_asset_file)
                    break

        return assets_added

    def _update_menu(self):
        """
        Internal function that updates add button menu depending of the current file types
        """

        new_menu = QMenu(self._add_btn)

        for file_name, file_type in reversed(self._file_types.items()):
            file_action = QAction(file_type.FILE_ICON, file_name, new_menu)
            file_action.triggered.connect(partial(self._on_add_file_item, file_type))
            new_menu.addAction(file_action)

        self._add_btn.setMenu(new_menu)

    def _on_add_file_item(self, file_item):
        """
        Internal callback function that adds a new file item into the Shot Assembler assets list
        :param file_item:
        """

        res = tp.Dcc.select_file_dialog(
            title='Select {} File'.format(file_item.FILE_TYPE.title()),
            start_directory=self._project.get_path(),
            pattern='{} {} Files (*{})'.format(self._project.name.title(), file_item.FILE_TYPE.title(), file_item.FILE_EXTENSION)
        )
        if not res:
            return

        new_asset = file_item(asset_file=res)
        self.add_asset(new_asset)
