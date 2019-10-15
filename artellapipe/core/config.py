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

import metayaml

import tpDccLib as tp

LOGGER = logging.getLogger()


class ArtellaConfigurationParser(object):
    def __init__(self, config_data):
        super(ArtellaConfigurationParser, self).__init__()

        self._config_data = config_data
        self._parsed_data = dict()

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

    PARSER_CLASS = ArtellaConfigurationParser

    def __init__(self, project_name, config_path):
        super(ArtellaConfiguration, self).__init__()

        self._parsed_data = self.load(project_name=project_name, config_path=config_path)

    @property
    def data(self):
        return self._parsed_data

    def load(self, project_name, config_path):
        """
        Function that reads project configuration file and initializes project variables properly
        This function can be extended in new projects
        """

        config_data = self._get_config_data(project_name, config_path)
        if not config_data:
            return False

        parsed_data = self.PARSER_CLASS(config_data).parse()

        return parsed_data

    def _get_config_data(self, project_name, config_path):
        """
        Returns the config data of the given project name
        :return: dict
        """

        if not config_path or not os.path.isfile(config_path):
            tp.Dcc.error('Project Configuration File for {} Project not found! {}'.format(self, config_path))
            return

        # We use artellapipe project configuration as base configuration file
        from artellapipe import config
        artella_config_path = config.ArtellaConfigs().get_project_configuration_file()

        project_config_data = metayaml.read(
            [artella_config_path, config_path],
            {
                'title': project_name.title(),
                'project_lower': project_name.replace(' ', '').lower(),
                'project_upper': project_name.replace(' ', '').upper()
            }
        )

        if not project_config_data:
            tp.Dcc.error('Project Configuration File for {} Project is empty! {}'.format(self, config_path))
            return

        return project_config_data
