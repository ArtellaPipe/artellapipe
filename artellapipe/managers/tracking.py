#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base abstract tracking class for Artella projects
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

from Qt.QtCore import *

from tpPyUtils import decorators

import artellapipe.register
from artellapipe.libs import artella

LOGGER = logging.getLogger()


class TrackingManager(QObject, object):

    logged = Signal()

    def __init__(self):
        super(TrackingManager, self).__init__()

        self._project = None
        self._data = dict()
        self._updated = False
        self._logged = False

    @property
    def project(self):
        return self._project

    def set_project(self, project):
        """
        Sets the project linked to the tracking manager
        :param project: ArtellaProject
        """

        self._project = project
        # self.update_tracking_info()

    def is_logged(self):
        """
        Returns whether user is locked into the tracking system or not
        :return: bool
        """

        return self._logged

    def check_update(self):
        """
        Checks if tracking manager has been updated or not. If not, an updating is forced
        """

        if self._updated:
            return

        self.update_tracking_info()

    @decorators.abstractmethod
    def update_tracking_info(self):
        """
        Updates all the project tracking info
        """

        raise NotImplementedError(
            'update_tracking_info function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def is_tracking_available(self):
        """
        Returns whether tracking service is available or not
        :return: bool
        """

        raise NotImplementedError(
            'is_tracking_available function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def login(self, *args, **kwargs):
        """
        Login into tracking service with given user and password
        :return: bool
        """

        raise NotImplementedError('login function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def logout(self, *args, **kwargs):
        """
        Logout from tracker service
        :param args:
        :param kwargs:
        :return: bool
        """

        raise NotImplementedError('logout function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def download_preview_file_thumbnail(self, preview_id, file_path):
        """
        Downloads given preview file thumbnail and save it at given location
        :param preview_id:  str or dict, The preview file dict or ID.
        :param target_path: str, Location on hard drive where to save the file.
        """

        raise NotImplementedError(
            'download_preview_file_thumbnail function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def all_project_assets(self):
        """
        Return all the assets information of the assets of the current project
        :return: list
        """

        # TODO: Default implementation, it will be removed in the future

        found_assets = list()

        if not self._project:
            LOGGER.warning('Impossible to retrieve assets because project is not defined!')
            return found_assets

        assets_path = artellapipe.AssetsMgr().get_assets_path()
        if not artellapipe.AssetsMgr().is_valid_assets_path():
            LOGGER.warning('Impossible to retrieve assets from invalid path: {}'.format(assets_path))
            return

        if not assets_path or not os.path.exists(assets_path):
            LOGGER.warning('Impossible to retrieve assets from invalid path: {}'.format(assets_path))
            return found_assets

        filename_attr = self.project.config.get('asset_data', 'filename')
        if not filename_attr:
            LOGGER.warning(
                'Impossible to retrieve {} assets because asset data file name is not defined!'.format(
                    self.project.name.title()))
            return

        for root, dirs, files in os.walk(assets_path):
            if dirs and artella.config.get('server', {}).get('working_folder') in dirs:
                _asset_name = os.path.basename(root)
                new_asset = self.get_asset_from_path(asset_path=root)
                if new_asset:
                    found_assets.append(new_asset)

        return found_assets


@decorators.Singleton
class TrackinManagerSingleton(TrackingManager, object):
    def __init__(self):
        TrackingManager.__init__(self)


artellapipe.register.register_class('Tracker', TrackinManagerSingleton)
