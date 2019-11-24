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


class ArtellaConfigurationAttribute(dict, object):
    """
    Class that allows access nested dictionaries using Python attribute access
    https://stackoverflow.com/questions/38034377/object-like-attribute-access-for-nested-dictionary
    """

    def __init__(self, *args, **kwargs):
        super(ArtellaConfigurationAttribute, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_nested_dict(data):
        """
        Construst a nested ArtellaConfigurationAttribute from nested dictionaries
        :param data: dict
        :return: ArtellaConfigurationAttribute
        """

        if not isinstance(data, dict):
            return data
        else:
            return ArtellaConfigurationAttribute(
                {key: ArtellaConfigurationAttribute.from_nested_dict(data[key]) for key in data})


class ArtellaConfigurationParser(object):
    def __init__(self, config_data):
        super(ArtellaConfigurationParser, self).__init__()

        self._config_data = config_data
        self._parsed_data = dict()

    def parse(self):
        self._parsed_data = self._config_data
        return ArtellaConfigurationAttribute.from_nested_dict(self._parsed_data)


class ArtellaConfiguration(object):
    def __init__(self, project_name, config_name, environment, config_dict=None,
                 parser_class=ArtellaConfigurationParser):
        super(ArtellaConfiguration, self).__init__()

        self._project_name = project_name
        self._config_name = config_dict
        self._environment = environment
        self._parser_class = parser_class
        self._parsed_data = self.load(project_name=project_name, config_name=config_name, config_dict=config_dict)

    @property
    def data(self):
        return self._parsed_data

    def get_path(self):
        if not self._parsed_data:
            return None

        return self._parsed_data.get('config', {}).get('path', None)

    def get(self, attr_section, attr_name=None, default=None):
        """
        Returns an attribute of the configuration
        :param attr_name: str
        :param attr_section: str
        :param default: object
        :return:
        """

        if not self._parsed_data:
            LOGGER.warning('Configuration "{}" is empty for "{} | {}"'.format(
                self._config_name, self._project_name, self._environment))
            return default

        if attr_section and attr_name:
            orig_section = attr_section
            attr_section = self._parsed_data.get(attr_section, dict())
            if not attr_section:
                LOGGER.warning('Configuration "{}" has no attribute "{}" in section "{}" for "{} | {}"'.format(
                    self._config_name, attr_name, orig_section, self._project_name, self._environment))
                return default
            attr_value = attr_section.get(attr_name, None)
            if attr_value is None:
                LOGGER.warning('Configuration "{}" has no attribute "{}" in section "{}" for "{} | {}"'.format(
                    self._config_name, attr_name, attr_section, self._project_name, self._environment))
                return default
            return attr_value
        else:
            attr_to_use = attr_section
            if attr_name and not default:
                default = attr_name
            if not attr_section:
                attr_to_use = attr_name
            attr_value = self._parsed_data.get(attr_to_use, None)
            if attr_value is None:
                LOGGER.warning('Configuration "{}" has no attribute "{}" for "{} | {}"'.format(
                    self._config_name, attr_to_use, self._project_name, self._environment))
                return default
            return attr_value

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

    def _get_artella_config_paths(self, module_config_name):
        """
        Returns a list of paths where configuration file can be located in artellapipe-config
        :return: list(str)
        """

        artella_configs_path = os.environ.get('ARTELLA_CONFIGS_PATH', None)
        if not artella_configs_path or not os.path.isdir(artella_configs_path):
            from artellapipe import config
            artella_config_dir = os.path.dirname(config.__file__)
        else:
            artella_config_dir = artella_configs_path

        artella_config_env_dir = os.path.join(artella_config_dir, self._environment.lower())
        if not os.path.isdir(artella_config_env_dir):
            LOGGER.warning('Configuration Folder for Environment "{}" does not exists: "{}"'.format(
                self._environment, artella_config_env_dir))

        artella_config_path = os.path.join(artella_config_env_dir, module_config_name)
        dcc_artella_config_path = os.path.join(artella_config_env_dir, tp.Dcc.get_name(), module_config_name)
        dcc_version_artella_config_path = os.path.join(
            artella_config_env_dir, tp.Dcc.get_name(), tp.Dcc.get_version_name(), module_config_name)

        return [artella_config_path, dcc_artella_config_path, dcc_version_artella_config_path]

    def _get_project_config_paths(self, project_name, module_config_name):
        """
        Returns a list of paths where configuration files can be located in project configuration module
        :return: list(str)
        """

        project_config_path = None
        dcc_project_config_path = None
        dcc_version_project_config_path = None

        try:
            project_config_mod = importlib.import_module('{}.config'.format(project_name))
            project_config_dir = os.path.dirname(project_config_mod.__file__)
            project_config_env_dir = os.path.join(project_config_dir, self._environment.lower())
            if not os.path.isdir(project_config_env_dir):
                LOGGER.warning(
                    'Configuration Folder for Environment "{}" and Project "{}" does not exists: "{}"'.format(
                        self._environment, project_name, project_config_dir))

            project_config_path = os.path.join(project_config_env_dir, module_config_name)
            dcc_project_config_path = os.path.join(project_config_env_dir, tp.Dcc.get_name(), module_config_name)
            dcc_version_project_config_path = os.path.join(
                project_config_env_dir, tp.Dcc.get_name(), tp.Dcc.get_version_name(), module_config_name)
        except RuntimeError:
            LOGGER.warning('No Configuration Module found for project: {}'.format(project_name))

        return [project_config_path, dcc_project_config_path, dcc_version_project_config_path]

    def _get_config_paths(self, project_name, module_config_name, skip_non_existent=True):
        """
        Returns a list of valid paths where configuration files can be located
        :return: list(str)
        """

        found_paths = list()
        paths_to_found = self._get_artella_config_paths(module_config_name=module_config_name)
        paths_to_found.extend(
            self._get_project_config_paths(project_name=project_name, module_config_name=module_config_name))

        for p in paths_to_found:
            if not p:
                continue
            if skip_non_existent and not os.path.isfile(p):
                continue
            found_paths.append(p)

        return found_paths

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
        all_config_paths = self._get_config_paths(
            project_name=project_name, module_config_name=module_config_name, skip_non_existent=False)
        valid_config_paths = self._get_config_paths(project_name=project_name, module_config_name=module_config_name)
        if not valid_config_paths:
            raise RuntimeError(
                'Impossible to load configuration "{}"  for project "{}" because it does not exists in any of '
                'the configuration folders: {}'.format(config_name, project_name, ''.join(all_config_paths)))

        project_config_path = valid_config_paths[-1]
        config_data = metayaml.read(valid_config_paths, config_dict)
        if not config_data:
            raise RuntimeError(
                'Project Configuration File for {} Project is empty! {}'.format(self, project_config_path))

        # We store path where configuration file is located in disk
        if 'config' in config_data and 'path' in config_data['config']:
            raise RuntimeError(
                'Project Configuration File for {} Project cannot contains '
                'config section with path attribute! {}'.format(self, project_config_path))
            return
        if 'config' in config_data:
            config_data['config']['path'] = project_config_path
        else:
            config_data['config'] = {'path': project_config_path}

        return config_data


def get_config(project, config_name, config_dict=None, parser_class=ArtellaConfigurationParser):
    """
    Returns a configuration with the given arguments and for the given project
    :param project: ArtellaProject
    :param config_name: str
    :param config_dict: dict
    :param parser_class: ArtellaConfigurationParser
    :param environment: str (optional)
    :return: ArtellaConfiguration
    """

    new_cfg = ArtellaConfiguration(
        project_name=project.get_clean_name(),
        config_name=config_name,
        config_dict=config_dict,
        parser_class=parser_class,
        environment=os.environ.get('{}_env'.format(project.get_clean_name()), 'DEVELOPMENT')
    )

    return new_cfg
