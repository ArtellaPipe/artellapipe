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
import logging
import webbrowser

from Qt.QtWidgets import *

from tpPyUtils import python, decorators, osplatform
from tpQtLib.core import qtutils

import artellapipe.register
from artellapipe.core import abstract, defines
from artellapipe.utils import resource
from artellapipe.libs import artella
from artellapipe.libs.artella.core import artellalib

LOGGER = logging.getLogger()


class ArtellaAsset(abstract.AbstractAsset, object):

    ASSET_TYPE = None
    ASSET_FILES = dict()

    def __init__(self, project, asset_data, node=None):

        self._artella_data = None

        super(ArtellaAsset, self).__init__(project=project, asset_data=asset_data, node=node)

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

    def get_id(self):
        """
        Implements abstract get_id function
        Returns the id of the asset
        :return: str
        """

        id_attr = artellapipe.AssetsMgr().config.get('data', 'id_attribute')
        asset_id = self._asset_data.get(id_attr, None)
        if not asset_id:
            LOGGER.warning(
                'Impossible to retrieve asset ID because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(id_attr, self._asset_data))
            return None

        return asset_id.rstrip()

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the asset
        :return: str
        """

        name_attr = artellapipe.AssetsMgr().config.get('data', 'name_attribute')
        asset_name = self._asset_data.get(name_attr, None)
        if not asset_name:
            LOGGER.warning(
                'Impossible to retrieve asset name because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(name_attr, self._asset_data))
            return None

        return asset_name.rstrip()

    def get_path(self):
        """
        Implements abstract get_path function
        Returns the path of the asset
        :return: str
        """

        path_template_name = artellapipe.AssetsMgr().config.get('data', 'path_template_name')
        template = artellapipe.FilesMgr().get_template(path_template_name)
        if not template:
            LOGGER.warning(
                'Impossible to retrieve asset path because template "{}" is not in configuration file'.format(
                    path_template_name))
            return None

        template_dict = {
            'project_path': self._project.get_path(),
            'asset_type': self.get_category(),
            'asset_name': self.get_name()
        }
        asset_path = template.format(template_dict)

        if not asset_path:
            LOGGER.warning(
                'Impossible to retrieve asset path from template: "{} | {} | {}"'.format(
                    template.name, template.pattern, template_dict))
            return None

        return asset_path

    def get_thumbnail_path(self):
        """
        Implements abstract get_path function
        Returns the path of the asset
        :return: str
        """

        thumb_attr = artellapipe.AssetsMgr().config.get('data', 'thumb_attribute')

        thumb_path = self._asset_data.get(thumb_attr, None)
        # if not thumb_path:
        #     LOGGER.warning(
        #         'Impossible to retrieve thumb path because asset data does not contains "{}" attribute.'
        #         '\nAsset Data: {}'.format(thumb_attr, self._asset_data))

        return thumb_path

    def get_category(self):
        """
        Implements abstract get_category function
        Returns the category of the asset
        :return: str
        """

        category_attr = artellapipe.AssetsMgr().config.get('data', 'category_attribute')

        category = self._asset_data.get(category_attr, None)
        if not category:
            LOGGER.warning(
                'Impossible to retrieve asset category because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(category_attr, self._asset_data))

        return category

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

        asset_file_class = artellapipe.AssetsMgr().get_asset_file(file_type=file_type, extension=extension)
        if not asset_file_class:
            LOGGER.warning('File Type: {} | {} not registered in current project!'.format(file_type, extension))
            return

        return asset_file_class(asset=self)

    def view_locally(self):
        """
        Opens folder where item is located locally
        """

        asset_path = self.get_path()
        if not os.path.isdir(asset_path):
            LOGGER.warning(
                'Impossible to open asset path locally because path for Asset "{}" : "{}" does not exists!'.format(
                    self.get_name(), asset_path
                ))
            return None

        artellalib.explore_file(self.get_path())

    def get_valid_file_types(self):
        """
        Returns a list with all valid file types of current asset
        :return: list(str)
        """

        return [i for i in self.ASSET_FILES if i in artellapipe.FilesMgr().files]

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
        if not artella_url:
            LOGGER.warning('Impossible to open Artella URL for asset "{}" : "{}"'.format(self.get_name(), artella_url))
            return None

        webbrowser.open(artella_url)

    # ==========================================================================================================
    # FILES
    # ==========================================================================================================

    def get_file(self, file_type, status, extension=None, version=None, fix_path=False):
        """
        Returns file path of the given file type and status
        :param file_type: str
        :param status: str
        :param extension: str
        :param fix_path: str
        """

        if not extension:
            extension = self.project.default_extension

        asset_files = artellapipe.FilesMgr().files
        if file_type not in asset_files:
            LOGGER.warning(
                'File Type "{}" is not valid! Supported File Types: {}'.format(file_type, asset_files.keys()))
            return None
        if not defines.ArtellaFileStatus.is_valid(status):
            LOGGER.warning('Given File Artella Sync Status: {} is not valid! Supported Statuses: {}'.format(
                status, defines.ArtellaFileStatus.supported_statuses()))
            return None

        file_template_name = file_type.lower()
        template = artellapipe.FilesMgr().get_template(file_template_name)
        if not template:
            LOGGER.warning(
                'Impossible to retrieve asset file path because template "{}" is not in configuration file'.format(
                    file_template_name))
            return None

        template_dict = {
            'asset_path': self.get_path(),
            'asset_name': self.get_name(),
            'file_extension': extension
        }

        asset_name = self.get_name()
        if status == defines.ArtellaFileStatus.WORKING:
            template_dict['version_folder'] = artella.config.get('server', 'working_folder')
            file_path = template.format(template_dict)
        else:
            latest_local_versions = self.get_latest_local_versions(
                status=defines.ArtellaFileStatus.PUBLISHED)
            file_type_local_versions = latest_local_versions.get(file_type, None)
            if not file_type_local_versions:
                LOGGER.warning(
                    'No local versions found in Asset "{}" for File Type: "{}"'.format(asset_name, file_type))
                return None
            if version:
                if version == file_type_local_versions[1]:
                    template_dict['version_folder'] = version
                else:
                    LOGGER.warning(
                        'No local version "{}" found in Asset "{}" for File Type: "{}"'.format(asset_name, file_type))
                    return None
            else:
                template_dict['version_folder'] = file_type_local_versions[1]

            file_path = template.format(template_dict)

        if not file_path:
            raise RuntimeError('Impossible to retrieve file because asset path for "{}" is not valid!'.format(
                asset_name
            ))

        if fix_path:
            file_path = artellapipe.FilesMgr().fix_path(file_path)

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
                file_path = artellapipe.FilesMgr().fix_path(file_path)
            artellalib.open_file_in_maya(file_path)
            return True
        elif os.path.isdir(file_path):
            osplatform.open_folder(file_path)
        else:
            LOGGER.warning('Impossible to open asset file of type "{}": {}'.format(file_type, file_path))

        return False

    def import_file_by_extension(self, status=None, extension=None, file_type=None, sync=False, reference=False):
        """
        Implements base AbstractAsset reference_file_by_extension function
        References asset file with the given extension
        :param status: str
        :param extension: bool
        :param file_type: bool
        :param sync: bool
        :param reference: bool
        """

        if not status:
            status = defines.ArtellaFileStatus.PUBLISHED

        available_extensions = self._project.extensions
        if extension not in available_extensions:
            LOGGER.warning('Impossible to reference file with extension "{}". Supported extensions: {}'.format(
                extension, available_extensions
            ))
            return False

        file_types = artellapipe.FilesMgr().get_file_types_by_extension(extension)
        if not file_types:
            LOGGER.warning(
                'Impossible to reference file by its extension ({}) because no file types are registered!'.format(
                    extension))
            return False

        if len(file_types) > 1 and not file_type:
            LOGGER.warning(
                'Multiple file types found with extension: {}. Do not know which file should imported!'.format(
                    extension))
            return False
        elif len(file_types) == 1:
            file_type_to_import = file_types[0]
            if reference:
                file_type_to_import(self).import_file(status=status, sync=sync, reference=True)
            else:
                file_type_to_import(self).import_file(status=status, sync=sync, reference=False)

        for ft in file_types:
            if ft.FILE_TYPE != file_type:
                continue
            if reference:
                return ft(self).import_file(sync=sync, reference=True)
            else:
                return ft(self).import_file(sync=sync, reference=False)

    # ==========================================================================================================
    # SYNC
    # ==========================================================================================================

    @decorators.timestamp
    def sync(self, file_type=None, sync_type=defines.ArtellaFileStatus.ALL):
        """
        Synchronizes asset file type and with the given sync type (working or published)
        :param file_type: str, type of asset file. If None, all asset file types will be synced
        :param sync_type: str, type of sync (working, published or all)
        """

        if sync_type != defines.ArtellaFileStatus.ALL:
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

        artellapipe.FilesMgr().sync_files(files=paths_to_sync)

    @decorators.timestamp
    def sync_latest_published_files(self, file_type=None, ask=False):
        """
        Synchronizes all latest published files for current asset
        :param file_type: str, if not given all files will be synced
        """

        if ask:
            result = qtutils.show_question(
                None, 'Synchronizing Latest Published Files: {}'.format(self.get_name()),
                'Are you sure you want to synchronize latest publishe files? This can take quite some time!')
            if result == QMessageBox.No:
                return

        valid_types = self._get_types_to_check(file_type)
        if not valid_types:
            return

        files_to_sync = list()

        for valid_type in valid_types:
            file_type = self.get_file_type(valid_type)
            if not file_type:
                continue

            latest_published_info = file_type.get_server_versions(status=defines.ArtellaFileStatus.PUBLISHED)
            if not latest_published_info:
                continue
            for version_info in latest_published_info:
                latest_version_path = version_info.get('version_path', None)
                if not latest_version_path:
                    continue

                # We do not get latest of the file already exists
                if os.path.isfile(latest_version_path):
                    continue
                if os.path.isdir(latest_version_path):
                    if not len(os.listdir(latest_version_path)) == 0:
                        continue

                files_to_sync.append(latest_version_path)

        if files_to_sync:
            artellapipe.FilesMgr().sync_files(files_to_sync)

        return files_to_sync

    # ==========================================================================================================
    # VERSIONS
    # ==========================================================================================================

    def get_local_versions(self, status=None, file_types=None):
        """
        Returns all local version of the given asset file types and with the given status
        :param status: ArtellaFileStatus
        :param file_types:
        :return:
        """

        if not status:
            status = defines.ArtellaFileStatus.WORKING

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
            status = defines.ArtellaFileStatus.WORKING

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

        valid_open = self.open_file(file_type=shading_type, status=defines.ArtellaFileStatus.WORKING)
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

            if sync_type == defines.ArtellaFileStatus.ALL or sync_type == defines.ArtellaFileStatus.WORKING:
                paths_to_sync.append(file_type.get_working_path(sync_folder=True))
            if sync_type == defines.ArtellaFileStatus.ALL or sync_type == defines.ArtellaFileStatus.PUBLISHED:
                paths_to_sync.append(file_type.get_latest_server_published_path(sync_folder=True))

        return paths_to_sync

    def _get_types_to_check(self, file_types=None):
        """
        Returns all file types that should be checked
        :param file_types: list(str) (optional)
        :return: list(str)
        """

        asset_valid_file_types = self.get_valid_file_types()
        if not file_types:
            file_types = asset_valid_file_types
        else:
            file_types = python.force_list(file_types)
            file_types = [i for i in file_types if i in asset_valid_file_types]

        return file_types


artellapipe.register.register_class('Asset', ArtellaAsset)
