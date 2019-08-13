#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for asset types
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from tpPyUtils import decorators, path as path_utils

from artellapipe.core import defines, artellalib


class ArtellaAssetType(object):

    FILE_TYPE = None
    FILE_EXTENSIONS = list()

    def __init__(self, asset):

        self._asset = asset

        self._history = None
        self._working_status = None
        self._working_history = None
        self._latest_server_version = {
            defines.ARTELLA_SYNC_WORKING_ASSET_STATUS: None,
            defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS: None
        }

        super(ArtellaAssetType, self).__init__()

    def open_file(self, status):
        """
        References current file into DCC
        :return:
        """

        if status == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
            file_path = self._get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        self._open_file(path=file_path)

    def import_file(self, status):
        """
        References current file into DCC
        :return:
        """

        if status == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
            file_path = self._get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        self._import_file(path=file_path)

    def reference_file(self, status, resolve_path=True):
        """
        References current file into DCC
        :param status: str
        :param resolve_path: bool
        :return:
        """

        if status == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
            file_path = self._get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        self._reference_file(path=file_path, resolve_path=resolve_path)

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
        :param status: ArtellaAssetFileStatus
        :param force_update: bool
        :return:
        """

        if self._history and not force_update:
            return self._history

        self._history = self._get_history(status=status)

        return self._history

    def get_working_path(self):
        """
        Returns working path to the file
        :return: str
        """

        asset_name = self.asset.get_name()
        asset_path = self.asset.get_path()

        return self._get_working_path(asset_name=asset_name, asset_path=asset_path)

    def get_latest_local_published_path(self):
        """
        Returns path to the latest published file
        :return: str
        """

        latest_Local_versions = self.get_latest_local_versions(status=defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS)
        if not latest_Local_versions:
            return

        asset_name = self.asset.get_name()
        asset_path = self.asset.get_path()
        version_folder = latest_Local_versions[1]
        published_path = self._get_published_path(asset_name=asset_name, asset_path=asset_path, version_folder=version_folder)

        return path_utils.clean_path(published_path)

    def get_latest_local_published_version(self):
        """
        Returns latest published version
        :return: str
        """

        latest_Local_versions = self.get_latest_local_versions(status=defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS)

        return latest_Local_versions


    def get_latest_published_version(self):
        """
        Returns latest published version in Artella server
        :return: str
        """

        pass

    def get_local_versions(self, status=None):
        """
        Returns all local version of the current file type in the wrapped asset
        :param status: ArtellaAssetFileStatus
        :return:
        """

        if not status:
            status = defines.ARTELLA_SYNC_WORKING_ASSET_STATUS

        local_versions = dict()

        asset_path = self.asset.get_path()
        if not asset_path:
            return local_versions

        for p in os.listdir(asset_path):
            if status == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
                if p != defines.ARTELLA_WORKING_FOLDER:
                    continue
                for f in os.listdir(os.path.join(asset_path, defines.ARTELLA_WORKING_FOLDER)):
                    if f != self.FILE_TYPE:
                        continue
                    # self.get_working_files_for_file_type(self.FILE_TYPE)
            else:
                if p == defines.ARTELLA_WORKING_FOLDER:
                    continue
                if self.FILE_TYPE in p:
                    version = artellalib.get_asset_version(p)
                    if version:
                        local_versions[str(version[1])] = p

        return local_versions

    def get_latest_local_versions(self, status=None):
        """
        Returns latest local version of the given asset file types
        :param status: str
        :return: dict
        """

        if not status:
            status = defines.ARTELLA_SYNC_WORKING_ASSET_STATUS

        latest_local_versions = dict()

        local_versions = self.get_local_versions(status=status)

        for version, version_folder in local_versions.items():
            if not latest_local_versions:
                latest_local_versions = [int(version), version_folder]
            else:
                if int(latest_local_versions[0]) < int(version):
                    latest_local_versions = [int(version), version_folder]

        return latest_local_versions

    @decorators.timestamp
    def get_server_versions(self, status=None, all_versions=True, force_update=False):
        """
        Returns all server version of the current file type in the wrapped asset
        :param status: ArtellaAssetFileStatus
        :param all_versions: bool, Whether to return all server versions of the file or only the latest one
        :param force_update: bool, Whether to update Artella data or not (this can take time)
        :return:
        """

        working_data = list()

        if not status:
            status = defines.ARTELLA_SYNC_WORKING_ASSET_STATUS

        if not force_update and self._latest_server_version.get(status):
            return self._latest_server_version[status]

        if status == defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS:
            self._get_published_server_versions(all_versions=all_versions, force_update=force_update)
        else:
            asset_path = self.asset.get_path()
            if not asset_path:
                return

            working_path = os.path.join(asset_path, defines.ARTELLA_WORKING_FOLDER, self.FILE_TYPE)

            if not force_update and self._working_status:
                status = self._working_status
            else:
                status = artellalib.get_status(working_path)

            if hasattr(status, 'references'):
                for ref_name, ref_data in status.references.items():
                    server_data = self._get_working_server_versions(working_path=working_path, artella_data=ref_data, force_update=force_update)
                    working_data.append(server_data)

        return working_data

    def get_extension(self):
        """
        Returns the extension of the aseet file
        :return: str
        """

        return self.get_project().assets_library_file_types.get()

    def _get_history(self, status):
        """
        Internal function that returns the history of the aset files
        Overrides in custom file types if necessary
        :param status: ArtellaAssetFileStatus
        :return:
        """

        asset_name = self._asset.get_name()
        asset_path = self._asset.get_path()
        file_path = os.path.join(asset_path, defines.ARTELLA_WORKING_FOLDER, self.FILE_TYPE, asset_name+self.FILE_EXTENSIONS[0])
        history = artellalib.get_asset_history(file_path=file_path)

        return history

    def _get_working_path(self, asset_name, asset_path):
        """
        Internal function that returns working path of the current asset file
        :param asset_name: str
        :param asset_path: str
        :return: str
        """

        return os.path.join(asset_path, defines.ARTELLA_WORKING_FOLDER, self.FILE_TYPE, asset_name+self.FILE_EXTENSIONS[0])

    def _get_published_path(self, asset_name, asset_path, version_folder):
        """
        Intenal function that returns published path of the current asset file
        Overrides to return specific paths in custom file types
        :param asset_name: str
        :param asset_path: str
        :param version_folder: str
        :return: str
        """

        return os.path.join(asset_path, version_folder, self.FILE_TYPE, asset_name+self.FILE_EXTENSIONS[0])

    def _get_published_server_versions(self, all_version=True, force_update=False):
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
        print('Published Versions: {}'.format(published_versions))

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
                    return artellalib.get_asset_history(ref_path)
                break

    def _open_file(self, path, resolve_path=True):
        """
        Internal function that opens current file in DCC
        Overrides in custom asset file
        :param path: str
        :param resolve_path: bool
        :return:
        """

        pass

    def _import_file(self, path, resolve_path=True):
        """
        Internal function that imports current file in DCC
        Overrides in custom asset file
        :param path: str
        :param resolve_path: bool
        :return:
        """

        pass

    def _reference_file(self, path, resolve_path=True):
        """
        Internal function that references current file in DCC
        Overrides in custom asset file
        :param path: str
        :param resolve_path: bool
        :return:
        """

        pass
