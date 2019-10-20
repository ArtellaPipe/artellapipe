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
import ast
import string
import logging
import webbrowser
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDccLib as tp
from tpPyUtils import python, decorators, strings, path as path_utils
from tpQtLib.core import base, image, qtutils, menu

from artellapipe.core import abstract, defines, artellalib, assetinfo
from artellapipe.utils import resource

LOGGER = logging.getLogger()
if tp.is_maya():
    import tpMayaLib as maya


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

    def __init__(self, project, asset_data, category=None, node=None):

        self._artella_data = None

        super(ArtellaAsset, self).__init__(project=project, asset_data=asset_data, category=category, node=node)

    @property
    def project(self):
        """
        Returns project linked to this assset
        :return: ArtellaProject
        """

        return self._project

    def is_available(self):
        """
        Returns whether or not asset is available locally or not
        :return: bool
        """

        asset_path = self.get_path()
        if not asset_path:
            return False

        return os.path.isdir(asset_path)

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the asset
        :return: str
        """

        return self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(
            defines.ARTELLA_ASSET_DATA_NAME_ATTR, defines.ARTELLA_DEFAULT_ASSET_NAME)

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

    def get_icon(self):
        """
        Returns the icon of the asset depending of the category
        :return: QIcon
        """

        return resource.ResourceManager().icon(self.get_category().lower().replace(' ', '_'))

    def get_file_type(self, file_type, extension=None):
        """
        Returns asset file object of the current asset and given file type
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        if file_type not in self.ASSET_FILES:
            return None

        asset_file_class = self._project.get_asset_file(file_type=file_type, extension=extension)
        if not asset_file_class:
            LOGGER.warning('File Type: {} | {} not registered in current project!'.format(file_type, extension))
            return

        return asset_file_class(asset=self)

    def view_locally(self):
        """
        Opens folder where item is located locally
        """

        artellalib.explore_file(self.get_path())

    def get_valid_file_types(self):
        """
        Returns a list with all valid file types of current asset
        :return: list(str)
        """

        asset_files = self.ASSET_FILES.keys()
        return [i for i in asset_files if i in self._project.asset_files]

    # ==========================================================================================================
    # ARTELLA
    # ==========================================================================================================

    def get_artella_url(self):
        """
        Returns Artella URL of the asset
        :return: str
        """

        relative_path = self.get_relative_path()
        assets_url = self._project.get_artella_assets_url()
        artella_url = '{}{}'.format(assets_url, relative_path)

        return artella_url

    def get_artella_data(self, force_update=False):
        """
        Retrieves status data of the asset from Artella
        :param force_update: bool, Whether to resync data if it is already synced
        :return: ArtellaAssetMetaData
        """

        if not force_update and self._artella_data:
            return self._artella_data

        self._artella_data = artellalib.get_status(file_path=self.get_path())

        return self._artella_data

    def open_in_artella(self):
        """
        Opens current asset in Artella web
        """

        artella_url = self.get_artella_url()
        webbrowser.open(artella_url)

    # ==========================================================================================================
    # FILES
    # ==========================================================================================================

    def get_file(self, file_type, status, extension=None, fix_path=False):
        """
        Returns file path of the given file type and status
        :param file_type: str
        :param status: str
        :param extension: str
        :param fix_path: str
        """

        if not extension:
            extension = defines.ARTELLA_DEFAULT_ASSET_FILES_EXTENSION

        if file_type not in self.project.asset_files:
            return None
        if not ArtellaAssetFileStatus.is_valid(status):
            return None

        asset_name = self.get_name()
        file_name = self._get_file_name(asset_name, asset_file_type=file_type)
        file_name += extension

        file_path = None
        if status == ArtellaAssetFileStatus.WORKING:
            file_path = path_utils.clean_path(
                os.path.join(self.get_path(), defines.ARTELLA_WORKING_FOLDER, file_type, file_name))
        else:
            latest_local_versions = self.get_latest_local_versions(status=defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS)
            if latest_local_versions[file_type]:
                file_path = os.path.join(self.get_path(), latest_local_versions[file_type][1], file_type, file_name)

        if not file_path:
            raise RuntimeError(
                'Impossible to retrieve file because asset path for {} is not valid!'.format(asset_name))

        if fix_path:
            file_path = self._project.fix_path(file_path)

        return file_path

    def open_file(self, file_type, status, extension=None, fix_path=True):
        """
        Opens asset file with the given type and status (if exists)
        :param file_type: str
        :param status: str
        :param extension: str
        :param fix_path: bool
        :return: bool
        """

        file_path = self.get_file(file_type=file_type, status=status, extension=extension, fix_path=fix_path)
        if os.path.isfile(file_path):
            if fix_path:
                file_path = self._project.fix_path(file_path)
            artellalib.open_file_in_maya(file_path)
            return True
        else:
            LOGGER.warning('Impossible to open asset file of type "{}": {}'.format(file_type, file_path))

        return False

    def reference_file(self, file_type, status, extension=None, fix_path=True):
        """
        References asset file with the given type and status
        :param file_type: str
        :param status: str
        :param fix_path: bool
        :return: bool
        """

        file_path = self.get_file(file_type=file_type, status=status, extension=extension, fix_path=False)
        if os.path.isfile(file_path):
            if fix_path:
                file_path = self._project.fix_path(file_path)
            if tp.is_maya():
                use_rename = maya.cmds.optionVar(q='referenceOptionsUseRenamePrefix')
                if use_rename:
                    namespace = maya.cmds.optionVar(q='referenceOptionsRenamePrefix')
                else:
                    filename = os.path.basename(file_path)
                    namespace, _ = os.path.splitext(filename)
                return tp.Dcc.reference_file(file_path=file_path, namespace=namespace)
            else:
                return tp.Dcc.reference_file(file_path=file_path)
        else:
            LOGGER.warning('Impossible to reference asset file of type "{}": {}'.format(file_type, file_path))
            return False

    # ==========================================================================================================
    # SYNC
    # ==========================================================================================================

    @decorators.timestamp
    def sync(self, file_type, sync_type):
        """
        Synchronizes asset file type and with the given sync type (working or published)
        :param asset_type: str, type of asset file
        :param sync_type: str, type of sync (working, published or all)
        :param ask: bool, Whether user will be informed of the sync operation before starting or not
        """

        # self.export_shaders()

        if sync_type != defines.ARTELLA_SYNC_ALL_ASSET_STATUS:
            if sync_type not in self.ASSET_FILES:
                LOGGER.warning(
                    'Impossible to sync "{}" because current Asset {} does not support it!'.format(
                        file_type, self.__class__.__name__))
                return
            if sync_type not in self.project:
                LOGGER.warning(
                    'Impossible to sync "{}" because project "{}" does not support it!'.format(
                        file_type, self.project.name.title()))
                return

        paths_to_sync = self._get_paths_to_sync(file_type, sync_type)
        if not paths_to_sync:
            LOGGER.warning('No Paths to sync for "{}"'.format(self.get_name()))
            return

        self._project.sync_files(files=paths_to_sync)

    @decorators.timestamp
    def sync_latest_published_files(self, file_type=None, ask=False):
        """
        Synchronizes all latest published files for current asset
        :param file_type: str, if not given all files will be synced
        """

        valid_types = self._get_types_to_check(file_type)
        if not valid_types:
            return

        for valid_type in valid_types:
            file_type = self.get_file_type(valid_type)
            file_type = self.get_file_type(valid_type)
            if not file_type:
                continue

            latest_published_path = file_type.get_server_versions()

            print(file_type, latest_published_path)

            # print('Syncing: {}'.format(latest_published_path))

    # ==========================================================================================================
    # VERSIONS
    # ==========================================================================================================

    def get_local_versions(self, status=None, file_types=None):
        """
        Returns all local version of the given asset file types and with the given status
        :param status: ArtellaAssetFileStatus
        :param file_types:
        :return:
        """

        if not status:
            status = defines.ARTELLA_SYNC_WORKING_ASSET_STATUS

        valid_types = self._get_types_to_check(file_types)

        local_versions = dict()
        for file_type in valid_types:
            local_versions[file_type] = dict()

        if not self.get_path():
            return local_versions

        for valid_type in valid_types:
            file_type = self.get_file_type(valid_type)
            if not file_type:
                continue
            file_type_versions = file_type.get_local_versions(status=status)
            if not file_type_versions:
                continue
            local_versions[valid_type] = file_type_versions

        return local_versions

    def get_latest_local_versions(self, status=None, file_types=None):
        """
        Returns latest local version of the given asset file types
        :param file_types: list (optional)
        :return: dict
        """

        if not status:
            status = defines.ARTELLA_SYNC_WORKING_ASSET_STATUS

        valid_types = self._get_types_to_check(file_types)

        latest_local_versions = dict()
        for file_type in valid_types:
            latest_local_versions[file_type] = None

        for valid_type in valid_types:
            file_type = self.get_file_type(valid_type)
            if not file_type:
                continue
            file_type_versions = file_type.get_latest_local_versions(status=status)
            if not file_type_versions:
                continue
            latest_local_versions[valid_type] = file_type_versions

        return latest_local_versions

    # ==========================================================================================================
    # SHADERS
    # ==========================================================================================================

    @decorators.abstractmethod
    def get_shading_type(self):
        """
        Returns the asset file type of the shading file for the project
        :return: str
        """

        raise NotImplementedError('get_shading_type must be implemented in extended classes')

    def export_shaders(self):
        """
        Exports shaders of current asset
        This function generates 2 files:
        1. Shader JSON files which are stored inside Shaders Library Path
        2. Asset Shader Description file, which maps the asset geometry to their respective shader
        :return: str
        """

        shading_type = self.get_file_type(self.get_shading_type())
        if not shading_type:
            LOGGER.warning(
                'Impossible to export shaders because shading file type "{}" is not valid!'.format(shading_type))
            return

        valid_open = self.open_file(file_type=shading_type, status=ArtellaAssetFileStatus.WORKING)
        if not valid_open:
            return

        all_shading_groups = list()
        json_data = dict()

    # ==========================================================================================================
    # PRIVATE
    # ==========================================================================================================

    def _get_file_name(self, asset_name, **kwargs):
        """
        Returns asset file name without extension
        :param asset_name: str
        :param kwargs: dict
        :return: str
        """

        return self._project.solve_name('asset_file', asset_name, **kwargs)

    def _get_paths_to_sync(self, file_type, sync_type):
        """
        Internal function that returns a complete list of paths to sync depending on the given file type and sync type
        :param file_type: str
        :param sync_type: str
        :return: list(str)
        """

        valid_types = self._get_types_to_check(file_type)
        if not valid_types:
            return

        paths_to_sync = list()

        for valid_type in valid_types:
            file_type = self.get_file_type(valid_type)
            if not file_type:
                continue

            if sync_type == defines.ARTELLA_SYNC_ALL_ASSET_STATUS or \
                    sync_type == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
                paths_to_sync.append(file_type.get_working_path(sync_folder=True))
            if sync_type == defines.ARTELLA_SYNC_ALL_ASSET_STATUS or \
                    sync_type == defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS:
                paths_to_sync.append(file_type.get_latest_server_published_path(sync_folder=True))

        return paths_to_sync

    def _get_types_to_check(self, file_types=None):
        """
        Returns all file types that should be checked
        :param file_types: list(str) (optional)
        :return: list(str)
        """

        asset_valid_file_types = self.get_valid_file_types()
        if file_types == defines.ARTELLA_SYNC_ALL_ASSET_TYPES:
            file_types = asset_valid_file_types
        else:
            file_types = python.force_list(file_types)
            if not file_types:
                file_types = asset_valid_file_types
            else:
                file_types = [i for i in file_types if i in asset_valid_file_types]

        return file_types


