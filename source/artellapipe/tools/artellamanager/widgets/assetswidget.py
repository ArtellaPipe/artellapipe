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

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import base

import artellapipe
from artellapipe.core import defines, assetsviewer


class AssetsWidget(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project
        if not self._project:
            artellapipe.logger.warning('Invalid project for AssetsWidget!')

        super(AssetsWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(AssetsWidget, self).ui()

        main_categories_menu_layout = QHBoxLayout()
        main_categories_menu_layout.setContentsMargins(0, 0, 0, 0)
        main_categories_menu_layout.setSpacing(0)
        self.main_layout.addLayout(main_categories_menu_layout)

        categories_menu = QWidget()
        categories_menu_layout = QVBoxLayout()
        categories_menu_layout.setContentsMargins(0, 0, 0, 0)
        categories_menu_layout.setSpacing(0)
        categories_menu_layout.setAlignment(Qt.AlignTop)
        categories_menu.setLayout(categories_menu_layout)
        main_categories_menu_layout.addWidget(categories_menu)

        asset_splitter = QSplitter(Qt.Horizontal)
        main_categories_menu_layout.addWidget(asset_splitter)

        self._assets_viewer = assetsviewer.AssetsViewer(project=self._project, parent=self)
        asset_splitter.addWidget(self._assets_viewer)
        self._assets_viewer.first_empty_cell()

        self._categories_btn_grp = QButtonGroup(self)
        self._categories_btn_grp.setExclusive(True)
        categories_buttons = dict()
        asset_categories = self._project.asset_types if self._project else list()
        all_asset_categories = [defines.ARTELLA_ALL_CATEGORIES_NAME]
        all_asset_categories.extend(asset_categories)
        for category in all_asset_categories:
            new_btn = QPushButton(category)
            new_btn.setCheckable(True)
            categories_buttons[category] = new_btn
            categories_menu_layout.addWidget(new_btn)
            self._categories_btn_grp.addButton(new_btn)
            new_btn.toggled.connect(partial(self._change_category, category))
        categories_buttons[defines.ARTELLA_ALL_CATEGORIES_NAME].setChecked(True)

    def _change_category(self, category, flag):
        """
        Internal function that is called when the user presses an Asset Category button
        :param category: str
        """

        if flag:
            self._assets_viewer.change_category(category=category)



