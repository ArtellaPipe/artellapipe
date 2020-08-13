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

import artellapipe

LOGGER = logging.getLogger('artellapipe')


class OCIOManager(object):

    _config = None
    _available_plugins = list()

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tp.ConfigsMgr().get_config(
                config_name='artellapipe-ocio',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    @property
    def plugins(self):
        if not self.__class__._available_plugins:
            self.load_plugins()

        return self.__class__._available_plugins

    def init_ocio(self):
        """
        Initializes OCIO setup of current DCC and project
        """

        self.load_plugins()

    def load_plugins(self):
        """
        Loads all OCIO related plugins
        """

        ocio_plugins = self.config.get('ocio_plugins', default=dict())
        if not ocio_plugins:
            LOGGER.warning('No OCIO plugins found in configuration file: "{}"'.format(self.config.get_path()))
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
            self.__class__._available_plugins.append(ocio_plugin_name)
