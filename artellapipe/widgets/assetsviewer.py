#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for asset viewer
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs.python import python
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import grid

import artellapipe
from artellapipe.core import defines
from artellapipe.widgets import asset as asset_widget

LOGGER = logging.getLogger('artellapipe')


class AssetsViewer(grid.GridWidget, object):

    assetAdded = Signal(object)
    assetSynced = Signal()

    def __init__(self, project, column_count=4, show_context_menu=False, parent=None):
        super(AssetsViewer, self).__init__(parent=parent)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setColumnCount(column_count)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setSelectionMode(QAbstractItemView.NoSelection)

        self._assets = list()
        self._cache = list()

        self._project = project
        self._show_context_menu = show_context_menu

        self._menu = self._create_contextual_menu()

    def contextMenuEvent(self, event):
        if not self._menu or not self._show_context_menu:
            return
        self._menu.exec_(event.globalPos())

    def get_assets(self, update_cache=True, force=False):
        """
        Returns a list with all the assets of the project
        :param update_cache: bool, Updates the internal cache
        :param force: bool, If True, cache and assets will be updated
        :return: list(ArtellaAssetWidget)
        """

        if update_cache:
            self.update_cache(force=force)

        if self._assets and not force:
            return self._assets

        self.update_assets()

        return self._assets

    def update_cache(self, force=False):
        """
        Updates internal cache with the current assets located in Artella server
        """

        if self._cache and not force:
            return self._cache

        python.clear_list(self._cache)
        self._cache = artellapipe.AssetsMgr().find_all_assets() or list()

        return self._cache

    def update_assets(self, force=False):
        """
        Updates the list of assets in the asset viewer
        :param force: bool
        """

        if not self._project:
            LOGGER.warning('Project not defined!')
            return

        self.clear_assets()

        all_assets = self.update_cache(force=force)
        if not all_assets:
            return

        for asset in all_assets:
            if not asset:
                continue
            new_asset_widget = asset_widget.ArtellaAssetWidget(asset)
            self.add_asset(new_asset_widget)

    def update_assets_thumbnails(self, force=False):
        """
        Updates all the thumbnails of the assets
        :param force: bool
        """

        for asset in self.get_assets():
            asset.update_thumbnail_icon(force=force)

    def clear_assets(self):
        """
        Clear all the assets of the asset viewer
        """

        python.clear_list(self._assets)
        self.clear()

    def change_category(self, category=None):
        """
        Changes the category assets that are being showed by the viewer
        :param category: str
        """

        if not category:
            category = defines.ArtellaFileStatus.ALL

        if category != defines.ArtellaFileStatus.ALL and category not in artellapipe.AssetsMgr().get_asset_categories():
            LOGGER.warning(
                'Asset Type {} is not a valid asset type for project {}'.format(category, self._project.name.title()))
            category = defines.ArtellaFileStatus.ALL

        self.clear()

        new_assets = list()
        for new_asset in reversed(self._assets):
            if category == defines.ArtellaFileStatus.ALL:
                new_asset.setVisible(True)
                new_assets.insert(0, new_asset)
            else:
                if new_asset.asset.get_category() == category:
                    new_asset.setVisible(True)
                    new_assets.insert(0, new_asset)
                else:
                    new_asset.setVisible(False)
                    new_assets.append(new_asset)

        for new_asset in new_assets:
            self._add_widget(new_asset)

    def add_asset(self, asset_widget):
        """
        Adds given asset widget to viewer
        :param asset_widget: ArtellaAssetWidget
        """

        if not asset_widget:
            return

        self._add_widget(asset_widget)
        self._assets.append(asset_widget)
        self.assetAdded.emit(asset_widget)

    def _add_widget(self, widget):
        """
        Internal function that adds a new widget to the viewer
        :param widget: QWidget
        :return:
        """

        if widget is None:
            return

        row, col = self.first_empty_cell()
        self.addWidget(row, col, widget)
        self.resizeRowsToContents()

    def _create_contextual_menu(self):
        """
        Returns custom contextual menu
        :return: QMenu
        """

        new_menu = QMenu(self)
        get_thumbnails_action = QAction(tpDcc.ResourcesMgr().icon('picture'), 'Update Thumbnails', new_menu)
        get_thumbnails_action.triggered.connect(self._on_update_thumbnails)
        new_menu.addAction(get_thumbnails_action)

        return new_menu

    def _on_update_thumbnails(self):
        """
        Internal callback function that is called when Update Thumbnails action is triggered
        """

        self.update_assets_thumbnails(force=True)


class CategorizedAssetViewer(base.BaseWidget, object):

    def __init__(self, project, column_count=4, show_context_menu=False, parent=None):

        self._project = project
        self._column_count = column_count
        self._show_context_menu = show_context_menu

        super(CategorizedAssetViewer, self).__init__(parent=parent)

        self._assets_viewer.update_assets()

    def ui(self):
        super(CategorizedAssetViewer, self).ui()

        self._assets_viewer = AssetsViewer(
            project=self._project,
            column_count=self._column_count,
            show_context_menu=self._show_context_menu,
            parent=self
        )
        self._assets_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._categories_menu_layout = QHBoxLayout()
        self._categories_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._categories_menu_layout.setSpacing(0)
        self._categories_menu_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self._categories_menu_layout)

        self._categories_btn_grp = QButtonGroup(self)
        self._categories_btn_grp.setExclusive(True)
        asset_categories = artellapipe.AssetsMgr().get_asset_types() or list()

        self.main_layout.addWidget(self._assets_viewer)

        self.update_asset_categories(asset_categories)

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
            new_btn.toggled.connect(partial(self._on_change_category, category))

    def _on_change_category(self, category, flag):
        """
        Internal callback function that is called when the user presses an Asset Category button
        :param category: str
        :param flag: bool
        """

        if flag:
            self._assets_viewer.change_category(category=category)