class ArtellaAssetWidget(base.BaseWidget, object):

    ASSET_INFO_CLASS = assetinfo.AssetInfoWidget
    DEFAULT_ICON = resource.ResourceManager().icon('default')
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

        str_icon = self.asset.data[defines.ARTELLA_ASSET_DATA_ATTR].get(
            defines.ARTELLA_ASSET_DATA_ICON_ATTR, None)
        icon_format = self.asset.data[defines.ARTELLA_ASSET_DATA_ATTR].get(
            defines.ARTELLA_ASSET_DATA_ICON_FORMAT_ATTR, None)
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

        sync_icon = resource.ResourceManager().icon('sync')
        artella_icon = resource.ResourceManager().icon('artella')
        eye_icon = resource.ResourceManager().icon('eye')

        artella_action = QAction(artella_icon, 'Open in Artella', context_menu)
        view_locally_action = QAction(eye_icon, 'View Locally', context_menu)
        sync_action = QAction(sync_icon, 'Synchronize', context_menu)
        sync_menu = menu.Menu(self)
        actions_added = self._fill_sync_action_menu(sync_menu)
        artella_action.triggered.connect(self._on_open_in_artella)
        view_locally_action.triggered.connect(self._on_view_locally)

        context_menu.addAction(artella_action)
        context_menu.addAction(view_locally_action)

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
            asset_type_action.triggered.connect(
                partial(self._on_sync, asset_type_name,
                        defines.ARTELLA_SYNC_ALL_ASSET_STATUS, False))
            actions_to_add.append(asset_type_action)

        if actions_to_add:
            download_icon = resource.ResourceManager().icon('download')
            all_action = QAction(download_icon, 'All', sync_menu)
            all_action.triggered.connect(
                partial(self._on_sync,
                        defines.ARTELLA_SYNC_ALL_ASSET_TYPES,
                        defines.ARTELLA_SYNC_ALL_ASSET_STATUS, False))
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

    def _on_view_locally(self):
        """
        Internal callback function that is called when the user presses View Locally contextual menu action
        """

        self._asset.view_locally()

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


