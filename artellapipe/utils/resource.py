#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle resources used in GUIs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
from collections import Iterable

from Qt.QtGui import (QIcon, QPixmap)

from tpPyUtils import decorators

from tpQtLib.core import resource


@decorators.Singleton
class ResourceManager(object):
    """
    Class that handles all resources stored in registered paths
    """

    def __init__(self):

        self._project_resources = dict()
        self._resources = dict()

    def register_resource(self, resources_path, key=None):
        """
        Registers given resource path
        :param str resources_path: path to register.
        :param str key: optional key for the resource path.
        :return:
        """
        if resources_path in self._resources:
            return

        if key:
            if key == 'project':
                self._project_resources[resources_path] = resource.Resource(resources_path)
                if key in self._resources:
                    self._resources[key].insert(0, resource.Resource(resources_path))
                else:
                    self._resources[key] = [resource.Resource(resources_path)]

        self._resources[resources_path] = resource.Resource(resources_path)

    def get_resources_paths(self, key=None):
        """
        Returns registered resource paths
        :param key: str, optional key to return resource path with given key
        :return:
        """
        if not self._resources:
            return []

        if key == 'project':
            return [res.dirname for res in self._project_resources.values()]

        if key and key in self._resources:
            return [res.dirname for res in self._resources[key]]

        resources_paths = list()
        for res in self._resources.values():
            if isinstance(res, Iterable):
                for r in res:
                    dirname = r.dirname
                    if dirname in resources_paths:
                        continue
                    resources_paths.append(dirname)
            else:
                dirname = res.dirname
                if dirname in resources_paths:
                    continue
                resources_paths.append(res.dirname)

        return resources_paths

    def get(self, *args, **kwargs):
        """
        Returns path to a resource
        :param args: list
        :return: str
        """

        if not self._resources:
            return None

        if 'key' in kwargs:
            resources_paths = self.get_resources_paths(kwargs.pop('key'))
            if resources_paths:
                for res_path in resources_paths:
                    res = None
                    if res_path in self._resources:
                        res = self._resources[res_path]
                    if res:
                        path = res.get(dirname=res_path, *args)
                        if path:
                            return path

        if self._project_resources:
            for res_path, res in self._project_resources.items():
                path = res.get(dirname=res_path, *args)
                if path and os.path.isfile(path):
                    return path

        for res_path, res in self._resources.items():
            if not os.path.isdir(res_path):
                continue
            if isinstance(res, Iterable):
                for r in res:
                    path = r.get(dirname=res_path, *args)
                    if path:
                        return path
            else:
                path = res.get(dirname=res_path, *args)
                if path and os.path.isfile(path):
                    return path

        return None

    def icon(self, *args, **kwargs):
        """
        Returns icon
        :param args: list
        :param kwargs: kwargs
        :return: QIcon
        """

        if not self._resources:
            return None

        if 'key' in kwargs:
            resources_paths = self.get_resources_paths(kwargs.pop('key'))
            if resources_paths:
                for res_path in resources_paths:
                    res = None
                    if res_path in self._resources:
                        res = self._resources[res_path]
                    if res:
                        path = res.icon(dirname=res_path, *args, **kwargs)
                        if path:
                            return path

        if self._project_resources:
            for res_path, res in self._project_resources.items():
                path = res.icon(dirname=res_path, *args, **kwargs)
                if path:
                    return path

        for res_path, res in self._resources.items():
            if isinstance(res, Iterable):
                for r in res:
                    path = r.icon(dirname=res_path, *args, **kwargs)
                    if path:
                        return path
            else:
                path = res.icon(dirname=res_path, *args, **kwargs)
                if path:
                    return path

        return QIcon()

    def pixmap(self, *args, **kwargs):
        """
        Returns pixmap
        :param args: list
        :param kwargs: dict
        :return: QPixmap
        """

        if not self._resources:
            return None

        if 'key' in kwargs:
            resources_paths = self.get_resources_paths(kwargs.pop('key'))
            if resources_paths:
                for res_path in resources_paths:
                    res = None
                    if res_path in self._resources:
                        res = self._resources[res_path]
                    if res:
                        path = res.pixmap(dirname=res_path, *args, **kwargs)
                        if path:
                            return path

        if self._project_resources:
            for res_path, res in self._project_resources.items():
                path = res.pixmap(dirname=res_path, *args, **kwargs)
                if path:
                    return path

        for res_path, res in self._resources.items():
            if isinstance(res, Iterable):
                for r in res:
                    path = r.pixmap(dirname=res_path, *args, **kwargs)
                    if path:
                        return path
            else:
                path = res.pixmap(dirname=res_path, *args, **kwargs)
                if path:
                    return path

        return QPixmap()
