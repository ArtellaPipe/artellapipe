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

import logging

from Qt.QtCore import *

from tpDcc.libs.python import decorators

import artellapipe.register

LOGGER = logging.getLogger()


class TrackingManager(QObject, object):

    logged = Signal()
    unlogged = Signal()

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

    def get_name(self):
        """
        Returns the name of the production tracker system
        :return: str
        """

        return 'Production Tracker'

    def needs_login(self):
        """
        Returns whether or not production trackign needs log to work or not
        """

        return False

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
    def get_user_name(self):
        """
        Returns the name of the current logged user
        :return: str
        """

        raise NotImplementedError('get_user_name function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def download_preview_file_thumbnail(self, preview_id, file_path):
        """
        Downloads given preview file thumbnail and save it at given location
        :param preview_id:  str or dict, The preview file dict or ID.
        :param file_path: str, Location on hard drive where to save the file.
        """

        raise NotImplementedError(
            'download_preview_file_thumbnail function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_project_name(self):
        """
        Returns name of the project
        :return: str
        """

        raise NotImplementedError(
            'get_project_name function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_project_fps(self):
        """
        Returns FPS (frames per second) used in the project
        :return: int
        """

        raise NotImplementedError(
            'get_project_fps function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def get_project_resolution(self):
        """
        Returns resolution used in the project
        :return: str
        """

        raise NotImplementedError(
            'get_project_resolution function for {} is not implemented!'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def all_project_assets(self):
        """
        Return all the assets information of the assets of the current project
        :return: list
        """

        raise NotImplementedError(
            'all_project_assets function for {} is not implemented!'.format(self.__class__.__name__))

    def all_project_sequences(self):
        """
        Returns all the sequences of the current project
        :return:
        """

        raise NotImplementedError(
            'all_project_sequences function for {} is not implemented!'.format(self.__class__.__name__))

    def all_project_shots(self):
        """
        Returns all the shots of the current project
        :return:
        """

        raise NotImplementedError(
            'all_project_shots function for {} is not implemented!'.format(self.__class__.__name__))

    def all_assets_in_shot(self, shot):
        """
        Returns all assets in the given shot
        :param shot:
        :param kwargs:
        :return: list
        """

        raise NotImplementedError(
            'all_assets_in_shot function for {} is not implemented!'.format(self.__class__.__name__))

    def get_tasks_in_shot(self, shot_id):
        """
        Returns all tasks in given shot
        :param shot_id: str
        :return: list
        """

        raise NotImplementedError(
            'get_tasks_in_shot function for {} is not implemented!'.format(self.__class__.__name__))

    def all_task_types(self):
        """
        Returns all task types
        :return: list
        """

        raise NotImplementedError(
            'all_assets_in_shot function for {} is not implemented!'.format(self.__class__.__name__))

    def all_task_types_for_assets(self):
        """
        Returns all task types for assets
        :return:
        """

        raise NotImplementedError(
            'all_task_types_for_assets function for {} is not implemented!'.format(self.__class__.__name__))

    def all_task_types_for_shots(self):
        """
        Returns all task types for assets
        :return:
        """

        raise NotImplementedError(
            'all_task_types_for_shots function for {} is not implemented!'.format(self.__class__.__name__))


@decorators.Singleton
class TrackinManagerSingleton(TrackingManager, object):
    def __init__(self):
        TrackingManager.__init__(self)


artellapipe.register.register_class('Tracker', TrackinManagerSingleton)
