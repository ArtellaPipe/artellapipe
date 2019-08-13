#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to interact with Artella functionality inside DCCS
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import weakref
import traceback
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import qtutils

from artellapipe.core import defines, assetsviewer
from artellapipe.gui import window


class ArtellaAssetsLibraryWidget(QWidget, object):

    # Necessary to support Maya dock
    name = 'ArtellaAssetsLibrary'
    title = 'Artella Assets Viewer'

    _instances = list()

    ASSETS_VIEWER_CLASS = assetsviewer.AssetsViewer

    def __init__(self, project, parent=None):

        self._project = project

        main_window = tp.Dcc.get_main_window()
        if parent is None:
            parent = main_window

        super(ArtellaAssetsLibraryWidget, self).__init__(parent=parent)

        if tp.is_maya():
            ArtellaAssetsLibraryWidget._delete_instances()
            self.__class__._instances.append(weakref.proxy(self))

        self.ui()
        self.resize(150, 800)

        self._assets_viewer.update_assets()

    @staticmethod
    def _delete_instances():
        for ins in ArtellaAssetsLibraryWidget._instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except Exception:
                pass

            ArtellaAssetsLibraryWidget._instances.remove(ins)
            del ins

    def ui(self):

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        if tp.is_maya():
            self.parent().layout().addLayout(self.main_layout)
        else:
            self.setLayout(self.main_layout)

        self._assets_viewer = self.ASSETS_VIEWER_CLASS(
            project=self._project,
            column_count=2,
            parent=self
        )
        self._assets_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        top_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.addLayout(top_layout)

        self._categories_menu_layout = QHBoxLayout()
        self._categories_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._categories_menu_layout.setSpacing(0)
        self._categories_menu_layout.setAlignment(Qt.AlignTop)
        top_layout.addLayout(self._categories_menu_layout)

        self._categories_btn_grp = QButtonGroup(self)
        self._categories_btn_grp.setExclusive(True)
        asset_categories = self._project.asset_types if self._project else list()

        self.main_layout.addWidget(self._assets_viewer)

        self._supported_types_layout = QHBoxLayout()
        self._supported_types_layout.setContentsMargins(2, 2, 2, 2)
        self._supported_types_layout.setSpacing(2)
        self._supported_types_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self._supported_types_layout)

        self._supported_types_btn_grp = QButtonGroup(self)
        self._supported_types_btn_grp.setExclusive(True)
        supported_types = self._project.assets_library_file_types if self._project else list()

        self._assets_viewer.assetAdded.connect(self._on_asset_added)

        self.update_asset_categories(asset_categories)
        self.update_supported_types(supported_types)

    def update_asset_categories(self, asset_categories):
        """
        Updates current categories with the given ones
        :param asset_categories: list(str)
        """

        for btn in self._categories_btn_grp.buttons():
            self._categories_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._categories_menu_layout)

        all_asset_categories = [defines.ARTELLA_ALL_CATEGORIES_NAME]
        all_asset_categories.extend(asset_categories)
        for category in all_asset_categories:
            new_btn = QPushButton(category)
            new_btn.setCheckable(True)
            self._categories_menu_layout.addWidget(new_btn)
            self._categories_btn_grp.addButton(new_btn)
            if category == defines.ARTELLA_ALL_CATEGORIES_NAME:
                new_btn.setChecked(True)
            new_btn.toggled.connect(partial(self._change_category, category))

    def update_supported_types(self, supported_types):
        """
        Updates current supported types
        :param supported_types: dict(str, str)
        """

        for btn in self._supported_types_btn_grp.buttons():
            self._supported_types_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._supported_types_layout)

        total_buttons = 0
        for type_name, type_extension in supported_types.items():
            new_btn = QPushButton(type_name.title())
            new_btn.setCheckable(True)
            new_btn.extension = type_extension
            self._supported_types_layout.addWidget(new_btn)
            self._supported_types_btn_grp.addButton(new_btn)
            if total_buttons == 0:
                new_btn.setChecked(True)
            total_buttons += 1

    def _change_category(self, category, flag):
        """
        Internal function that is called when the user presses an Asset Category button
        :param category: str
        """

        if flag:
            self._assets_viewer.change_category(category=category)

    def _setup_asset_signals(self, asset_widget):
        """
        Internal function that sets proper signals to given asset widget
        This function can be extended to add new signals to added items
        :param asset_widget: ArtellaAssetWidget
        """

        asset_widget.clicked.connect(self._on_asset_clicked)

    def _on_asset_added(self, asset_widget):
        """
        Internal callback function that is called when a new asset widget is added to the assets viewer
        :param asset_widget: ArtellaAssetWidget
        """

        if not asset_widget:
            return

        self._setup_asset_signals(asset_widget)

    def _on_asset_clicked(self, asset_widget):
        """
        Internal callback function that is called when an asset button is clicked
        :param asset_widget: ArtellaAssetWidget
        """

        if not asset_widget:
            return

        for btn in self._supported_types_btn_grp.buttons():
            if btn.isChecked():
                try:
                    asset_widget.asset.reference_file_by_extension(extension=btn.extension)
                except Exception as e:
                    self._project.logger.warning('Impossible to reference asset!')
                    self._project.logger.error('{} | {}'.format(e, traceback.format_exc()))
                finally:
                    return


class ArtellaAssetsLibrary(window.ArtellaWindow, object):

    LOGO_NAME = 'assetsmanager_logo'
    LIBRARY_WIDGET = ArtellaAssetsLibraryWidget

    def __init__(self, project, parent=None):
        super(ArtellaAssetsLibrary, self).__init__(
            project=project,
            name='ManagerWindow',
            title='Manager',
            size=(1100, 900),
            parent=parent
        )

    def ui(self):
        super(ArtellaAssetsLibrary, self).ui()

        self._library_widget = self.LIBRARY_WIDGET(project=self._project)
        self.main_layout.addWidget(self._library_widget)


def run(project):
    if tp.is_maya():
        win = window.dock_window(project=project, window_class=ArtellaAssetsLibraryWidget)
        return win
    else:
        win = ArtellaAssetsLibrary(project=project)
        win.show()
        return win
