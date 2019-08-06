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

    ASSET_FILES = dict()

    def __init__(self, project, asset_data, category=None):
        super(AbstractAsset, self).__init__()

        self._project = project
        self._asset_data = asset_data
        self._category = category

    @property
    def data(self):
        """
        Returns asset data
        :return: object
        """

        return self._asset_data

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

    def get_relative_path(self):
        """
        Returns path of the asset relative to the Artella project
        :return: str
        """

        return os.path.relpath(self.get_path(), self._project.get_assets_path())