class ArtellaTagNode(object):
    def __init__(self, project, node, tag_info=None):
        super(ArtellaTagNode, self).__init__()

        self._project = project
        self._node = node
        self._tag_info_dict = tag_info

        if tag_info:
            self._tag_info_dict = ast.literal_eval(tag_info)
            short_node = tp.Dcc.node_short_name(node)
            if short_node in self._tag_info_dict.keys():
                self._tag_info_dict = self._tag_info_dict[short_node]
            else:
                short_node_strip = short_node.rstrip(string.digits)
                if short_node_strip in self._tag_info_dict.keys():
                    self._tag_info_dict = self._tag_info_dict[short_node_strip]

    @property
    def node(self):
        """
        Returns linked to the tag node
        :return: str
        """

        return self._node

    @property
    def tag_info(self):
        """
        Returns tag info data stored in this node
        :return: dict
        """

        return self._tag_info_dict

    def get_clean_node(self):
        """
        Returns current node with the short name and with ids removed
        :return: str
        """

        return tp.Dcc.node_short_name(self._node).rstrip(string.digits)

    def get_asset_node(self):
        """
        Returns asset node linked to this tag node
        :return: ArtellaAssetNode
        """

        if not self._node or not tp.Dcc.object_exists(self._node):
            return None

        if self._tag_info_dict:
            return self._project.ASSET_NODE_CLASS(project=self._project, node=self._node)
        else:
            if not tp.Dcc.attribute_exists(node=self._node, attribute_name=tagger_defines.NODE_ATTRIBUTE_NAME):
                return None
            connections = tp.Dcc.list_connections(node=self._node, attribute_name=tagger_defines.NODE_ATTRIBUTE_NAME)
            if connections:
                node = connections[0]
                return self._project.ASSET_NODE_CLASS(project=self._project, node=node)

        return None

    def get_tag_type(self):
        """
        Returns the type of the tag
        :return: str
        """

        return self._get_attribute(attribute_name=tagger_defines.TAG_TYPE_ATTRIBUTE_NAME)

    def _get_attribute(self, attribute_name):
        """
        Internal function that retrieves attribute from wrapped TagData node
        :param attribute_name: str, attribute name to retrieve from TagData node
        :return: variant
        """

        if self._tag_info_dict:
            return self._tag_info_dict.get(attribute_name)
        else:
            if not self._node or not tp.Dcc.object_exists(self._node):
                return None
            if not tp.Dcc.attribute_exists(node=self._node, attribute_name=attribute_name):
                return None

            return tp.Dcc.get_attribute_value(node=self._node, attribute_name=attribute_name)
