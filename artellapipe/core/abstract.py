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

from tpPyUtils import decorators


class AbstractAsset(object):

    def __init__(self, project, asset_data, category=None, node=None):
        super(AbstractAsset, self).__init__()

        self._project = project
        self._asset_data = asset_data
        self._category = category
        self._node = node

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

    @decorators.abstractmethod
    def get_name(self):
        """
        Returns the name of the asset
        :return: str
        """

        raise NotImplementedError('get_name function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_path(self):
        """
        Returns the path of the asset
        :return: str
        """

        raise NotImplementedError('get_path function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_category(self):
        """
        Returns the category of the asset
        :return: str
        """

        raise NotImplementedError('get_category function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_file(self, file_type, status, extension=None, fix_path=False):
        """
        Returns file path of the given file type and status
        :param file_type: str
        :param status: str
        :param extension: str
        :param fix_path: bool
        """

        raise NotImplementedError('get_file function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_file(self, file_type, status, extension=None, fix_path=False):
        """
        Returns file path of the given file type and status
        :param file_type: str
        :param status: str
        :param extension: str
        :param fix_path: bool
        """

        raise NotImplementedError('get_file function for {} is not implemented!'.format(self.__class__.__name__))

    def open_file(self, file_type, status, extension=None):
        """
        Opens asset file with the given type and status (if exists)
        :param file_type: str
        :param status: str
        :param extension: str
        """

        raise NotImplementedError('get_file function for {} is not implemented!'.format(self.__class__.__name__))

    def import_file(self, file_type, status, extension=None):
        """
        Imports asset file with the given type and status (if exists)
        :param file_type: str
        :param status: str
        :param extension: str
        """
        raise NotImplementedError('import_file function for {} is not implemented!'.format(self.__class__.__name__))

    def import_file_by_extension(self, extension=None):
        """
        Imports asset file with the given extension
        :param extension: str
        """
        raise NotImplementedError(
            'import_file_by_extension function for {} is not implemented!'.format(self.__class__.__name__))

    def reference_file(self, file_type, status, extension=None):
        """
        References asset file with the given type and status (if exists)
        :param file_type: str
        :param status: str
        :param extension: str
        """
        raise NotImplementedError('reference_file function for {} is not implemented!'.format(self.__class__.__name__))

    def reference_file_by_extension(self, extension=None):
        """
        References asset file with the given extension
        :param extension: str
        """

        raise NotImplementedError(
            'reference_file_by_extension function for {} is not implemented!'.format(self.__class__.__name__))

    def get_relative_path(self):
        """
        Returns path of the asset relative to the Artella project
        :return: str
        """

        return os.path.relpath(self.get_path(), self._project.get_assets_path())
