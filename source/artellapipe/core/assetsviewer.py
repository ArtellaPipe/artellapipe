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
from artellapipe.core import defines


class AssetsViewer(grid.GridWidget, object):

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

        self._project = project

        self.update_assets()

    def update_assets(self):
        """
        Updates the list of assets in the asset viewer
        """

        self.clear()

        if not self._project:
            artellapipe.logger.warning('Project not defined!')
            return

        all_assets = self._project.find_all_assets()
        if not all_assets:
            return

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

        print('Changing category to: {}'.format(category))

