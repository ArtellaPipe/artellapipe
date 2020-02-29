#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager that handles OCIO setup
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
import traceback

import tpDcc as tp
from tpDcc.libs.python import decorators

import artellapipe.register

LOGGER = logging.getLogger()


class ArtellaOCIOManager(object):
    def __init__(self):
        self._project = None
        self._config = None
        self._available_plugins = list()

    @property
    def config(self):
        return self._config

    @property
    def plugins(self):
        return self._available_plugins

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project
        self._config = tp.ConfigsMgr().get_config(
            config_name='artellapipe-ocio',
            package_name=self._project.get_clean_name(),
            root_package_name='artellapipe',
            environment=project.get_environment()
        )

    def init_ocio(self):
        """
        Initializes OCIO setup of current DCC and project
        """

        self.load_plugins()

    def load_plugins(self):
        """
        Loads all OCIO related plugins
        """

        ocio_plugins = self._config.get('ocio_plugins', default=dict())
        if not ocio_plugins:
            LOGGER.warning('No OCIO plugins found in configuration file: "{}"'.format(self._config.get_path()))
            return

        for ocio_plugin_name, ocio_plugin_info in ocio_plugins.items():
            plugin_name = ocio_plugin_info.get('plugin_name', None)
            if not plugin_name:
                LOGGER.warning(
                    'Impossible to load "{}" OCIO Plugin because its plugin_name is not defined!'.format(
                        ocio_plugin_name))
                continue

            if not tp.Dcc.is_plugin_loaded(plugin_name):
                LOGGER.info('Loading OCIO Plugin: "{}"'.format(plugin_name))
                try:
                    tp.Dcc.load_plugin(plugin_name, quiet=True)
                except Exception as exc:
                    LOGGER.error(
                        'Error while loading OCIO Plugin: "{}" | {} | {}'.format(
                            plugin_name, exc, traceback.format_exc()))
                    continue

            LOGGER.info('OCIO Plugin "{}" loaded successfully!'.format(plugin_name))
            self._available_plugins.append(ocio_plugin_name)


@decorators.Singleton
class ArtellaOCIOManagerSingleton(ArtellaOCIOManager, object):
    def __init__(self):
        ArtellaOCIOManager.__init__(self)


artellapipe.register.register_class('OCIOMgr', ArtellaOCIOManagerSingleton)
