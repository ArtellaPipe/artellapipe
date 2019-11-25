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

from tpPyUtils import python, path as path_utils
from tpQtLib.core import qtutils

import artellapipe
from artellapipe.core import asset

LOGGER = logging.getLogger()


class ArtellaFile(object):

    FILE_TYPE = None
    FILE_EXTENSIONS = list()
    FILE_RULE = None
    FILE_TEMPLATE = None

    def __init__(self, file_name, file_path=None, file_extension=None):
        self._file_name = self._get_name(file_name)
        self._file_path = self._get_path(file_path)
        self._extensions = self._get_extensions(file_extension)
        self._history = None
        self._working_status = None
        self._working_history = None
        self._latest_server_version = {
            asset.ArtellaAssetFileStatus.WORKING: None,
            asset.ArtellaAssetFileStatus.PUBLISHED: None
        }

        super(ArtellaFile, self).__init__()

    @property
    def name(self):
        return self._file_name

    @property
    def path(self):
        return self._file_path

    @property
    def extensions(self):
        return self._extensions

    def get_file_paths(self, return_first=False, fix_path=True):
        """
        Returns full path of the file
        :return: str or list(str)
        """

        base_path = path_utils.clean_path('{}{}{}'.format(self.path, os.sep, self.name))
        if not self._extensions:
            LOGGER.warning('No valid extensions found for file: "{}"'.format(self.__class__.__name__))
            return base_path

        file_paths = list()
        extensions = self._extensions
        for extension in extensions:
            if not extension.startswith('.'):
                extension = '.{}'.format(extension)

            file_path = '{}{}'.format(base_path, extension)
            if fix_path:
                file_path = artellapipe.FilesMgr().fix_path(file_path)
            file_paths.append(file_path)

        if return_first:
            return file_paths[0]

        return file_paths

    def open_file(self, status):
        """
        References current file into DCC
        :return:
        """

        if status == asset.ArtellaAssetFileStatus.WORKING:
            file_path = self.get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        self._open_file(path=file_path)

    def import_file(self, status, fix_path=True, sync=False, *args, **kwargs):
        """
        References current file into DCC
        :return:
        """

        file_path = self._get_path(status=status, fix_path=fix_path)
        valid_path = self._check_path(file_path, sync=sync)
        if not valid_path:
            msg = 'Impossible to import file of type "{}". File Path "{}" does not exists!'.format(
                self.FILE_TYPE, file_path)
            LOGGER.warning(msg)
            qtutils.warning_message(msg)
            return None

        self._import_file(path=file_path, *args, **kwargs)

    def reference_file(self, fix_path=True, sync=False, *args, **kwargs):
        """
        References current file into DCC
        :param status: str
        :param fix_path: bool
        :param sync: bool
        :return:
        """

        file_path = self.get_file_paths(return_first=True, fix_path=fix_path)
        valid_path = self._check_path(file_path, sync=sync)
        if not valid_path:
            msg = 'Impossible to reference file of type "{}". File Path "{}" does not exists!'.format(
                self.FILE_TYPE, file_path)
            LOGGER.warning(msg)
            qtutils.warning_message(msg)
            return None

        return self._reference_file(file_path=file_path, *args, **kwargs)

    def get_template_dict(self):
        """
        Returns dictionary with the template data for this file
        :return: dict
        """

        return dict()

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

        if not self.FILE_TEMPLATE:
            return path

        template_data = self.get_template_dict()
        if not template_data:
            return path

        template = artellapipe.FilesMgr().get_template(self.FILE_TEMPLATE)
        if not template:
            return path

        return template.format(template_data)

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

        pass

    def _import_file(self, file_path, *args, **kwargs):
        """
        Internal function that imports current file in DCC
        Overrides in custom asset file
        :param path: str
        :return:
        """

        pass

    def _reference_file(self, file_path, *args, **kwargs):
        """
        Internal function that references current file in DCC
        Overrides in custom asset file
        :param path: str
        :return:
        """

        pass
