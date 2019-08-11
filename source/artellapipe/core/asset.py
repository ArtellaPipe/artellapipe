#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions for asset in Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import time
import webbrowser
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpPyUtils import strings, path as path_utils
from tpQtLib.core import base, image, qtutils, menu

import artellapipe
from artellapipe.core import abstract, defines, artellalib
from artellapipe.tools.assetsmanager.widgets import assetinfo


class ArtellaAssetFileStatus(object):

    WORKING = defines.ARTELLA_SYNC_WORKING_ASSET_STATUS
    PUBLISHED = defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS

    @staticmethod
    def is_valid(status):
        """
        Returns whether given status is valid or not
        :param status: str
        :return: bool
        """

        return status == ArtellaAssetFileStatus.WORKING or status == ArtellaAssetFileStatus.PUBLISHED


class ArtellaAsset(abstract.AbstractAsset, object):

    ASSET_TYPE = None
    ASSET_FILES = dict()

    def __init__(self, project, asset_data, category=None):

        self._artella_data = None

        super(ArtellaAsset, self).__init__(project=project, asset_data=asset_data, category=category)

    @property
    def project(self):
        """
        Returns project linked to this assset
        :return: ArtellaProject
        """

        return self._project

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the asset
        :return: str
        """

        return self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_NAME_ATTR, defines.ARTELLA_DEFAULT_ASSET_NAME)

    def get_path(self):
        """
        Implements abstract get_path function
        Returns the path of the asset
        :return: str
        """

        return self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_PATH_ATTR, '')

    def get_category(self):
        """
        Implements abstract get_thumbnail_icon function
        Returns the category of the asset
        :return: str
        """

        if self._category:
            return self._category

        asset_path = self.get_path()
        if not asset_path:
            return ''

        self._category = strings.camel_case_to_string(os.path.basename(os.path.dirname(asset_path)))

        return self._category

    def get_artella_url(self):
        """
        Returns Artella URL of the asset
        :return: str
        """

        relative_path = self.get_relative_path()
        assets_url = self._project.get_artella_assets_url()
        artella_url = '{}{}'.format(assets_url, relative_path)

        return artella_url

    def get_artella_data(self, update=True, force=False):
        """
        Retrieves status data of the asset from Artella
        :param update: bool, Whether to resync data if it is already synced
        :param force: bool, Whether to force the resync of the data
        :return: ArtellaAssetMetaData
        """

        if not update:
            return self._artella_data

        if self._artella_data and not update and not force:
            return self._artella_data

        self._artella_data = artellalib.get_status(file_path=self.get_path())

        return self._artella_data

    def get_file(self, file_type, status, extension=None):
        """
        Returns file path of the given file type and status
        :param file_type: str
        :param status: str
        :param extension: str
        """

        if not extension:
            extension = defines.ARTELLA_DEFAULT_ASSET_FILES_EXTENSION

        if file_type not in self.project.asset_files:
            return None
        if not ArtellaAssetFileStatus.is_valid(status):
            return None

        asset_name = self.get_short_name()
        file_name = self._project.solve_name('asset_file', asset_name, asset_file_type=file_type)
        file_name += extension

        if status == ArtellaAssetFileStatus.WORKING:
            file_path = path_utils.clean_path(os.path.join(self.get_path(), defines.ARTELLA_WORKING_FOLDER, file_type, file_name))
        else:
            raise NotImplementedError('Open Published Assets is not implemented yet!')

        return file_path

    def open_in_artella(self):
        """
        Opens current asset in Artella web
        """

        artella_url = self.get_artella_url()
        webbrowser.open(artella_url)

    def view_locally(self):
        """
        Opens folder where item is located locally
        """

        artellalib.explore_file(self.get_path())

    def open_file(self, file_type, status, extension=None):
        """
        Opens asset file with the given type and status (if exists)
        :param file_type: str
        :param status: str
        :param extension: str
        :return:
        """

        file_path = self.get_file(file_type=file_type, status=status, extension=extension)
        if os.path.isfile(file_path):
            artellalib.open_file_in_maya(file_path)
        else:
            artellapipe.logger.warning('Impossible to open asset file of type "{}": {}'.format(file_type, file_path))

    def sync(self, file_type, sync_type):
        """
        Synchronizes assaet file type and with the given sync type (working or published)
        :param asset_type: str, type of asset file
        :param sync_type: str, type of sync (working, published or all)
        :param ask: bool, Whether user will be informed of the sync operation before starting or not
        """

        if sync_type != defines.ARTELLA_SYNC_ALL_ASSET_TYPES:
            if sync_type not in self.ASSET_FILES:
                artellapipe.logger.warning('Impossible to sync "{}" because current Asset {} does not support it!'.format(file_type, self.__class__.__name__))
                return
            if sync_type not in self.project:
                artellapipe.logger.warning('Impossible to sync "{}" because project "{}" does not support it!'.format(file_type, self.project.name.title()))
                return

        start_time = time.time()

        paths_to_sync = self._get_paths_to_sync(file_type, sync_type)

        elapsed_time = time.time() - start_time
        artellapipe.logger.warning('{} synchronized in {} seconds'.format(self.get_name(), elapsed_time))

    def _get_paths_to_sync(self, file_type, sync_type):
        """
        Internal function that returns a complete list of paths to sync depending on the given file type and sync type
        :param file_type: str
        :param sync_type: str
        :return: list(str)
        """

        paths_to_sync = list()

        if sync_type == defines.ARTELLA_SYNC_ALL_ASSET_STATUS or sync_type == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
            if sync_type == defines.ARTELLA_SYNC_ALL_ASSET_STATUS:
                paths_to_sync.append(os.path.join(self.get_path(), defines.ARTELLA_WORKING_FOLDER))
            else:
                paths_to_sync.append(os.path.join(self.get_path(), defines.ARTELLA_WORKING_FOLDER, file_type))

        return paths_to_sync


class ArtellaAssetWidget(base.BaseWidget, object):

    ASSET_INFO_CLASS = assetinfo.AssetInfoWidget
    DEFAULT_ICON = artellapipe.resource.icon('default')
    THUMB_SIZE = (200, 200)

    clicked = Signal(object)
    startSync = Signal(object, str, str)

    def __init__(self, asset, parent=None):

        self._asset = asset
        self._thumbnail_icon = None

        super(ArtellaAssetWidget, self).__init__(parent=parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(ArtellaAssetWidget, self).ui()

        self.setFixedWidth(160)
        self.setFixedHeight(160)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(2, 2, 2, 2)
        widget_layout.setSpacing(0)
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        self._asset_btn = QPushButton('', self)
        self._asset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._asset_btn.setIconSize(QSize(150, 150))
        self._asset_lbl = QLabel(defines.ARTELLA_DEFAULT_ASSET_NAME)
        self._asset_lbl.setAlignment(Qt.AlignCenter)

        widget_layout.addWidget(self._asset_btn)
        widget_layout.addWidget(self._asset_lbl)

    def setup_signals(self):
        self._asset_btn.clicked.connect(partial(self.clicked.emit, self))
        self.customContextMenuRequested.connect(self._on_context_menu)

    @property
    def asset(self):
        """
        Returns asset data
        :return: ArtellaAsset
        """

        return self._asset

    def get_asset_info(self):
        """
        Retruns AssetInfo widget associated to this asset
        :return: AssetInfoWidget
        """

        return self.ASSET_INFO_CLASS(self)

    def get_thumbnail_icon(self):
        """
        Implements abstract get_thumbnail_icon function
        Returns the icon of the asset
        :return: QIcon
        """

        # If the icon is already cached we return it
        if self._thumbnail_icon:
            return self._thumbnail_icon

        str_icon = self.asset.data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_ICON_ATTR, None)
        icon_format = self.asset.data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_ICON_FORMAT_ATTR, None)
        if not str_icon or not icon_format:
            return self.DEFAULT_ICON

        thumbnail_pixmap = QPixmap.fromImage(image.base64_to_image(str_icon.encode('utf-8'), image_format=icon_format))
        if not thumbnail_pixmap:
            self._thumbnail_icon = self.DEFAULT_ICON

        return QIcon(thumbnail_pixmap)

    def _init(self):
        """
        Internal function that initializes asset widget
        Can be extended to add custom initialization functionality to asset widgets
        """

        if not self._asset:
            return

        self._asset_lbl.setText(self._asset.get_name())

        thumb_icon = self.get_thumbnail_icon()
        if thumb_icon:
            self._asset_btn.setIcon(thumb_icon)

    def _create_context_menu(self, context_menu):
        """
        Internal function that generates contextual menu for asset widget
        Reimplement for custom functionality
        :param context_menu: Menu
        """

        sync_icon = artellapipe.resource.icon('sync')
        artella_icon = artellapipe.resource.icon('artella')

        artella_action = QAction(artella_icon, 'Open in Artella', context_menu)

        sync_action = QAction(sync_icon, 'Synchronize', context_menu)
        sync_menu = menu.Menu(self)
        actions_added = self._fill_sync_action_menu(sync_menu)
        artella_action.triggered.connect(self._on_open_in_artella)

        context_menu.addAction(artella_action)

        if actions_added:
            sync_action.setMenu(sync_menu)
            context_menu.addAction(sync_action)

    def _fill_sync_action_menu(self, sync_menu):
        """
        Internal function that fills sync menu with proper actions depending of the asset files supported
        :param sync_menu: Menu
        """

        if not sync_menu:
            return

        actions_to_add = list()

        for asset_type_name, asset_type_icon in self.asset.ASSET_FILES.items():
            asset_type_action = QAction(asset_type_icon, asset_type_name.title(), sync_menu)
            asset_type_action.triggered.connect(partial(self._on_sync, asset_type_name, defines.ARTELLA_SYNC_ALL_ASSET_STATUS, False))
            actions_to_add.append(asset_type_action)

        if actions_to_add:
            download_icon = artellapipe.resource.icon('download')
            all_action = QAction(download_icon, 'All', sync_menu)
            all_action.triggered.connect(partial(self._on_sync, defines.ARTELLA_SYNC_ALL_ASSET_TYPES, defines.ARTELLA_SYNC_ALL_ASSET_STATUS, False))
            actions_to_add.insert(0, all_action)

            for action in actions_to_add:
                sync_menu.addAction(action)

        return actions_to_add

    def _on_context_menu(self, pos):
        """
        Internal callback function that is called when the user wants to show asset widget contextual menu
        :param pos: QPoint
        """

        context_menu = menu.Menu(self)
        self._create_context_menu(context_menu)
        context_menu.exec_(self.mapToGlobal(pos))

    def _on_open_in_artella(self):
        """
        Internal callback function that is called when the user presses Open in Artella contextual menu action
        """

        self._asset.open_in_artella()

    def _on_sync(self, file_type, sync_type, ask=False):
        """
        Internal callback function that is called when the user tries to Sync an asset through UI
        :param file_type: str
        :param sync_type: str
        :param ask: bool
        """

        if ask:
            res = qtutils.show_question(
                None,
                'Synchronize "{}" file: {}'.format(self.asset.get_name(), file_type.title()),
                'Are you sure you want to sync this asset? This can take some time!'
            )
            if res != QMessageBox.Yes:
                return

        self.startSync.emit(self.asset, file_type, sync_type)
