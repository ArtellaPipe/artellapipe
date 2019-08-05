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

from tpPyUtils import decorators


class AbstractAsset(object):

    def __init__(self, asset_data):
        super(AbstractAsset, self).__init__()

        self._asset_data = asset_data

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
    def get_thumbnail_icon(self):
        """
        Returns the icon of the asset
        :return: QIcon
        """

        raise NotImplementedError('get_thumbnail_icon function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_category(self):
        """
        Returns the category of the asset
        :return: str
        """

        raise NotImplementedError('get_category function for {} is not implemented!'.format(self.__class__.__name__))
