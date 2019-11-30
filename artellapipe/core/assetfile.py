#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for asset files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

from tpPyUtils import decorators, path as path_utils
from tpQtLib.core import qtutils

import artellapipe
from artellapipe.core import defines, file
from artellapipe.libs import artella
from artellapipe.libs.artella.core import artellalib

LOGGER = logging.getLogger()


class ArtellaAssetFile(file.ArtellaFile, object):
    def __init__(self, file_asset=None):

        self._asset = file_asset

        super(ArtellaAssetFile, self).__init__(file_name=self._asset.get_name() if self._asset else None)

    def open_file(self, status):
        """
        References current file into DCC
        :return:
        """

        if status == defines.ArtellaFileStatus.WORKING:
            file_path = self.get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        self._open_file(path=file_path)

    # def import_file(self, status, fix_path=True, sync=False, *args, **kwargs):
    #     """
    #     References current file into DCC
    #     :return:
    #     """
    #
    #     file_path = self._get_path(status=status, fix_path=fix_path)
    #
    #     valid_path = self._check_path(file_path, sync=sync)
    #     if not valid_path:
    #         msg = 'Impossible to import asset file of type "{}". File Path "{}" does not exists!'.format(
    #             self.FILE_TYPE, file_path)
    #         LOGGER.warning(msg)
    #         qtutils.warning_message(msg)
    #         return None
    #
    #     self._import_file(path=file_path, *args, **kwargs)

    # def reference_file(self, status, fix_path=True, sync=False, *args, **kwargs):
    #     """
    #     References current file into DCC
    #     :param status: str
    #     :param fix_path: bool
    #     :param sync: bool
    #     :return:
    #     """
    #
    #     valid_path = self._check_path(sync=sync)
    #     if not valid_path:
    #         msg = 'Impossible to reference asset file of type "{}". File Path "{}" does not exists!'.format(
    #             self.FILE_TYPE, self._file_path)
    #         LOGGER.warning(msg)
    #         qtutils.warning_message(msg)
    #         return None
    #
    #     return self._reference_file(file_path=self._file_path, status=status, sync=sync, *args, **kwargs)

    @property
    def asset(self):
        """
        Returns asset linked to this file type
        :return: ArtellaAssset
        """

        return self._asset

    def get_project(self):
        """
        Returns project where this asset file belongs to
        :return: ArtellaProject
        """

        return self._asset.project

    def get_history(self, status, force_update=False):
        """
        Returns the history of the asset files
        :param status: ArtellaFileStatus
        :param force_update: bool
        :return:
        """

        if self._history and not force_update:
            return self._history

        self._history = self._get_history(status=status)

        return self._history

    def get_working_path(self, sync_folder=False):
        """
        Returns working path to the file
        :return: str
        """

        working_path = self.asset.get_file(
            file_type=self.FILE_TYPE, status=defines.ArtellaFileStatus.WORKING,
            extension=self.FILE_EXTENSIONS[0], fix_path=False
        )

        if sync_folder:
            return path_utils.clean_path(os.path.dirname(working_path))

        return path_utils.clean_path(working_path)

    def get_latest_local_published_path(self, sync_folder=False):
        """
        Returns local path to the latest published file
        :return: str
        """

        latest_local_versions = self.get_latest_local_versions(status=defines.ArtellaFileStatus.PUBLISHED)
        if not latest_local_versions:
            return

        version_folder = latest_local_versions[1]

        published_path = self.asset.get_file(
            file_type=self.FILE_TYPE, status=defines.ArtellaFileStatus.PUBLISHED,
            extension=self.FILE_EXTENSIONS[0], fix_path=False, version=version_folder
        )

        if sync_folder:
            return path_utils.clean_path(os.path.dirname(os.path.dirname(published_path)))

        return path_utils.clean_path(published_path)

    def get_latest_local_published_version(self):
        """
        Returns local latest published version
        :return: str
        """

        latest_local_versions = self.get_latest_local_versions(status=defines.ArtellaFileStatus.PUBLISHED)

        return latest_local_versions

    def get_latest_server_published_path(self, sync_folder=False):
        """
        Returns server path to the latest published file
        :return: str
        """

        latest_published_version = self.get_latest_server_published_versions()
        if not latest_published_version:
            return

        version_folder = latest_published_version['version_name']
        if not version_folder.startswith('__'):
            version_folder = '__{}'.format(version_folder)
        if not version_folder.endswith('__'):
            version_folder = '{}__'.format(version_folder)

        published_path = self.asset.get_file(
            file_type=self.FILE_TYPE, status=defines.ArtellaFileStatus.PUBLISHED,
            extension=self.FILE_EXTENSIONS[0], version=version_folder, fix_path=False)

        if sync_folder:
            return path_utils.clean_path(os.path.dirname(os.path.dirname(published_path)))

        return path_utils.clean_path(published_path)

    def get_latest_server_published_versions(self):
        """
        Returns latest published version in Artella server
        :return: str
        """

        latest_server_versions = self.get_latest_server_version(status=defines.ArtellaFileStatus.PUBLISHED)

        return latest_server_versions

    def get_local_versions(self, status=None):
        """
        Returns all local version of the current file type in the wrapped asset
        :param status: ArtellaFileStatus
        :return:
        """

        if not status:
            status = defines.ArtellaFileStatus.WORKING

        local_versions = dict()

        if not self.asset:
            LOGGER.warning('Impossible to retrieve local version because asset is not defined!')
            return local_versions

        asset_path = self.asset.get_path()
        if not asset_path or not os.path.exists(asset_path):
            return local_versions

        file_type_template = artellapipe.FilesMgr().get_template(self.FILE_TYPE)
        if not file_type_template:
            LOGGER.warning(
                'Impossible to retrieve local version because template for "{}" is not in configuration file'.format(
                    self.FILE_TYPE))
            return local_versions

        for extension in self.FILE_EXTENSIONS:

            template_dict = {
                'asset_path': asset_path,
                'asset_name': self._asset.get_name(),
                'file_extension': extension
            }

            folders_to_check = list()
            working_folder = artella.config.get('server', 'working_folder')
            if status == defines.ArtellaFileStatus.PUBLISHED:
                for p in os.listdir(asset_path):
                    if p == working_folder:
                        continue
                    folders_to_check.append(p)

            for folder in folders_to_check:
                template_dict['version_folder'] = folder
                file_path = file_type_template.format(template_dict)
                if file_path and os.path.isfile(file_path):
                    version = artellalib.split_version(folder)
                    if version:
                        local_versions[str(version[1])] = folder

            return local_versions

        return local_versions

    def get_latest_local_versions(self, status=None):
        """
        Returns latest local version of the of the current file type
        :param status: str
        :return: dict
        """

        if not status:
            status = defines.ArtellaFileStatus.WORKING

        latest_local_versions = dict()

        local_versions = self.get_local_versions(status=status)

        for version, version_folder in local_versions.items():
            if not latest_local_versions:
                latest_local_versions = [int(version), version_folder]
            else:
                if int(latest_local_versions[0]) < int(version):
                    latest_local_versions = [int(version), version_folder]

        return latest_local_versions

    def get_latest_server_version(self, status=None):
        """
        Returns latest server version of the current file type
        :param status: str
        :return: dict
        """

        if not status:
            status = defines.ArtellaFileStatus.WORKING

        server_versions = self.get_server_versions(status=status, all_versions=False)
        if not server_versions:
            return None

        latest_server_version = server_versions[0]

        return latest_server_version

    @decorators.timestamp
    def get_server_versions(self, status=None, all_versions=True, force_update=False):
        """
        Returns all server version of the current file type in the wrapped asset
        :param status: ArtellaFileStatus
        :param force_update: bool, Whether to update Artella data or not (this can take time)
        :return:
        """

        result = list()

        if not status:
            status = defines.ArtellaFileStatus.WORKING

        if not force_update and self._latest_server_version.get(status):
            return self._latest_server_version[status]

        asset_path = self.asset.get_path()
        if not asset_path:
            return

        if status == defines.ArtellaFileStatus.PUBLISHED:
            result = artellapipe.AssetsMgr().get_latest_published_versions(asset_path, file_type=self.FILE_TYPE)
        else:
            working_folder = artella.config.get('server', 'working_folder')
            working_path = os.path.join(asset_path, working_folder, self.FILE_TYPE)

            if not force_update and self._working_status:
                status = self._working_status
            else:
                status = artellalib.get_status(working_path)

            if hasattr(status, 'references'):
                for ref_name, ref_data in status.references.items():
                    server_data = self._get_working_server_versions(
                        working_path=working_path, artella_data=ref_data, force_update=force_update)
                    result.append(server_data)

        return result

    def get_extension(self):
        """
        Returns the extension of the aseet file
        :return: str
        """

        return self.get_project().assets_library_file_types.get()

    def get_file_paths(self, return_first=False, fix_path=True, **kwargs):

        if self.FILE_TYPE not in self._asset.ASSET_FILES:
            LOGGER.warning(
                'FileType "{}" is not a valid file for Assets of type "{}"'.format(
                    self.FILE_TYPE, self._asset.ASSET_TYPE))
            return list()

        file_paths = super(
            ArtellaAssetFile, self).get_file_paths(return_first=return_first, fix_path=fix_path, **kwargs)
        if file_paths:
            return file_paths

        status = kwargs.get('status', defines.ArtellaFileStatus.PUBLISHED)
        if status == defines.ArtellaFileStatus.WORKING:
            file_path = self.get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        if not file_path:
            return None if return_first else file_paths

        if fix_path:
            file_path = artellapipe.FilesMgr().fix_path(file_path)

        if return_first:
            return file_path
        else:
            return [file_path]

    # def _get_path(self, path, status=defines.ArtellaFileStatus.PUBLISHED, fix_path=True):
    #     """
    #     Returns asset file path taking into account its status
    #     :param status:
    #     :param fix_path: bool
    #     :return: str
    #     """
    #
    #     file_path = super(ArtellaAssetFile, self)._get_path(path=path)
    #     if file_path:
    #         return file_path
    #
    #     if status == defines.ArtellaFileStatus.WORKING:
    #         file_path = self.get_working_path()
    #     else:
    #         file_path = self.get_latest_local_published_path()
    #
    #     if not file_path:
    #         return None
    #
    #     if fix_path:
    #         file_path = artellapipe.FilesMgr().fix_path(file_path)
    #
    #     return file_path

    # def _check_path(self, sync=False):
    #     """
    #     Returns whether or not given path exists.
    #     :param file_path: str
    #     :param sync: bool
    #     :return: bool
    #     """
    #
    #     if sync or not self._file_path:
    #         self.asset.sync_latest_published_files(file_type=self.FILE_TYPE)
    #
    #     if not self._file_path or not os.path.isfile(self._file_path):
    #         return False
    #
    #     return True

    def _get_history(self, status):
        """
        Internal function that returns the history of the aset files
        Overrides in custom file types if necessary
        :param status: ArtellaFileStatus
        :return:
        """

        asset_name = self._asset.get_name()
        asset_path = self._asset.get_path()
        working_folder = artella.config.get('server', 'working_folder')
        file_path = os.path.join(asset_path, working_folder, self.FILE_TYPE, asset_name + self.FILE_EXTENSIONS[0])
        history = artellalib.get_file_history(file_path=file_path)

        return history

    def _get_published_server_versions(self, all_versions=True, force_update=False):
        """
        Internal function that returns all the published server versions of the current file type in the wrapped asset
        Overrides to implement custom functionality
        :param all_versions: bool, Whether to return all server versions of the file or only the latest one
        :param force_update: bool, Whether to update Artella data or not (this can take time)
        :return:
        """

        artella_data = self.asset.get_artella_data(force_update=force_update)
        if not artella_data:
            return
        published_versions = artella_data.get_published_versions(all=all_versions)

        return published_versions

    def _get_working_server_versions(self, working_path, artella_data, force_update=False):
        """
        Internal function that returns all the working server versions of the current file type in the wrapped asset
        Overrides to implement custom functionality
        :param working_path: str, working path in Artella server
        :param artella_data: ArtellaReferencesMetaData
        :param force_update: bool, Whether to update Artella data or not (this can take time)
        :return:
        """

        if not artella_data:
            return

        asset_name = self._asset.get_name()
        ref_path = os.path.join(working_path, artella_data.name)
        file_name = os.path.basename(ref_path)
        for extension in self.FILE_EXTENSIONS:
            if file_name == '{}{}'.format(asset_name, extension):
                if not force_update and self._working_history:
                    return self._working_history
                else:
                    return artellalib.get_file_history(ref_path)
                break
