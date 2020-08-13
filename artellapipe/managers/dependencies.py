#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager for DCC dependencies
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

import tpDcc as tp
from tpDcc.libs.python import decorators

LOGGER = logging.getLogger('artellapipe')


class DependenciesManager(object):

    @decorators.abstractmethod
    def get_dependencies(self, file_path, parent_path=None, found_files=None):
        """
        Returns all dependencies that are currently loaded in the given file
        :param file_path: str, file path we want to get dependencies of
        :param parent_path: str
        :param found_files: list(str)
        :param fix_paths: bool
        :return: list(str)
        """

        raise NotImplementedError(
            'get_dependencies function is not implemented in "{}"'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def fix_dependencies_paths(self, file_path):
        """
        Tries to fix paths that are not valid in the given file
        :param file_path: str, file path we want to fix paths of
        """

        raise NotImplementedError(
            'fix_dependencies_paths function is not implemented in "{}"'.format(self.__class__.__name__))

    def get_current_scene_dependencies(self):
        """
        Returns all dependencies that are currently loaded in current scene
        :return: list(str)
        """

        file_path = tp.Dcc.scene_name()
        if not file_path or not os.path.isfile(file_path):
            LOGGER.warning('Impossible to retrieve dependencies from current scene file: "{}"'.format(file_path))
            return

        return self.get_dependencies(file_path=file_path)

    @decorators.abstractmethod
    def update_dependencies(self, file_path):
        """
        Updates all the dependencies of the given file path
        :param file_path: str
        """

        raise NotImplementedError(
            'update_dependencies function is not implemented in "{}"'.format(self.__class__.__name__))
