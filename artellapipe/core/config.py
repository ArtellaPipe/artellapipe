#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains default implementation for Artella project configuration
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import importlib

import metayaml

import tpDccLib as tp

LOGGER = logging.getLogger()


class ArtellaConfigurationParser(object):
    def __init__(self, config_data):
        super(ArtellaConfigurationParser, self).__init__()

        self._config_data = config_data
        self._parsed_data = dict()

    def parse(self):
        self._parsed_data = self._config_data
        return self._parsed_data


class ArtellaProjectConfigurationParser(ArtellaConfigurationParser, object):
    def __init__(self, config_data):
        super(ArtellaProjectConfigurationParser, self).__init__(config_data=config_data)

    def parse(self):
        if not self._config_data:
            return self._parsed_data

        for section_name, section_dict in self._config_data.items():
            if not isinstance(section_dict, dict):
                continue

            for attr_name, attr_value in section_dict.items():
                if attr_name in self._parsed_data:
                    LOGGER.warning('Attribute {} is already loaded in Project Configuration File!'.format(attr_name))
                    continue
                if section_name == 'project':
                    self._parsed_data[attr_name] = attr_value
                else:
                    self._parsed_data['{}_{}'.format(section_name, attr_name)] = attr_value

        if not self._parsed_data:
            LOGGER.error('Impossible to parse Project Configuration File!')

        return self._parsed_data


class ArtellaConfiguration(object):
    def __init__(self, project_name, config_name, config_dict=None, parser_class=ArtellaConfigurationParser):
        super(ArtellaConfiguration, self).__init__()

        self._parser_class = parser_class
        self._parsed_data = self.load(project_name=project_name, config_name=config_name, config_dict=config_dict)

    @property
    def data(self):
        return self._parsed_data

    def load(self, project_name, config_name, config_dict=None):
        """
        Function that reads project configuration file and initializes project variables properly
        This function can be extended in new projects
        """

        if not config_dict:
            config_dict = {}

        config_data = self._get_config_data(project_name, config_name, config_dict=config_dict)
        if not config_data:
            return False

        parsed_data = self._parser_class(config_data).parse()

        return parsed_data

    def _get_config_data(self, project_name, config_name, config_dict):
        """
        Returns the config data of the given project name
        :return: dict
        """

        if not config_name:
            tp.Dcc.error(
                'Project Configuration File for {} Project not found! {}'.format(self, project_name, config_name))
            return

        module_config_name = config_name + '.yml'

        # We use artellapipe project configuration as base configuration file
        from artellapipe import config
        artella_config_dir = os.path.dirname(config.__file__)
        artella_config_path = os.path.join(artella_config_dir, module_config_name)

        project_config_path = None
        try:
            project_config_mod = importlib.import_module('{}.config'.format(project_name))
            project_config_dir = os.path.dirname(project_config_mod.__file__)
            all_configs = [
                f for f in os.listdir(project_config_dir) if os.path.isfile(os.path.join(project_config_dir, f))]
            if module_config_name in all_configs:
                project_config_path = os.path.join(project_config_dir, module_config_name)
        except RuntimeError:
            LOGGER.warning('No Configuration Module found for project: {}'.format(project_name))

        if project_config_path and os.path.isfile(project_config_path):
            if artella_config_path and os.path.isfile(artella_config_path):
                config_data = metayaml.read([artella_config_path, project_config_path], config_dict)
            else:
                config_data = metayaml.read([project_config_path], config_dict)
        else:
            if not artella_config_path or not os.path.isfile(artella_config_path):
                raise RuntimeError(
                    'Impossible to load configuration "{}" because it does not exists!"'.format(artella_config_path))
            config_data = metayaml.read([artella_config_path], config_dict)

        if not config_data:
            tp.Dcc.error('Project Configuration File for {} Project is empty! {}'.format(self, project_config_path))
            return

        return config_data
