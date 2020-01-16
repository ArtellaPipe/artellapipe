#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract definitions for some classes for Artella Pipeline
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

import tpDccLib as tp
from tpPyUtils import decorators, python, osplatform, path as path_utils
from tpQtLib.core import qtutils

import artellapipe
from artellapipe.core import defines
from artellapipe.libs import artella
from artellapipe.libs.artella.core import artellalib

LOGGER = logging.getLogger()


class AbstractFile(object):

    FILE_TYPE = None
    FILES = dict()

    def __init__(self, project):
        super(AbstractFile, self).__init__()

        self._project = project

    # ==========================================================================================================
    # PROPERTIES
    # ==========================================================================================================

    @property
    def project(self):
        """
        Returns project linked to this assset
        :return: ArtellaProject
        """

        return self._project

    # ==========================================================================================================
    # ABSTRACT
    # ==========================================================================================================

    @decorators.abstractmethod
    def get_id(self):
        """
        Returns the ID of the sequence
        :return: str
        """

        raise NotImplementedError('get_id function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_name(self):
        """
        Returns the name of the asset
        :return: str
        """

        raise NotImplementedError('get_name function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_template_dict(self, extension):
        """
        Returns the dict that contains necessary data to retrieve file template
        :param extension: str
        :return: dict
        """

        raise NotImplementedError(
            'get_template_dict function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_path(self):
        """
        Returns the path of the asset
        :return: str
        """

        raise NotImplementedError('get_path function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_thumbnail_path(self):
        """
        Returns the path where thumbnail path is located
        :return: str
        """

        raise NotImplementedError(
            'get_thumbnail_path function for {} is not implemented!'.format(self.__class__.__name__))

    def get_file_type(self, file_type, extension=None):
        """
        Returns file object of the current asset and given file type
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        raise NotImplementedError('get_file_type function for {} is not implemented!'.format(self.__class__.__name__))

    # ==========================================================================================================
    # BASE
    # ==========================================================================================================

    def get_relative_path(self):
        """
        Returns path of the asset relative to the Artella project
        :return: str
        """

        return os.path.relpath(self.get_path(), self._project.get_path())

    def is_available(self):
        """
        Returns whether or not asset is available locally or not
        :return: bool
        """

        asset_path = self.get_path()
        if not asset_path:
            return False

        return os.path.isdir(asset_path)

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

    # ==========================================================================================================
    # FILES
    # ==========================================================================================================

    def get_valid_file_types(self):
        """
        Returns a list with all valid file types of current asset
        :return: list(str)
        """

        return [i for i in self.FILES if i in artellapipe.FilesMgr().files]

    def get_file(self,
                 file_type, status, extension=None, version=None, fix_path=False, only_local=False, extra_dict=None):
        """
        Returns file path of the given file type and status
        :param file_type: str
        :param status: str
        :param extension: str
        :param version: str
        :param fix_path: str
        :param only_local: bool
        :param extra_dict: dict,
        :return:
        """

        if extra_dict is None:
            extra_dict = dict()

        if not extension:
            extensions = artellapipe.FilesMgr().get_file_type_extensions(file_type)
            if extensions:
                extension = extensions[0]
            else:
                extension = self.project.default_extension

        available_files_types = artellapipe.FilesMgr().files
        if file_type not in available_files_types:
            LOGGER.warning(
                'File Type "{}" is not valid! Supported File Types: {}'.format(file_type, available_files_types.keys()))
            return None
        if not defines.ArtellaFileStatus.is_valid(status):
            LOGGER.warning('Given File Artella Sync Status: {} is not valid! Supported Statuses: {}'.format(
                status, defines.ArtellaFileStatus.supported_statuses()))
            return None

        file_template_name = available_files_types[file_type].get('template', file_type.lower())
        template = artellapipe.FilesMgr().get_template(file_template_name)
        if not template:
            LOGGER.warning(
                'Impossible to retrieve file path because template "{}" is not in configuration file'.format(
                    file_template_name))
            return None

        file_name = self.get_name()
        template_dict = self.get_template_dict(extension=extension)

        if status == defines.ArtellaFileStatus.WORKING:
            template_dict['version_folder'] = artella.config.get('server', 'working_folder')
            template_dict.update(extra_dict)
            file_path = template.format(template_dict)
        else:
            latest_local_versions = self.get_latest_local_versions(
                status=defines.ArtellaFileStatus.PUBLISHED)
            file_type_local_versions = latest_local_versions.get(file_type, None)
            if file_type_local_versions:
                if version:
                    if version == file_type_local_versions[1]:
                        template_dict['version_folder'] = version
                    else:
                        if only_local:
                            LOGGER.warning(
                                'No local version "{}" found in Asset "{}" for File Type: "{}"'.format(
                                    version, file_name, file_type))
                            return None
                        else:
                            template_dict['version_folder'] = version

                else:
                    template_dict['version_folder'] = file_type_local_versions[1]
            else:
                if not version:
                    LOGGER.warning(
                        'No local versions found in Asset "{}" for File Type: "{}"'.format(file_name, file_type))
                    return None
                else:
                    template_dict['version_folder'] = version

            template_dict.update(extra_dict)

            file_path = template.format(template_dict)

        if not file_path:
            raise RuntimeError('Impossible to retrieve file because asset path for "{}" is not valid!'.format(
                file_name
            ))

        if fix_path:
            file_path = artellapipe.FilesMgr().fix_path(file_path)

        return file_path

    def open_file(self, file_type, status, extension=None, fix_path=True):
        """
        Opens asset file with the given type and status (if exists)
        :param file_type: str

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
            if path_utils.clean_path(tp.Dcc.scene_name()) == path_utils.clean_path(file_path):
                return True
            tp.Dcc.open_file(file_path)
            return True
        elif os.path.isdir(file_path):
            osplatform.open_folder(file_path)
        else:
            LOGGER.warning('Impossible to open file of type "{}": {}'.format(file_type, file_path))

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

    def supports_file_type(self, file_type, status=defines.ArtellaFileStatus.ALL):
        """
        Returns whether or not current asset supports given file type
        :param file_type: str, type of asset file.
        :param status: type of sync (working, published or all)
        :return: bool
        """

        if status != defines.ArtellaFileStatus.ALL:
            if status not in self.FILES:
                LOGGER.warning(
                    'Impossible to sync "{}" because current Asset {} does not support it!'.format(
                        file_type, self.__class__.__name__))
                return False
            if status not in self.project:
                LOGGER.warning(
                    'Impossible to sync "{}" because project "{}" does not support it!'.format(
                        file_type, self.project.name.title()))
                return False

        return True

    # ==========================================================================================================
    # ARTELLA
    # ==========================================================================================================

    def get_artella_url(self):
        """
        Returns Artella URL of the file
        :return: str
        """

        assets_relative_path = os.path.relpath(self.get_path(), artellapipe.AssetsMgr().get_assets_path())
        assets_url = self._project.get_artella_assets_url()
        artella_url = '{}{}'.format(assets_url, assets_relative_path)

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
    # SYNC
    # ==========================================================================================================

    @decorators.timestamp
    def is_published(self, file_type=None):
        """
        Returns whether or not current asset and given type is published
        :param file_type: str, type of asset file. If None, True will be returned if any fiel type is published
        :return: bool
        """

        valid_types = self._get_types_to_check(file_type)
        if not valid_types:
            return

        for valid_type in valid_types:
            file_type = self.get_file_type(valid_type)
            if not file_type:
                continue

            latest_published_info = file_type.get_server_versions(status=defines.ArtellaFileStatus.PUBLISHED)
            if not latest_published_info:
                return False
            for version_info in latest_published_info:
                latest_version_path = version_info.get('version_path', None)
                if not latest_version_path:
                    return False

            return True

    @decorators.timestamp
    def sync(self, file_type=None, sync_type=defines.ArtellaFileStatus.ALL):
        """
        Synchronizes asset file type and with the given sync type (working or published)
        :param file_type: str, type of asset file. If None, all asset file types will be synced
        :param sync_type: str, type of sync (working, published or all)
        """

        if not self.supports_file_type(file_type=file_type, status=sync_type):
            return

        paths_to_sync = self._get_paths_to_sync(file_type, sync_type)
        if not paths_to_sync:
            LOGGER.warning('No Paths to sync for "{}"'.format(self.get_name()))
            return

        artellapipe.FilesMgr().sync_paths(paths_to_sync, recursive=True)

    @decorators.timestamp
    def sync_latest_published_files(self, file_type=None, ask=False):
        """
        Synchronizes all latest published files for current asset
        :param file_type: str, if not given all files will be synced
        """

        if ask:
            result = qtutils.show_question(
                None, 'Synchronizing Latest Published Files: {}'.format(self.get_name()),
                'Are you sure you want to synchronize latest published files? This can take quite some time!')
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
    # INTERNAL
    # ==========================================================================================================

    def _get_types_to_check(self, file_types=None):
        """
        Returns all file types that should be checked
        :param file_types: list(str) (optional)
        :return: list(str)
        """

        asset_valid_file_types = self.get_valid_file_types()
        if not file_types or file_types == defines.ArtellaFileStatus.ALL:
            file_types = asset_valid_file_types
        else:
            file_types = python.force_list(file_types)
            file_types = [i for i in file_types if i in asset_valid_file_types]

        return file_types

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
                working_path = file_type.get_working_path(sync_folder=True)
                if working_path and working_path not in paths_to_sync:
                    paths_to_sync.append(working_path)
            if sync_type == defines.ArtellaFileStatus.ALL or sync_type == defines.ArtellaFileStatus.PUBLISHED:
                published_path = file_type.get_latest_server_published_path(sync_folder=True)
                if published_path and published_path not in paths_to_sync:
                    paths_to_sync.append(published_path)

        return paths_to_sync


class AbstractAsset(AbstractFile, object):
    def __init__(self, project, asset_data, node=None):
        super(AbstractAsset, self).__init__(project=project)

        self._asset_data = asset_data
        self._node = node

    # ==========================================================================================================
    # PROPERTIES
    # ==========================================================================================================

    @property
    def data(self):
        """
        Returns asset data
        :return: object
        """

        return self._asset_data

    @property
    def node(self):
        """
        Returns DCC node linked to this asset
        :return: str
        """

        return self._node

    # ==========================================================================================================
    # ABSTRACTS
    # ==========================================================================================================

    @decorators.abstractmethod
    def get_tags(self):
        """
        Returns tags of the asset
        :return: list(str)
        """

        raise NotImplementedError('get_tags function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_category(self):
        """
        Returns the category of the asset
        :return: str
        """

        raise NotImplementedError('get_category function for {} is not implemented!'.format(self.__class__.__name__))

    # ==========================================================================================================
    # IMPLEMENT
    # ==========================================================================================================

    def get_template_dict(self, extension):
        """
        Returns the dict that contains necessary data to retrieve file template
        :return: dict
        """

        asset_name = self.get_name()

        template_dict = {
            'project_path': self._project.get_path(),
            'asset_name': asset_name,
            'asset_type': self.get_category(),
            'file_extension': extension
        }

        return template_dict

    def get_file_type(self, file_type, extension=None):
        """
        Returns asset file object of the current asset and given file type
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        if file_type not in self.FILES:
            return None

        asset_file_class = artellapipe.AssetsMgr().get_asset_file(file_type=file_type, extension=extension)
        if not asset_file_class:
            LOGGER.warning('File Type: {} | {} not registered in current project!'.format(file_type, extension))
            return

        return asset_file_class(asset=self)


class AbstractSequence(AbstractFile, object):

    def __init__(self, project, sequence_data):
        super(AbstractSequence, self).__init__(project=project)

        self._sequence_data = sequence_data

    @property
    def data(self):
        """
        Returns sequence data
        :return: object
        """

        return self._sequence_data

    # ==========================================================================================================
    # IMPLEMENT
    # ==========================================================================================================

    def get_template_dict(self, **kwargs):
        """
        Returns the dict that contains necessary data to retrieve file template
        :return: dict
        """

        sequence_name = self.get_name()

        template_dict = {
            'project_path': self._project.get_path(),
            'sequence_name': sequence_name,
            'file_extension': kwargs.get('extension', None),
            'version_folder': kwargs.get('version_folder', defines.ArtellaFileStatus.WORKING)
        }

        return template_dict

    def get_file_type(self, file_type, extension=None):
        """
        Returns sequence file object of the current sequence and given file type
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        if file_type not in self.FILES:
            return None

        sequence_file_class = artellapipe.SequencesMgr().get_sequence_file(file_type=file_type, extension=extension)
        if not sequence_file_class:
            LOGGER.warning('File Type: {} | {} not registered in current project!'.format(file_type, extension))
            return

        return sequence_file_class(sequence=self)


class AbstractShot(AbstractFile, object):
    def __init__(self, project, shot_data):
        super(AbstractShot, self).__init__(project=project)

        self._shot_data = shot_data

    @property
    def data(self):
        """
        Returns shot data
        :return: object
        """

        return self._shot_data

    @decorators.abstractmethod
    def get_id(self):
        """
        Returns the ID of the shot
        :return: str
        """

        raise NotImplementedError('get_id function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_thumbnail_path(self):
        """
        Returns the path where thumbnail path is located
        :return: str
        """

        raise NotImplementedError(
            'get_thumbnail_path function for {} is not implemented!'.format(self.__class__.__name__))
