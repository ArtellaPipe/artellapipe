#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

import tpDcc as tp
from tpDcc.libs.python import decorators, python, path as path_utils

import artellapipe
from artellapipe.core import defines
from artellapipe.libs.artella.core import artellalib

LOGGER = logging.getLogger('artellapipe')


class ArtellaFile(object):

    FILE_TYPE = None
    FILE_EXTENSIONS = list()
    FILE_RULE = None
    FILE_TEMPLATE = None

    def __init__(self, file_name, file_path=None, file_extension=None, project=None):
        self._project = project if project else artellapipe.project
        self._file_name = self._get_name(file_name)
        self._file_path = self._get_path(file_path)
        self._extensions = self._get_extensions(file_extension)
        self._history = None
        self._working_status = None
        self._working_history = None
        self._latest_server_version = {
            defines.ArtellaFileStatus.WORKING: None,
            defines.ArtellaFileStatus.PUBLISHED: None
        }

        super(ArtellaFile, self).__init__()

    # ==========================================================================================================
    # PROPERTIES
    # ==========================================================================================================

    @property
    def name(self):
        return self._file_name

    @property
    def path(self):
        return self._file_path

    @property
    def extensions(self):
        return self._extensions

    # ==========================================================================================================
    # ABSTRACT
    # ==========================================================================================================

    @decorators.abstractmethod
    def has_valid_object(self):
        """
        Returns whether valid object is attached to this file
        :return: bool
        """

        raise NotImplementedError(
            'has_valid_object function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_template_dict(self, **kwargs):
        """
        Returns dictionary with the template data for this file
        :return: dict
        """

        raise NotImplementedError(
            'get_template_dict function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_project(self):
        """
        Returns project this file is associated to
        :return: ArtellaProject
        """

        raise NotImplementedError('get_project function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_file(
            self, status=defines.ArtellaFileStatus.WORKING, extension=None, fix_path=False, version=None, **kwargs):
        """
        Returns file of the attached object
        :param status: str
        :param extension: str
        :param fix_path: bool
        :param version: str
        :return: str
        """

        raise NotImplementedError('get_file function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_name(self):
        """
        Returns name of the attached object
        :return: str
        """

        raise NotImplementedError('get_name function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_path(self):
        """
        Returns path of the attached object
        :return: str
        """

        raise NotImplementedError('get_path function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_extension(self):
        """
        Returns the extension of the attached file
        :return: str
        """

        raise NotImplementedError('get_extension function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_latest_published_versions(self):
        """
        Returns latest published version of file
        :return: str
        """

        raise NotImplementedError(
            'get_latest_published_versions function for {} is not implemented!'.format(self.__class__.__name__))

    # ==========================================================================================================
    # FILES
    # ==========================================================================================================

    def get_history(self, status, force_update=False):
        """
        Returns the history of the asset files
        :param status: ArtellaFileStatus
        :param force_update: bool
        :return:
        """

        # TODO: Add support for both working and published files

        if self._history and not force_update:
            return self._history

        file_name = self.get_name()
        file_path = self.get_path()
        working_folder = self._project.get_working_folder()
        file_path = os.path.join(file_path, working_folder, self.FILE_TYPE, file_name + self.FILE_EXTENSIONS[0])
        history = artellalib.get_file_history(file_path=file_path)

        self._history = history

        return self._history

    def get_file_paths(self, return_first=False, fix_path=True, **kwargs):
        """
        Returns full path of the file
        :return: str or list(str)
        """

        file_paths = list()

        if self.path:
            split_path = os.path.splitext(self.path)
            if not self.path.endswith(self.name) and not split_path[-1]:
                base_path = path_utils.clean_path(os.path.join(self.path, self.name))
            else:
                base_path = self.path
            if not self._extensions:
                LOGGER.warning('No valid extensions found for file: "{}"'.format(self.__class__.__name__))
                return base_path
        else:
            return None if return_first else file_paths

        extensions = self._extensions
        for extension in extensions:
            if not extension.startswith('.'):
                extension = '.{}'.format(extension)

            split_path = os.path.splitext(base_path)
            if split_path[-1] == extension:
                file_path = base_path
            else:
                file_path = '{}{}'.format(base_path, extension)

            if fix_path:
                file_path = artellapipe.FilesMgr().fix_path(file_path)

            file_path = artellapipe.FilesMgr().prefix_path_with_project_path(file_path)

            file_paths.append(file_path)

        if return_first:
            return file_paths[0]

        return file_paths

    def open_file(self, status=defines.ArtellaFileStatus.WORKING, fix_path=False):
        """
        References current file into DCC
        :return:
        """

        file_path = None
        if self.path:
            file_path = self.get_file_paths(return_first=True, fix_path=fix_path)
        if not file_path or not os.path.isfile(file_path):
            if status == defines.ArtellaFileStatus.WORKING:
                file_path = self.get_working_path()
            else:
                file_path = self.get_latest_local_published_path()

            if fix_path:
                file_path = artellapipe.FilesMgr().fix_path(file_path)

        return self._open_file(file_path=file_path)

    def import_file(self, status=defines.ArtellaFileStatus.WORKING, fix_path=True, sync=False,
                    reference=False, *args, **kwargs):
        """
        References current file into DCC
        :param status: str
        :param fix_path: bool
        :param sync: bool
        :return:
        """

        file_path = self.get_file_paths(return_first=True, fix_path=fix_path, status=status)
        valid_path = self._check_path(file_path, sync=sync)
        if not valid_path:
            msg = 'Impossible to reference file of type "{}". File Path "{}" does not exists!'.format(
                self.FILE_TYPE, file_path)
            LOGGER.warning(msg)
            return None

        if reference:
            return self._reference_file(file_path=file_path, *args, **kwargs)
        else:
            return self._import_file(file_path=file_path, *args, **kwargs)

    def export_file(self, fix_path=True, *args, **kwargs):
        """
        Exports current file
        :param fix_path: bool
        :param args:
        :param kwargs:
        """

        file_path = self.get_file_paths(return_first=True, fix_path=fix_path, **kwargs)
        return self._export_file(file_path, *args, **kwargs)

    def get_working_path(self, sync_folder=False):
        """
        Returns working path to the file
        :return: str
        """

        working_path = self.get_file(
            status=defines.ArtellaFileStatus.WORKING, extension=self.FILE_EXTENSIONS[0], fix_path=False)

        if sync_folder:
            return path_utils.clean_path(os.path.dirname(working_path))

        return path_utils.clean_path(working_path)

    def get_local_versions(self, status=None):
        """
        Returns all local version of the current file type in the wrapped asset
        :param status: ArtellaFileStatus
        :return:
        """

        if not status:
            status = defines.ArtellaFileStatus.WORKING

        local_versions = dict()

        if not self.has_valid_object():
            LOGGER.warning('Impossible to retrieve local version because file object is not defined!')
            return local_versions

        file_path = self.get_path()
        if not file_path or not os.path.exists(file_path):
            return local_versions

        file_type_template = artellapipe.FilesMgr().get_template(self.FILE_TYPE)
        if not file_type_template:
            LOGGER.warning(
                'Impossible to retrieve local version because template for "{}" is not in configuration file'.format(
                    self.FILE_TYPE))
            return local_versions

        for extension in self.FILE_EXTENSIONS:

            template_dict = self.get_template_dict(extension=extension)

            folders_to_check = list()
            working_folder = self._project.get_working_folder()
            if status == defines.ArtellaFileStatus.PUBLISHED:
                for p in os.listdir(file_path):
                    if p == working_folder:
                        continue
                    folders_to_check.append(p)
            for folder in folders_to_check:
                template_dict['version_folder'] = folder
                file_path = file_type_template.format(template_dict)
                file_path = artellapipe.FilesMgr().prefix_path_with_project_path(file_path)
                if file_path and os.path.exists(file_path):
                    version = artellalib.split_version(folder)
                    if version:
                        local_versions[str(version[1])] = folder

            return local_versions

        return local_versions

    def get_latest_local_versions(self, status=None, next_version=False):
        """
        Returns latest local version of the of the current file type
        :param status: str
        :param next_version: bool
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

        if latest_local_versions and next_version:
            current_version = artellalib.split_version(latest_local_versions[1])
            new_version = artellalib.split_version(latest_local_versions[1], next_version=True)
            latest_local_versions[0] = new_version[1]
            latest_local_versions[1] = latest_local_versions[1].replace(current_version[0], new_version[0])

        return latest_local_versions

    def get_latest_local_published_path(self, sync_folder=False):
        """
        Returns local path to the latest published file
        :return: str
        """

        latest_local_versions = self.get_latest_local_versions(status=defines.ArtellaFileStatus.PUBLISHED)
        if not latest_local_versions:
            return

        version_folder = latest_local_versions[1]

        published_path = self.get_file(status=defines.ArtellaFileStatus.PUBLISHED, extension=self.FILE_EXTENSIONS[0],
                                       fix_path=False, version=version_folder)

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

        file_path = self.get_path()
        if not file_path:
            return

        if status == defines.ArtellaFileStatus.PUBLISHED:
            result = self.get_latest_published_versions()
        else:
            working_folder = self._project.get_working_folder()
            working_path = os.path.join(file_path, working_folder, self.FILE_TYPE)

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

    def get_latest_server_published_versions(self):
        """
        Returns latest published version in Artella server
        :return: str
        """

        latest_server_versions = self.get_latest_server_version(status=defines.ArtellaFileStatus.PUBLISHED)

        return latest_server_versions

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

        published_path = self.get_file(status=defines.ArtellaFileStatus.PUBLISHED, extension=self.FILE_EXTENSIONS[0],
                                       fix_path=False, version=version_folder)
        if not published_path:
            LOGGER.warning('Impossible to retrieve latest published path ...')
            return

        if sync_folder:
            ext = os.path.splitext(published_path)[-1]
            if ext:
                return path_utils.clean_path(os.path.dirname(os.path.dirname(published_path)))
            else:
                return path_utils.clean_path(os.path.dirname(published_path))

        return path_utils.clean_path(published_path)

    # ==========================================================================================================
    # INTERNAL
    # ==========================================================================================================

    def _get_name(self, name):
        """
        Internal function that returns valid file name for this file
        Can be override in specific files to return proper name arguments
        :return: str
        """

        if not self.FILE_RULE:
            return name

        solved_name = artellapipe.NamesMgr().solve_name(self.FILE_RULE, name)
        if not solved_name:
            solved_name = name

        return solved_name

    def _get_path(self, path):
        """
        Internal function that tries to return a file path with the information of the file
        :return:str
        """

        if path:
            return path

        if self.FILE_TEMPLATE:
            if self.FILE_EXTENSIONS:
                template_data = self.get_template_dict(extension=self.FILE_EXTENSIONS[0])
            else:
                template_data = self.get_template_dict()
            if template_data:
                template = artellapipe.FilesMgr().get_template(self.FILE_TEMPLATE)
                if template:
                    try:
                        file_path = template.format(template_data)
                        if file_path.endswith('.'):
                            file_path = file_path[:-1]
                    except Exception:
                        file_path = None
                    return file_path

    def _get_extensions(self, extension):
        """
        Internal function that tries to return a file extension with the information of the file
        :return: str
        """

        if not self.FILE_EXTENSIONS:
            if extension:
                return python.force_list(extension)
            else:
                return list()

        if extension:
            if extension in self.FILE_EXTENSIONS:
                return python.force_list(extension)

        return self.FILE_EXTENSIONS or list()

    def _check_path(self, file_path, sync=False):
        """
        Returns whether or not given path exists.
        :param file_path: str
        :param sync: bool
        :return: bool
        """

        if sync or not file_path:
            self.asset.sync_latest_published_files(file_type=self.FILE_TYPE)

        if not file_path or not os.path.isfile(file_path):
            return False

        return True

    def _open_file(self, file_path):
        """
        Internal function that opens current file in DCC
        Overrides in custom asset file
        :param path: str
        :return:
        """

        if not file_path:
            return False

        if os.path.isfile(file_path) and tp.Dcc.scene_name() != file_path:
            tp.Dcc.open_file(file_path)

        return True

    def _import_file(self, file_path, *args, **kwargs):
        """
        Internal function that imports current file in DCC
        Overrides in custom asset file
        :param path: str
        :return:
        """

        if not file_path:
            return False

        if os.path.isfile(file_path) and tp.Dcc.scene_name() != file_path:
            tp.Dcc.import_file(file_path)

        return True

    def _reference_file(self, file_path, *args, **kwargs):
        """
        Internal function that references current file in DCC
        Overrides in custom asset file
        :param path: str
        :return:
        """

        raise NotImplementedError('_reference_file function for "{}" is not implemented!'.format(self))

    def _export_file(self, file_path, *args, **kwargs):
        """
        Internal function that exports current file
        :param file_path: str
        :param args:
        :param kwargs:
        """

        raise NotImplementedError('_export_file function for "{}" is not implemented!'.format(self))

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

        asset_name = self.get_name()
        ref_path = os.path.join(working_path, artella_data.name)
        file_name = os.path.basename(ref_path)
        for extension in self.FILE_EXTENSIONS:
            if file_name == '{}{}'.format(asset_name, extension):
                if not force_update and self._working_history:
                    return self._working_history
                else:
                    return artellalib.get_file_history(ref_path)
