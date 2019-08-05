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

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.widgets import grid

import artellapipe
from artellapipe.core import defines, asset


class AssetsViewer(grid.GridWidget, object):

    ASSET_WIDGET_CLASS = asset.ArtellaAssetWidget

    assetAdded = Signal(object)
    assetSynced = Signal()

    def __init__(self, project, column_count=4, parent=None):
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
        self._project = project

    def get_assets(self, category=None):
        """
        Returns a list with all the assets of the given categories; All assets will be returned if not category is given
        :param category: str
        :return: list(ArtellaAssetWidget)
        """

        if not self._assets:
            self.update_assets()

        return self._assets

    def update_assets(self):
        """
        Updates the list of assets in the asset viewer
        :param async: bool, Whether the update operation should be done asynchronously or not
        """

        if not self._project:
            artellapipe.logger.warning('Project not defined!')
            return

        self.clear_assets()

        all_assets = self._project.find_all_assets()
        if not all_assets:
            return

        for asset in all_assets:
            if not asset:
                continue
            asset_widget = self.ASSET_WIDGET_CLASS(asset)
            self.add_asset(asset_widget)

    def clear_assets(self):
        """
        Clear all the assets of the asset viewer
        """

        self._assets = list()
        self.clear()

    def change_category(self, category=None):
        """
        Changes the category assets that are being showed by the viewer
        :param category: str
        """

        if not category:
            category = defines.ARTELLA_ALL_CATEGORIES_NAME

        if category != defines.ARTELLA_ALL_CATEGORIES_NAME and category not in self._project.asset_types:
            artellapipe.logger.warning('Asset Type {} is not a valid asset type for project {}'.format(category, self._project.name.title()))
            category = defines.ARTELLA_ALL_CATEGORIES_NAME

        self.clear()

        new_assets = list()
        for new_asset in reversed(self._assets):
            if category == defines.ARTELLA_ALL_CATEGORIES_NAME:
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
        Adds given asset to viewer
        :param asset_widget: ArtellaAssetWidget
        """

        if asset_widget is None:
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
