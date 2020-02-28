#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils classes to define Artella Plugins
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


import time
import inspect

import tpDcc as tp
from tpDcc.libs.python import osplatform


class PluginStats(object):
    """
    Class used to get info about a plugin and its environment
    """

    def __init__(self, plugin):
        self._plugin = plugin
        self._id = self._plugin.id
        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0

        self._info = dict()
        self._init()

    def _init(self):
        """
        Internal function that initializes plugin statistics data
        """

        self._info.update({
            'name': self._plugin.__class__.__name__,
            'constructor': self._plugin.constructor,
            'module': self._plugin.__class__.__module__,
            'filepath': inspect.getfile(self._plugin.__class__),
            'id': self._id,
            'application': tp.Dcc.get_name()
        })

        self._info.update(osplatform.machine_info())

    def start(self):
        """
        Function that is called when a plugins is started
        """

        self._start_time = time.time()

    def finish(self, trace_back=None):
        """
        Function that is called when a plugin finish its execution
        :param trace_back: optional traceback
        """

        self._end_time = time.time()
        self._execution_time = self._end_time - self._start_time
        self._info['executionTime'] = self._execution_time
        self._info['lastUsed'] = self._end_time
        if trace_back:
            self._info['traceback'] = trace_back


class Plugin(object):
    """
    Base class to defines new plugins
    """

    id = ''

    def __init__(self, manager=None):
        self._manager = manager
        self._stats = PluginStats(self)

    @property
    def manager(self):
        return self._manager

    @property
    def stats(self):
        return self._stats


class PluginManager(object):

    def __init__(self, interface=Plugin, variable_name=None):
        self._plugins = dict()
        self._interface = interface
        self._variable_name = variable_name or ''
        self._loaded_tools = dict()
        self._base_paths = list()
