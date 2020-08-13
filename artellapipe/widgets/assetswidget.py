#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for assets manager widget
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging.config
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs.qt.core import base, qtutils

import artellapipe
from artellapipe.core import defines
from artellapipe.widgets import assetsviewer

LOGGER = logging.getLogger('artellapipe')


class AssetsWidget(base.BaseWidget, object):

    assetAdded = Signal(object)

    def __init__(self, project, column_count=4, show_viewer_menu=False, parent=None, category_alignment='vertical'):

        self._project = project
        self._column_count = column_count
        self._show_viewer_menu = show_viewer_menu
        self._category_alignment = category_alignment
        if not self._project:
            LOGGER.warning('Invalid project for AssetsWidget!')

        super(AssetsWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(AssetsWidget, self).ui()

        if self._category_alignment == 'vertical':
            main_categories_menu_layout = QHBoxLayout()
        else:
            main_categories_menu_layout = QVBoxLayout()

        main_categories_menu_layout.setContentsMargins(0, 0, 0, 0)
        main_categories_menu_layout.setSpacing(0)
        self.main_layout.addLayout(main_categories_menu_layout)

        categories_menu = QWidget()

        if self._category_alignment == 'vertical':
            self._categories_menu_layout = QVBoxLayout()
        else:
            self._categories_menu_layout = QHBoxLayout()
        self._categories_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._categories_menu_layout.setSpacing(0)
        self._categories_menu_layout.setAlignment(Qt.AlignTop)
        categories_menu.setLayout(self._categories_menu_layout)
        main_categories_menu_layout.addWidget(categories_menu)

        asset_splitter = QSplitter(Qt.Horizontal)
        main_categories_menu_layout.addWidget(asset_splitter)

        self._assets_viewer = assetsviewer.AssetsViewer(
            project=self._project, column_count=self._column_count,
            show_context_menu=self._show_viewer_menu, parent=self)
        asset_splitter.addWidget(self._assets_viewer)
        self._assets_viewer.first_empty_cell()

        self._categories_btn_grp = QButtonGroup(self)
        self._categories_btn_grp.setExclusive(True)
        asset_categories = artellapipe.AssetsMgr().get_asset_categories()
        self.update_asset_categories(asset_categories)

    def setup_signals(self):
        self._assets_viewer.assetAdded.connect(self.assetAdded.emit)

    def update_assets(self):
        """
        Updates the list of assets in the asset viewer
        """

        self._assets_viewer.update_assets()

    def clear_assets(self):
        """
        Clear all the assets of the asset viewer
        """

        self._assets_viewer.clear_assets()

    def update_asset_categories(self, asset_categories):
        """
        Updates current categories with the given ones
        :param asset_categories: list(str)
        """

        for btn in self._categories_btn_grp.buttons():
            self._categories_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._categories_menu_layout)

        all_asset_categories = [defines.ArtellaFileStatus.ALL]
        all_asset_categories.extend(asset_categories)
        for category in all_asset_categories:
            new_btn = QPushButton(category)
            new_btn.setMinimumWidth(QFontMetrics(new_btn.font()).width(category) + 10)
            new_btn.setIcon(tpDcc.ResourcesMgr().icon(category.lower()))
            new_btn.setCheckable(True)
            self._categories_menu_layout.addWidget(new_btn)
            self._categories_btn_grp.addButton(new_btn)
            if category == defines.ArtellaFileStatus.ALL:
                new_btn.setIcon(tpDcc.ResourcesMgr().icon('home'))
                new_btn.setChecked(True)
            new_btn.toggled.connect(partial(self._change_category, category))

    def _change_category(self, category, flag):
        """
        Internal function that is called when the user presses an Asset Category button
        :param category: str
        """

        if flag:
            self._assets_viewer.change_category(category=category)
