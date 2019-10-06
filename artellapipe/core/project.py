#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains basic implementation for Artella Projects
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import re
import sys
import json
import locale
import logging
import tempfile
import traceback
import webbrowser
try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote
from collections import OrderedDict

import six

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp
from tpPyUtils import python, strings, decorators, osplatform, jsonio, fileio, path as path_utils, \
    folder as folder_utils
from tpQtLib.core import qtutils

from artellapipe.core import defines, artellalib, artellaclasses, asset, node, syncdialog, assetsviewer, sequence, shot
from artellapipe.gui import tray, defines as gui_defines
from artellapipe.utils import resource, tag

LOGGER = logging.getLogger()


class ArtellaProject(object):

    PROJECT_RESOURCE = None
    TRAY_CLASS = tray.ArtellaTray
    SHELF_CLASS = tp.Shelf
    ASSET_CLASS = asset.ArtellaAsset
    SEQUENCE_CLASS = sequence.ArtellaSequence
    SHOT_CLASS = shot.ArtellaShot
    ASSETS_VIEWER_CLASS = assetsviewer.AssetsViewer
    ASSET_NODE_CLASS = node.ArtellaAssetNode
    SYNC_FILES_DIALOG_CLASS = syncdialog.ArtellaSyncFileDialog
    SYNC_PATHS_DIALOG_CLASS = syncdialog.ArtellaSyncPathDialog
    TAG_NODE_CLASS = asset.ArtellaTagNode

    class DataVersions(object):
        SHOT = '0.0.1'

    class DataExtensions(object):
        pass

    def __init__(self, settings=None):
        super(ArtellaProject, self).__init__()

        self._name = None
        self._project_env_var = None
        self._logger = None
        self._tray = None
        self._config = None
        self._id_number = None
        self._id = None
        self._url = None
        self._full_id = None
        self._asset_types = list()
        self._asset_files = list()
        self._asset_must_files = list()
        self._wip_status = None
        self._publish_status = None
        self._shelf_icon = None
        self._tray_icon = None
        self._project_icon = None
        self._folders_to_register = list()
        self._emails = list()
        self._progress_bar_color0 = None
        self._progress_bar_color1 = None
        self._asset_ignored_paths = list()
        self._assets_library_file_types = dict()
        self._asset_data_filename = None
        self._tag_types = list()
        self._outliner_categories = dict()
        self._shot_regex = None
        self._shot_file_types = list()
        self._shot_extension = None
        self._shaders_extension = None
        self._playblast_presets_url = None

        self._registered_asset_classes = list()
        self._asset_classes_types = dict()
        self._registered_asset_file_type_classes = list()
        self._asset_classes_file_types = dict()

        self._production_info = None
        self._sequences = list()
        self._shots = list()

        self._settings = settings

        # To make sure that all variables are properly initialized we must call init_config first
        self.init_config()
        self.init_settings()
        self._logger = self.create_logger()[1]

        # self._register_asset_classes()
        self._register_asset_file_types()

    # ==========================================================================================================
    # PROPERTIES
    # ==========================================================================================================

    @property
    def name(self):
        """
        Returns the name of the Artella project
        :return: str
        """

        return self._name

    @property
    def settings(self):
        """
        Returns the settings of the project
        :return: ArtellaProjectSettings
        """

        return self._settings

    @property
    def id(self):
        """
        Returns ID of the project
        :return: str
        """

        return self._id

    @property
    def id_number(self):
        """
        Returns ID number of the project
        :return: str
        """

        return self._id_number

    @property
    def full_id(self):
        """
        Returns full ID of the project
        :return: str
        """

        return self._full_id

    @property
    def id_path(self):
        """
        Returns ID path of this Artella project
        :return: str
        """

        return '{}{}{}'.format(self._id_number, os.sep, self._id)

    @property
    def project_url(self):
        """
        Returns URL to official Plot Twist web page
        :return: str
        """

        return self._url

    @property
    def project_environment_variable(self):
        """
        Returns name used to store path to the current project
        :return: str
        """

        return self._project_env_var

    @property
    def logger(self):
        """
        Returns the logger used by the Artella project
        :return: Logger
        """

        return self._logger

    @property
    def tray(self):
        """
        Returns the tray used by the Artella project
        :return: Tray
        """

        return self._tray

    @property
    def asset_types(self):
        """
        Returns the list of asset types being used by the Artella project
        :return: list(str)
        """

        return self._asset_types

    @property
    def asset_files(self):
        """
        Returns the list of asset files being used by the Artella project
        :return: list(str)
        """

        return self._asset_files

    @property
    def asset_must_files(self):
        """
        Returns the list of asset files that an asset need to have published to consider the asset ready for
        production
        :return: list(str)
        """

        return self._asset_must_files

    @property
    def tag_types(self):
        """
        Returns the list of types that can be used to categorize all the elements of the project
        :return: list(str)
        """

        return self._tag_types

    @property
    def outliner_categories(self):
        """
        Returns a dictionary that maps tag types with outliner categories
        :return: dict
        """

        return self._outliner_categories

    @property
    def working_status(self):
        """
        Returns the name of the working status
        :return: str
        """

        return self._wip_status

    @property
    def publish_status(self):
        """
        Returns the name of the publish status
        :return: str
        """

        return self._publish_status

    @property
    def icon_name(self):
        """
        Returns the name of the icon by Artella project
        :return: str
        """

        return self._project_icon

    @property
    def icon(self):
        """
        Returns the icon used by the Artella project
        :return: QIcon
        """

        return self.resource.icon(self._project_icon, theme='logos')

    @property
    def tray_icon_name(self):
        """
        Returns the name of the icon used by Artella project tray
        :return: str
        """

        return self._tray_icon

    @property
    def tray_icon(self):
        """
        Retrusn the tray icon used by Artella project tray
        :return: QIcon
        """

        return self.resource.icon(self._tray_icon)

    @property
    def resource(self):
        """
        Returns the class used by the project to load resources (icons, images, fonts, etc)
        :return: Resource
        """

        return resource.ResourceManager()

    @property
    def emails(self):
        """
        Returns list of emails that will be used when sending an email
        :return: list(str)
        """

        return self._emails

    @property
    def assets_library_file_types(self):
        """
        Returns file types supported by assets library
        :return: dict
        """

        return self._assets_library_file_types

    @property
    def progress_bar_color_0(self):
        """
        Returns color 0 used in progress bar color gradient
        :return: str
        """

        return self._progress_bar_color0

    @property
    def progress_bar_color_1(self):
        """
        Returns color 1 used in progress bar color gradient
        :return: str
        """

        return self._progress_bar_color1

    @property
    def tag_type_id(self):
        """
        Returns tag name used to identify assets for the current project
        :return: str
        """

        return '{}_TAG'.format(self.get_clean_name().upper())

    @property
    def shot_file_types(self):
        """
        Returns of shot files supported by the project
        :return: list(str)
        """

        return self._shot_file_types

    @property
    def shot_extension(self):
        """
        Returns extesnsion used to stored shot files
        :return: str
        """

        return self._shot_extension

    @property
    def shaders_extension(self):
        """
        Returns extension usded by shaders files
        :return: str
        """

        return self._shaders_extension

    @property
    def playblast_presets_url(self):
        """
        Returns the URL where playblast presets are located
        :return: str
        """

        return self._playblast_presets_url

    @property
    def namemanager(self):
        """
        Returns name manager widget used to manage nomenclature in the project
        :return: NameWidget
        """

        return self._namemanager

    # ==========================================================================================================
    # INITIALIZATION, CONFIG & SETTINGS
    # ==========================================================================================================

    def init(self, force_skip_hello=False):
        """
        This function initializes Artella project
        :param force_skip_hello: bool, Whether the hello window should be showed or not
        """

        if force_skip_hello:
            os.environ['ARTELLA_PIPELINE_SHOW'] = ''

        if tp.Dcc.get_name() != tp.Dccs.Unknown:
            self.update_paths()
            self.set_environment_variables()
            self.create_shelf()
            self.create_menu()
            self._tray = self.create_tray()
            self.update_project()

    def get_project_path(self):
        """
        Returns path where default Artella project is located
        :return: str
        """

        return path_utils.clean_path(os.path.dirname(__file__))

    def get_configurations_folder(self):
        """
        Returns folder where project configuration files are loaded
        :return: str
        """

        if os.environ.get(defines.ARTELLA_CONFIGURATION_ENV, None):
            return os.environ[defines.ARTELLA_CONFIGURATION_ENV]
        else:
            from artellapipe import config
            return os.path.dirname(config.__file__)

    def get_config_path(self):
        """
        Returns path where default Artella project config is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_CONFIG_FILE_NAME))

    def get_changelog_path(self):
        """
        Returns path where default Artella project changelog is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_CHANGELOG_FILE_NAME))

    def get_naming_path(self):
        """
        Returns path where default Artella naming configuration is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_DEFAULT_NAMING_FILE_NAME))

    def get_shelf_path(self):
        """
        Returns path where default Artella shelf file is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_SHELF_FILE_NAME))

    def get_menu_path(self):
        """
        Returns path where default Artella shelf file is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_MENU_FILE_NAME))

    def get_version_path(self):
        """
        Returns path where version file is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME))

    def get_version(self):
        """
        Returns the current version of the tools
        :return: str
        """

        version_file_path = self.get_version_path()
        if not os.path.isfile(version_file_path):
            self.logger.warning('No Version File found "{}" for project "{}"!'.format(version_file_path, self.name))
            return

        version_data = fileio.get_file_lines(version_file_path)
        if not version_data:
            self.logger.warning('Version File "{}" does not contain any version information!'.format(version_file_path))
            return

        for line in version_data:
            if not line.startswith('__version__'):
                continue
            version_split = line.split('=')
            if not version_split:
                self.logger.warning('Version data in file "{}" is not formatted properly!'.format(version_file_path))
                return

            return version_split[-1].strip()[1:-1]

        return 'Not Found!'

    def solve_name(self, rule_name, *args, **kwargs):
        """
        Resolves name with given rule and attributes
        :param rule_name: str
        :param args: list
        :param kwargs: dict
        """

        current_rule = self._namemanager.get_active_rule()
        self._namemanager.set_active_rule(rule_name)
        solved_name = self._namemanager.solve(*args, **kwargs)
        if current_rule:
            if rule_name != current_rule.name:
                self._namemanager.set_active_rule(current_rule.name)
        else:
            self._namemanager.set_active_rule(None)

        return solved_name

    def get_templates(self):
        """
        Returns a list with all available templates
        :return: list(str)
        """

        return namemanager.NameManager.get_templates()

    def parse_template(self, template_name, path_to_parse):
        """
        Parses given path in the given template
        :param template_name: str
        :param path_to_parse: str
        :return: list(str)
        """

        return namemanager.NameManager.parse_template(template_name=template_name, path_to_parse=path_to_parse)

    def check_template_validity(self, template_name, path_to_check):
        """
        Returns whether given path matches given pattern or not
        :param template_name: str
        :param path_to_check: str
        :return: bool
        """

        return namemanager.NameManager.check_template_validity(tepmlate_name=template_name, path_to_check=path_to_check)

    def format_template(self, template_name, template_tokens):
        """
        Returns template path filled with tempalte tokens data
        :param template_name: str
        :param template_tokens: dict
        :return: str
        """

        return namemanager.NameManager.format_template(template_name=template_name, template_tokens=template_tokens)

    def get_config_data(self):
        """
        Returns the config data of the project
        :return: dict
        """

        config_path = self.get_config_path()

        if not config_path or not os.path.isfile(config_path):
            tp.Dcc.error('Project Configuration File for {} Project not found! {}'.format(self, config_path))
            return

        with open(config_path, 'r') as f:
            project_config_data = json.load(f, object_hook=OrderedDict)
        if not project_config_data:
            tp.Dcc.error('Project Configuration File for {} Project is empty! {}'.format(self, config_path))
            return

        return project_config_data

    def init_config(self):
        """
        Function that reads project configuration file and initializes project variables properly
        This function can be extended in new projects
        """

        project_config_data = self.get_config_data()
        if not project_config_data:
            return False

        self._name = project_config_data.get(defines.ARTELLA_CONFIG_PROJECT_NAME, defines.ARTELLA_DEFAULT_PROJECT_NAME)
        self._project_env_var = project_config_data.get(
            defines.ARTELLA_CONFIG_ENVIRONMENT_VARIABLE, defines.ARTELLA_DEFAULT_ENVIRONMENT_VARIABLE)
        self._id_number = project_config_data.get(defines.ARTELLA_CONFIG_PROJECT_NUMBER, -1)
        self._id = project_config_data.get(defines.ARTELLA_CONFIG_PROJECT_ID, -1)
        self._full_id = '{}/{}/{}/'.format(defines.ARTELLA_PRODUCTION_FOLDER, self._id_number, self._id)
        self._url = project_config_data.get(defines.ARTELLA_PROJECT_URL, None)
        self._version_file = project_config_data.get(
            defines.ARTELLA_VERSION_FILE_NAME_ATTRIBUTE_NAME, defines.ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME)
        self._asset_types = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_TYPES, list())
        self._asset_files = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_FILES, list())
        self._asset_must_files = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_MUST_FILES_ATTRIBUTE_NAME, list())
        self._wip_status = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_WIP_STATUS, None)
        self._publish_status = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_PUBLISH_STATUS, None)
        self._project_icon = project_config_data.get(
            defines.ARTELLA_PROJECT_ICON, gui_defines.ARTELLA_PROJECT_DEFAULT_ICON)
        self._shelf_icon = project_config_data.get(defines.ARTELLA_CONFIG_SHELF_ICON, None)
        self._tray_icon = project_config_data.get(defines.ARTELLA_CONFIG_TRAY_ICON, None)
        self._folders_to_register = project_config_data.get(
            defines.ARTELLA_CONFIG_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME,
            defines.ARTELLA_CONFIG_DEFAULT_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME)
        self._emails = project_config_data.get(defines.ARTELLA_CONFIG_EMAIL_ATTRIBUTE_NAME, list())
        self._progress_bar_color0 = project_config_data.get(
            defines.ARTELLA_PROGRESS_BAR_COLOR_0_ATTRIBUTE_NAME, '255, 255, 255')
        self._progress_bar_color1 = project_config_data.get(
            defines.ARTELLA_PROGRESS_BAR_COLOR_1_ATTRIBUTE_NAME, '255, 255, 255')
        self._asset_ignored_paths = project_config_data.get(
            defines.ARTELLA_ASSETS_IGNORED_PATHS_ATTRIBUTE_NAME, list())
        self._assets_library_file_types = project_config_data.get(
            defines.ARTELLA_ASSETS_LIBRARY_SUPPORTED_TYPES_ATTRIBUTE_NAME, dict())
        self._asset_data_filename = project_config_data.get(defines.ARTELLA_ASSET_DATA_FILENAME_ATTRIBUTE_NAME, None)
        self._tag_types = project_config_data.get(defines.ARTELLA_CONFIG_TAG_TYPES_ATTRIBUTE_NAME, list())
        self._outliner_categories = project_config_data.get(
            defines.ARTELLA_CONFIG_OUTLINER_CATEGORIES_ATTRIBUTE_NAME, dict())
        self._shot_regex = project_config_data.get(defines.ARTELLA_CONFIG_SHOT_REGEX_ATTRIBUTE_NAME, '*')
        self._shot_file_types = project_config_data.get(defines.ARTELLA_SHOT_FILE_TYPES_ATTRIBUTE_NAME, list())
        self._shot_extension = project_config_data.get(defines.ARTELLA_SHOT_EXTENSION_ATTRIBUTE_NAME, '.shot')
        self._shaders_extension = project_config_data.get(defines.ARTELLA_SHADERS_EXTENSION_ATTRIBUTE_NAME, None)
        self._playblast_presets_url = project_config_data.get(
            defines.ARTELLA_PLAYBLAST_PRESETS_URL_ATTRIBUTE_NAME, None)

        if self._id_number == -1 or self._id == -1 or not self._wip_status or not self._publish_status:
            tp.Dcc.error('Project Configuration File for Project: {} is not valid!'.format(self.name))
            return False

    def init_settings(self):
        """
        Function that initializes project settings file
        """

        self._settings = self._settings if self._settings else self._create_new_settings()

    def get_clean_name(self):
        """
        Returns a cleaned version of the project name (without spaces and in lowercase)
        :return: str
        """

        return self.name.replace(' ', '').lower()

    def get_data_path(self):
        """
        Returns path where user data for Artella project should be located
        This path is mainly located to store tools configuration files and log files
        :return: str
        """

        data_path = os.path.join(os.getenv('APPDATA'), self.get_clean_name())
        if not os.path.isdir(data_path):
            os.makedirs(data_path)

        return data_path

    def get_settings_file(self):
        """
        Returns file path of the window settings file
        :return: str
        """

        return os.path.expandvars(os.path.join(self.get_data_path(), '{}.cfg'.format(self.get_clean_name())))

    def create_logger(self):
        """
        Creates and initializes Artella project logger
        """

        from tpPyUtils import log as log_utils

        log_path = self.get_data_path()
        if not os.path.exists(log_path):
            raise RuntimeError('{} Log Path {} does not exists!'.format(self.name, log_path))

        log = log_utils.create_logger(logger_name=self.get_clean_name(), logger_path=log_path)
        logger = log.logger

        if '{}_DEV'.format(self.get_clean_name().upper()) in os.environ and os.environ.get(
                '{}_DEV'.format(self.get_clean_name().upper())) in ['True', 'true']:
            logger.setLevel(log_utils.LoggerLevel.DEBUG)
        else:
            logger.setLevel(log_utils.LoggerLevel.WARNING)

        return log, logger

    def update_paths(self):
        """
        Updates system path with custom paths needed by Artella project
        This function is called during project initialization and can be extended in new projects
        """

        # We add Artella Python Scripts folder if it is not already added
        artella_folder = artellalib.get_artella_python_folder()
        if artella_folder not in sys.path:
            sys.path.append(artella_folder)

    def set_environment_variables(self):
        """
        Initializes environment variables needed by the Artella Project
        This function is called during project initialization and can be extended in new projects
        :return:
        """

        self.logger.debug('Initializing environment variables for: {}'.format(self.name))

        try:
            artellalib.update_local_artella_root()
            artella_var = os.environ.get(defines.ARTELLA_ROOT_PREFIX, None)
            self.logger.debug('Artella environment variable is set to: {}'.format(artella_var))
            if artella_var and os.path.exists(artella_var):
                os.environ[self._project_env_var] = '{}{}/{}/{}/'.format(
                    artella_var, defines.ARTELLA_PRODUCTION_FOLDER, self._id_number, self._id)
            else:
                self.logger.warning('Impossible to set Artella environment variable!')
        except Exception as e:
            self.logger.debug(
                'Error while setting {0} Environment Variables. {0} Pipeline Tools may not work properly!'.format(
                    self._name.title()))
            self.logger.error('{} | {}'.format(e, traceback.format_exc()))

        icons_paths = resource.ResourceManager().get_resources_paths()
        # icons_paths = [
        #     artellapipe.resource.RESOURCES_FOLDER,
        #     self.resource.RESOURCES_FOLDER
        # ]

        current_paths = list()
        if os.environ.get('XBMLANGPATH'):
            if osplatform.is_mac():
                current_paths = os.environ['XBMLANGPATH'].split(':')
            else:
                current_paths = os.environ['XBMLANGPATH'].split(';')

        for p in icons_paths:
            for root, _, _ in os.walk(p):
                if root in current_paths:
                    continue
                if tp.is_maya():
                    if osplatform.is_mac():
                        os.environ['XBMLANGPATH'] = os.environ.get('XBMLANGPATH') + ':' + root
                    else:
                        os.environ['XBMLANGPATH'] = os.environ.get('XBMLANGPATH') + ';' + root

        self.logger.debug('=' * 100)
        self.logger.debug("{} Pipeline initialization completed!".format(self.name))
        self.logger.debug('=' * 100)
        self.logger.debug('*' * 100)
        self.logger.debug('-' * 100)
        self.logger.debug('\n')

    def create_shelf(self):
        """
        Creates Artella Project shelf
        """

        self.logger.debug('Building {} Tools Shelf'.format(self.name.title()))

        shelf_category_icon = None
        if self.resource and self._shelf_icon:
            shelf_category_icon = self.resource.icon(self._shelf_icon, theme=None)
        project_shelf = self.SHELF_CLASS(name=self._name.replace(' ', ''), category_icon=shelf_category_icon)
        icons_paths = resource.ResourceManager().get_resources_paths(key='shelf')
        project_shelf.ICONS_PATHS = icons_paths
        project_shelf.create(delete_if_exists=True)
        shelf_file = self.get_shelf_path()
        if not shelf_file or not os.path.isfile(shelf_file):
            self.logger.warning('Shelf File for Project {} is not valid: {}'.format(self._name, shelf_file))
            return
        project_shelf.build(shelf_file=shelf_file)
        project_shelf.set_as_active()

    def create_menu(self):
        """
        Creates Artella Project menu
        """

        self.logger.debug('Building {} Tools Menu ...'.format(self.name.title()))
        menu_name = self._name.title()
        if tp.is_maya():
            from tpMayaLib.core import menu
            try:
                menu.remove_menu(menu_name)
            except Exception:
                pass

        try:
            project_menu = tp.Menu(name=menu_name)
            menu_file = self.get_menu_path()
            if menu_file and os.path.isfile(menu_file):
                project_menu.create_menu(file_path=menu_file, parent_menu=menu_name)
        except Exception as e:
            self.logger.warning(
                'Error during {} Tools Menu creation: {} | {}'.format(self.name.title(), e, traceback.format_exc()))

    def get_folders_to_register(self, full_path=True):
        """
        Returns folders to register paths
        :param full_path: bool, Whether to return full path of the folder or not
        :return: list(str)
        """

        if not self._folders_to_register:
            return list()

        if not full_path:
            return self._folders_to_register
        else:
            paths_to_return = list()
            for p in self._folders_to_register:
                paths_to_return.append(path_utils.clean_path(os.path.join(self.get_project_path(), p)))
            return paths_to_return

    def message(self, msg, title=None):
        """
        Shows tray given message in OS tray. If tray is not available, the message will be
        output in the debug logger
        :param msg: str, message to show
        :param title: str, title to show; if None, the project name will be used
        :return:
        """

        if not title:
            title = self.name.title()

        if osplatform.is_windows():
            if self.tray:
                self.tray.show_message(title=title, msg=msg)
            else:
                self.logger.debug(str(msg))
        else:
            self.logger.debug(str(msg))

    # ==========================================================================================================
    # TRAY
    # ==========================================================================================================

    def create_tray(self):
        """
        Creates Artella Project tray
        """

        if not self.TRAY_CLASS:
            return

        self.logger.debug('Creating {} Tools Tray ...'.format(self.name.title()))
        tray = self.TRAY_CLASS(project=self)

        return tray

    def open_artella_project_url(self):
        """
        Opens Artella Project web page in browser
        """

        webbrowser.open(self.get_artella_url())

    def send_email(self, title=None):
        """
        Opens email application with proper info
        """

        if not title:
            title = self.name.title()

        webbrowser.open("mailto:%s?subject=%s" % (','.join(self._emails), quote(title)))

    # ==========================================================================================================
    # PROJECT
    # ==========================================================================================================

    def get_path(self, force_update=False):
        """
        Returns path where project is located
        :param force_update: bool, Whether to force the update of project path is environment variables are not setup
        :return: str
        """

        env_var = os.environ.get(self._project_env_var, None)

        if not env_var or force_update:
            self.update_project()
            env_var = os.environ.get(self._project_env_var, None)

            # We force the launch of Artella
            if not env_var:
                try:
                    if tp.is_maya():
                        artellalib.launch_artella_app()
                        artellalib.load_artella_maya_plugin()
                    self.update_project()
                except Exception as e:
                    raise RuntimeError(
                        '{} Project not set up properly after launching Artella. Is Artella Running?'.format(
                            self.name.title()))

        env_var = os.environ.get(self._project_env_var, None)
        if not env_var:
            raise RuntimeError(
                '{} Project not setup properly. Please contact TD to fix this problem'.format(self.name.title()))

        return os.environ.get(self._project_env_var)

    def get_production_path(self):
        """
        Returns path where Production data for current project is stored
        :return: str
        """

        project_path = self.get_path()
        if not project_path:
            LOGGER.warning('Impossible to retrieve productoin path because Artella project is not setup!')
            return

        return path_utils.clean_path(os.path.join(project_path, defines.ARTELLA_PRODUCTION_FOLDER_NAME))

    def get_temp_path(self, *args):
        """
        Returns temporary folder path of the project
        :return: str
        """

        temp_path = '{temp}/' + self.get_clean_name() + '/pipeline/{user}'

        return path_utils.clean_path(os.path.join(self._format_path(temp_path), *args))

    def resolve_path(self, path_to_resolve):
        """
        Converts path to a valid full path
        :param path_to_resolve: str
        :return: str
        """

        path_to_resolve = path_to_resolve.replace('\\', '/')
        project_var = os.environ.get(self._project_env_var)
        if not project_var:
            return path_to_resolve

        if path_to_resolve.startswith(project_var):
            path_to_resolve = path_to_resolve.replace(project_var, '${}/'.format(self._project_env_var))

        return path_to_resolve

    def fix_path(self, path_to_fix):
        """
        Converts path to a path relative to project environment variable
        :param path_to_fix: str
        :return: str
        """

        path_to_fix = path_to_fix.replace('\\', '/')
        project_var = os.environ.get(self._project_env_var)
        if not project_var:
            return path_to_fix

        if path_to_fix.startswith('${}/'.format(self._project_env_var)):
            path_to_fix = path_to_fix.replace('${}/'.format(self._project_env_var), project_var)
        elif path_to_fix.startswith('${}/'.format(defines.ARTELLA_ROOT_PREFIX)):
            path_to_fix = path_to_fix.replace('${}/'.format(defines.ARTELLA_ROOT_PREFIX), project_var)

        return path_to_fix

    def relative_path(self, full_path):
        """
        Returns relative path of the given path relative to Project path
        :param full_path: str
        :return: str
        """

        return path_utils.clean_path(os.path.relpath(full_path, self.get_path()))

    def get_artella_url(self):
        """
        Returns Artella URL of the project
        :return: str
        """

        return '{}/project/{}/files'.format(defines.ARTELLA_WEB, self.id)

    def get_artella_assets_url(self):
        """
        Returns URL of the Artella Assets of the project are located
        :return: str
        """

        return '{}/Assets/'.format(self.get_artella_url())

    def update_project(self):
        """
        Sets the current Maya project to the path where Artella project is located inside Artella folder
        """

        try:
            if tp.is_maya():
                import tpMayaLib as maya
                self.logger.debug('Setting {} Project ...'.format(self.name))
                project_folder = os.environ.get(self._project_env_var, 'folder-not-defined')
                if project_folder and os.path.exists(project_folder):
                    maya.cmds.workspace(project_folder, openWorkspace=True)
                    self.logger.debug('{} Project setup successfully! => {}'.format(self.name, project_folder))
                else:
                    self.logger.warning('Unable to set {} Project! => {}'.format(self.name, project_folder))
        except Exception as e:
            self.logger.error('{} | {}'.format(str(e), traceback.format_exc()))

    def open_in_artella(self):
        """
        Opens project Artella web page in user web browser
        """

        project_url = self.get_artella_url()
        webbrowser.open(project_url)

    def open_folder(self):
        """
        Opens folder where Artella project is located in user computer
        """

        project_path = self.get_path()
        folder_utils.open_folder(project_path)

    def get_progress_bar(self):
        """
        Creates and returns a new instance of project Progress bar
        :return: QProgressBar
        """

        new_progress_bar = QProgressBar()
        new_progress_bar.setStyleSheet(
            "QProgressBar {border: 0px solid grey; "
            "border-radius:4px; padding:0px} "
            "QProgressBar::chunk {background: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 1, stop: 0 "
            "rgb(" + self.progress_bar_color_0 + "), stop: 1 rgb(" + self.progress_bar_color_1 + ")); }")

        return new_progress_bar

    # ==========================================================================================================
    # SYNC
    # ==========================================================================================================

    def sync_files(self, files):
        """
        Creates an return a new instance of the Artella files sync dialog
        :param files: list(str)
        """

        files = python.force_list(files)

        sync_dialog = self.SYNC_FILES_DIALOG_CLASS(project=self, files=files)
        sync_dialog.sync()

    def sync_paths(self, paths):
        """
        Creates an return a new instance of the Artella paths sync dialog
        :param paths: list(str)
        """

        paths = python.force_list(paths)

        sync_dialog = self.SYNC_PATHS_DIALOG_CLASS(project=self, paths=paths)
        sync_dialog.sync()

    # ==========================================================================================================
    # FILES
    # ==========================================================================================================

    def save_scene(self, notify=False):
        """
        Saves current scene and cleans invalid data
        :param notify: bool
        """

        tp.Dcc.clean_scene()
        tp.Dcc.save_current_scene(force=False)
        scene_name = tp.Dcc.scene_name()
        if not scene_name:
            LOGGER.warning('File was not saved!')
            return False

        if tp.is_maya():
            from tpMayaLib.core import helpers
            helpers.clean_student_line()

        if notify:
            self.tray.show_message(title='Save File', msg='File saved successfully!')

        return True

    def lock_file(self, file_path=None, notify=False):
        """
        Locks given file in Artella
        :param file_path: str
        :param notify: bool
        :return: bool
        """

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            return False

        valid_lock = artellalib.lock_file(file_path=file_path, force=True)
        if not valid_lock:
            return False

        if notify:
            self.tray.show_message(title='Lock File', msg='File locked successfully!')

        return True

    def unlock_file(self, file_path=None, notify=False, warn_user=True):
        """
        Unlocks current file in Artella
        :param file_path: str
        :param notify: bool
        :param warn_user: bool
        :return: bool
        """

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            LOGGER.warning('File Path "{}" is not valid!'.format(valid_path))
            return False

        if warn_user:
            msg = 'If changes in file: \n\n{}\n\n are not submitted to Artella yet, submit them before ' \
                  'unlocking the file please. \n\n Do you want to continue?'.format(file_path)
            res = tp.Dcc.confirm_dialog(
                title='Unlock File', message=msg,
                button=['Yes', 'No'], default_button='Yes', cancel_button='No', dismiss_string='No')
            if res != tp.Dcc.DialogResult.Yes:
                return False

        artellalib.unlock_file(file_path=file_path)
        if notify:
            self.tray.show_message(title='Unlock File', msg='File unlocked successfully!')

        return True

    def check_lock_status(self, file_path=None, show_message=False):
        """
        Returns the current lock status of the file in Artella
        :param file_path: stro
        :param show_message: bool
        :return: bool
        """

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            LOGGER.warning('File Path "{}" is not valid!'.format(valid_path))
            return False

        in_edit_mode, is_locked_by_me = artellalib.is_locked(file_path=file_path)
        if not in_edit_mode:
            msg = 'File is not locked!'
            color = 'white'
        else:
            if is_locked_by_me:
                msg = 'File locked by you!'
                color = 'green'
            else:
                msg = 'File locked by other user!'
                color = 'red'

        if show_message:
            tp.Dcc.show_message_in_viewport(msg=msg, color=color)

        if not in_edit_mode:
            return False

        return True

    def upload_working_version(self, file_path=None, skip_saving=False, notify=False, comment=None, force=False):
        """
        Uploads a new working version of the given file
        :param file_path: str
        :param skip_saving: bool
        :param notify: bool
        :param comment: str
        :param force: bool
        :return: bool
        """

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            LOGGER.warning('File Path "{}" is not valid!'.format(valid_path))
            return False

        short_path = file_path.replace(self.get_assets_path(), '')[1:]

        history = artellalib.get_asset_history(file_path)
        file_versions = history.versions
        if not file_versions:
            current_version = -1
        else:
            current_version = 0
            for v in file_versions:
                if int(v[0]) > current_version:
                    current_version = int(v[0])
        current_version += 1

        if comment:
            comment = str(comment)
        else:
            comment = qtutils.get_comment(
                text_message='Make New Version ({}) : {}'.format(
                    current_version, short_path), title='Comment', parent=tp.Dcc.get_main_window())

        if comment:
            artellalib.upload_new_asset_version(file_path=file_path, comment=comment, skip_saving=skip_saving)
            if notify:
                self.tray.show_message(
                    title='New Working Version', msg='Version {} uploaded to Artella server successfully!'.format(
                        current_version))
            return True

        return False

    # ==========================================================================================================
    # ASSETS
    # ==========================================================================================================

    def register_asset_class(self, asset_class):
        """
        Registers a new asset class into the project
        :param asset_class: cls
        """

        if asset_class not in self._registered_asset_classes:
            self._registered_asset_classes.append(asset_class)

    def register_asset_file_type(self, asset_file_type_class):
        """
        Registers a new asset file type class into the project
        :param asset_file_type_class: cls
        """

        if asset_file_type_class not in self._registered_asset_file_type_classes:
            self._registered_asset_file_type_classes.append(asset_file_type_class)

    def get_assets_path(self):
        """
        Returns path where project assets are located
        :return: str
        """

        assets_path = os.path.join(self.get_path(), defines.ARTELLA_ASSETS_FOLDER_NAME)

        return assets_path

    def is_valid_assets_path(self):
        """
        Returns whether current asset path exists or not
        :return: bool
        """

        assets_path = self.get_assets_path()
        if not assets_path or not os.path.exists(assets_path):
            return False

        return True

    def is_valid_asset_file_type(self, file_type):
        """
        Returns whether the current file type is valid or not for current project
        :param file_type: str
        :return: bool
        """

        return file_type in self._asset_classes_file_types.keys()

    def get_asset_file(self, file_type, extension=None):
        """
        Returns asset file object class linked to given file type for current project
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        if not self.is_valid_asset_file_type(file_type):
            return

        asset_classes = self._asset_classes_file_types[file_type]
        if not asset_classes:
            LOGGER.warning('No Asset Class found for file of type: "{}"'.format(file_type))
            return

        if len(asset_classes) == 0:
            return asset_classes[0]
        else:
            if extension:
                for asset_class in asset_classes:
                    if extension in asset_class.FILE_EXTENSIONS:
                        return asset_class
            else:
                return asset_classes[0]

    def get_asset_data_file_path(self, asset_path):
        """
        Returns asset data file path of given asset
        :param asset_path: str
        :return: str
        """

        return os.path.join(asset_path, defines.ARTELLA_WORKING_FOLDER, self._asset_data_filename)

    def create_asset(self, asset_data, category=None):
        """
        Returns a new asset with the given data
        :param asset_data: dict
        :param category: str
        """

        if category and category in self._asset_classes_types:
            return self._asset_classes_types[category](project=self, asset_data=asset_data)
        else:
            return self.ASSET_CLASS(project=self, asset_data=asset_data)

    def create_asset_in_artella(self, asset_name, asset_path, folders_to_create=None):
        """
        Creates a new asset in Artella
        :param asset_name: str
        :param asset_path: str
        :param folders_to_create: list(str) or None
        """

        valid_create = artellalib.create_asset(asset_name, asset_path)
        if not valid_create:
            LOGGER.warning('Impossible to create Asset {} in Path: {}!'.format(asset_name, asset_path))
            return

        if folders_to_create:
            for folder_name in folders_to_create:
                file_path = path_utils.clean_path(os.path.join(asset_path, asset_name, defines.ARTELLA_WORKING_FOLDER))
                artellalib.new_folder(file_path, folder_name)

        return True

    def find_all_assets(self, asset_name=None, asset_path=None):
        """
        Returns a list of all assets in the project
        :param asset_name: str, If given, a list with the given item will be returned instead
        :param asset_path: str, If given, asset will be found in given path
        :return: variant, ArtellaAsset or list(ArtellaAsset)
        """

        assets_path = self.get_assets_path()
        if not self.is_valid_assets_path():
            self.logger.warning('Impossible to retrieve assets from invalid path: {}'.format(assets_path))
            return

        if not assets_path or not os.path.exists(assets_path):
            self.logger.warning('Impossible to retrieve assets from invalid path: {}'.format(assets_path))
            return list()

        if not self._asset_data_filename:
            self.logger.warning(
                'Impossible to retrieve {} assets because asset data file name is not defined!'.format(
                    self._name.title()))
            return

        found_assets = list()

        if asset_path:
            if not os.path.isdir(asset_path):
                LOGGER.warning('Impossible to retrieve asset from non-existent path: {}!'.format(asset_path))
                return
            if asset_name:
                _asset_name = os.path.basename(asset_path)
                if asset_name and asset_name != _asset_name:
                    return
            new_asset = self.get_asset_from_path(asset_path=asset_path)
            if new_asset:
                found_assets.append(new_asset)
        else:
            for root, dirs, files in os.walk(assets_path):
                if dirs and defines.ARTELLA_WORKING_FOLDER in dirs:
                    _asset_name = os.path.basename(root)
                    if asset_name and asset_name != _asset_name:
                        continue
                    new_asset = self.get_asset_from_path(asset_path=root)
                    if new_asset:
                        found_assets.append(new_asset)

        return found_assets

    def find_asset(self, asset_name=None, asset_path=None, allow_multiple_instances=True):
        """
        Returns asset of the project if found
        :param asset_name: str, name of the asset to find
        :param asset_path: str, path where asset is located in disk
        :param allow_multiple_instances: bool, whether to return None if multiple instances of an asset is found;
        otherwise first asset in the list will be return
        :return: Asset or None
        """

        asset_founds = self.find_all_assets(asset_name=asset_name, asset_path=asset_path)
        if len(asset_founds) > 1:
            LOGGER.warning('Found Multiple instances of Asset "{} | {}"'.format(
                asset_name, asset_path))
            if not allow_multiple_instances:
                return None

        return asset_founds[0]

    def get_asset_from_path(self, asset_path):
        """
        Returns asset from the given path
        :param asset_path: str
        :return: ArtellaAsset
        """

        asset_path = path_utils.clean_path(asset_path)
        _asset_name = os.path.basename(asset_path)

        asset_data_file = self.get_asset_data_file_path(asset_path)

        is_ignored = False
        for ignored in self._asset_ignored_paths:
            if ignored in asset_data_file:
                is_ignored = True
                break

        if is_ignored:
            return

        if not os.path.isfile(asset_data_file):
            LOGGER.warning('Impossible to get info of asset "{}". Please sync it! Skipping it ...'.format(_asset_name))
            return

        asset_data = jsonio.read_file(asset_data_file)
        asset_data[defines.ARTELLA_ASSET_DATA_ATTR][defines.ARTELLA_ASSET_DATA_NAME_ATTR] = _asset_name
        asset_data[defines.ARTELLA_ASSET_DATA_ATTR][defines.ARTELLA_ASSET_DATA_PATH_ATTR] = asset_path
        asset_category = strings.camel_case_to_string(os.path.basename(os.path.dirname(asset_path)))

        if asset_category in self._asset_types:
            new_asset = self.create_asset(asset_data=asset_data, category=asset_category)
        else:
            new_asset = self.create_asset(asset_data=asset_data)

        return new_asset

    def get_tag_info_nodes(self, as_tag_nodes=False):
        """
        Returns all nodes containing tag info data
        :return: list
        """

        tag_info_nodes = list()
        objs = tp.Dcc.all_scene_objects()
        for obj in objs:
            valid_tag_info_data = tp.Dcc.attribute_exists(
                node=obj, attribute_name=defines.ARTELLA_TAG_INFO_ATTRIBUTE_NAME)
            if valid_tag_info_data:
                if as_tag_nodes and self.TAG_NODE_CLASS:
                    tag_info = tp.Dcc.get_attribute_value(
                        node=obj, attribute_name=defines.ARTELLA_TAG_INFO_ATTRIBUTE_NAME)
                    obj = self.TAG_NODE_CLASS(project=self, node=obj, tag_info=tag_info)
                tag_info_nodes.append(obj)

        return tag_info_nodes

    @decorators.timestamp
    def get_scene_assets(self, as_nodes=True, allowed_types=None):
        """
        Returns a list with all nodes in the current scene
        :return: list
        """

        asset_nodes = list()

        abc_nodes = self.get_alembics(as_asset_nodes=False, only_roots=True)

        tag_data_nodes = tag.get_tag_data_nodes(project=self, as_tag_nodes=True)
        for tag_data in tag_data_nodes:
            asset_node = tag_data.get_asset_node()
            if asset_node is None or asset_node in abc_nodes:
                continue
            if allowed_types:
                asset_types = tag_data.get_types()
                allow = [i for i in asset_types if i in allowed_types]
                if allow:
                    if as_nodes:
                        asset_nodes.append(asset_node)
                    else:
                        asset_nodes.append(asset_node.name)
            else:
                if as_nodes:
                    asset_nodes.append(asset_node)
                else:
                    asset_nodes.append(asset_node.name)

        tag_info_nodes = self.get_tag_info_nodes(as_tag_nodes=True)
        for tag_info in tag_info_nodes:
            asset_node = tag_info.get_asset_node()
            if not asset_node:
                continue
            if allowed_types:
                asset_types = tag_info.get_types()
                allow = [i for i in asset_types if i in allowed_types]
                if allow:
                    if as_nodes:
                        asset_nodes.append(asset_node)
                    else:
                        asset_nodes.append(asset_node.name)
            else:
                if as_nodes:
                    asset_nodes.append(asset_node)
                else:
                    asset_nodes.append(asset_node.name)

        return asset_nodes

    def get_alembics(self, as_asset_nodes=True, only_roots=True):
        """
        Returns all alembic nodes in the scene
        :param as_asset_nodes: bool, Whether to return nodes as ArtellaAssetNodes
        :param only_roots: bool
        :return: list
        """

        all_abc_roots = list()
        added_roots = list()
        abc_nodes = list()

        objs = tp.Dcc.all_scene_objects()
        for obj in objs:
            if tp.Dcc.node_type(obj) == 'AlembicNode':
                abc_nodes.append(obj)

        for abc in abc_nodes:
            connections = tp.Dcc.list_connections(abc, 'transOp')
            if not connections:
                continue
            for cnt in connections:
                cnt_root = tp.Dcc.node_root(cnt)
                if cnt_root in added_roots:
                    continue
                if tp.Dcc.attribute_exists(cnt_root, defines.ARTELLA_TAG_INFO_ATTRIBUTE_NAME):
                    if as_asset_nodes:
                        if only_roots:
                            all_abc_roots.append(self.ASSET_NODE_CLASS(project=self, node=cnt_root))
                        else:
                            all_abc_roots.append((self.ASSET_NODE_CLASS(project=self, node=cnt_root), abc))
                    else:
                        if only_roots:
                            all_abc_roots.append(cnt_root)
                        else:
                            all_abc_roots.append((cnt_root, abc))
                    added_roots.append(cnt_root)

        return all_abc_roots

    def get_cameras(self):
        """
        Returns all cameras in the scene
        :return: list(str)
        """

        all_cameras = self.get_scene_assets(as_nodes=False, allowed_types=['camera'])

        return all_cameras

    # ==========================================================================================================
    # SEQUENCES
    # ==========================================================================================================

    @decorators.timestamp
    def get_sequences(self, force_update=False):
        """
        Returns a list of current sequences in Artella
        :param force_update: bool
        :return: list(ArtellaSequence)
        """

        if self._sequences and not force_update:
            return self._sequences

        if self._production_info and not force_update:
            production_info = self._production_info
        else:
            production_info = self._update_production_info()
        if not production_info:
            return

        sequences_dict = dict()
        sequences_names = dict()
        for ref_name, ref_data in production_info.references.items():
            if not ref_data.is_directory:
                continue
            rel_path = self.relative_path(ref_data.path)
            parse_data = self.parse_template('sequence', rel_path)
            if not parse_data:
                continue
            seq_id = parse_data['sequence_index']
            seq_name = parse_data['sequence_name']
            if seq_id in sequences_dict:
                LOGGER.warning('Sequence with name: {} is duplicated. Skipping ...'.format(seq_name))
                continue
            sequences_dict[seq_id] = ref_data
            sequences_names[seq_id] = seq_name

        valid_index_sequences = dict()
        not_index_sequences = dict()
        for seq_id in sequences_dict.keys():
            try:
                int_id = int(seq_id)
                valid_index_sequences[seq_id] = sequences_dict[seq_id]
            except Exception:
                not_index_sequences[seq_id] = sequences_dict[seq_id]

        sequences_ordered = OrderedDict(sorted(valid_index_sequences.items(), key=lambda x: int(x[0])))
        for seq_id in not_index_sequences.keys():
            sequences_ordered[seq_id] = not_index_sequences[seq_id]

        for seq_id, seq_data in sequences_ordered.items():
            seq_name = sequences_names[seq_id]
            new_sequence = self.SEQUENCE_CLASS(
                project=self, sequence_name=seq_name, sequence_id=seq_id, sequence_data=seq_data)
            self._sequences.append(new_sequence)

        return self._sequences

    # ==========================================================================================================
    # SHOTS
    # ==========================================================================================================

    @decorators.timestamp
    def get_shots(self, force_update=False):
        """
        Returns all shots of the given sequence name
        :param force_update: bool
        :return: list(ArtellaShot)
        """

        if self._shots and not force_update:
            return self._shots

        if self._production_info and not force_update:
            production_info = self._production_info
        else:
            production_info = self._update_production_info()
        if not production_info:
            return

        sequences = self.get_sequences(force_update=force_update)
        for seq in sequences:
            sequence_path = seq.get_path()
            if not sequence_path:
                LOGGER.warning('Impossible to retrieve path for Sequence: {}!'.format(seq.name))
                continue
            sequence_info = seq.get_info()
            print(sequence_info)

    def get_shots_from_sequence(self, sequence_name, force_update=False):
        """
        Returns shots of the given sequence name
        :param sequence_name: str
        :param force_update: bool
        :return:
        """

        shots = self.get_shots(force_update=force_update)

    def get_shot_name_regex(self):
        """
        Returns regex used to identeify shots
        :return: str
        """

        return re.compile(r"{}".format(self._shot_regex))

    # ==========================================================================================================
    # PUBLISHER
    # ==========================================================================================================

    def get_publisher_plugin_paths(self):
        """
        Function that registers all plugins available for Artella Publisher
        """

        return [
            path_utils.clean_path(os.path.join(self.get_project_path(), 'tools', 'publisher', 'plugins'))
        ]

    # ==========================================================================================================
    # SHADERS
    # ==========================================================================================================

    def get_shaders_path(self):
        """
        Returns path where shareds are located in the project
        :return: str
        """

        return path_utils.clean_path(os.path.join(self.get_assets_path(), 'shaders'))

    def update_shaders(self):
        """
        Updates shaders from Artella
        """

        shaders_path = self.get_shaders_path()
        if not shaders_path:
            return

        self.sync_files(files=shaders_path)

    # ==========================================================================================================
    # LIGHT RIGS
    # ==========================================================================================================

    def get_light_rigs_path(self):
        """
        Returns path where light rigs are located in the project
        :return: str
        """

        return path_utils.clean_path(os.path.join(self.get_assets_path(), 'lightrigs'))

    # ==========================================================================================================
    #  PLAYBLAST
    # ==========================================================================================================

    def get_playblast_presets_folder(self):
        """
        Returns path where Playblas Presets are loated
        :return: str
        """

        presets_url = self.playblast_presets_url
        if not presets_url:
            return

        return '{}{}'.format(self.get_path(), presets_url)

    # ==========================================================================================================
    # PRIVATE
    # ==========================================================================================================

    def _create_new_settings(self):
        """
        Creates new empty settings file
        :return: QtSettings
        """

        return ArtellaProjectSettings(project=self, filename=self.get_settings_file())

    def _check_file_path(self, file_path):
        """
        Returns whether given path is a valid project path or not
        :param file_path: str
        :return: str
        """

        if not file_path:
            file_path = tp.Dcc.scene_name()
            if not file_path:
                self.logger.error('File {} cannot be locked because it does not exists!'.format(file_path))
                return False

        if not file_path.startswith(self.get_path()):
            self.logger.error('Impossible to lock file that is nos located in {} Project Folder!'.format(self.name))
            return

        if not os.path.isfile(file_path):
            self.logger.error('File {} cannot be locked because it does not exists!'.format(file_path))
            return False

        return True

    def _register_asset_classes(self):
        """
        Internal function that can be override to register specific project asset classes
        """

        for asset_type in self.asset_types:
            for registered_asset in self._registered_asset_classes:
                if registered_asset.ASSET_TYPE == asset_type:
                    self._asset_classes_types[asset_type] = registered_asset
                    break

        for asset_type in self.asset_types:
            if asset_type not in self._asset_classes_types:
                self.logger.warning('Asset Type {} has not an associated asset class!'.format(asset_type))

    def _register_asset_file_types(self):
        """
        Internal function that can be override to register specific project file type classes
        """

        for asset_file in self.asset_files:
            if asset_file not in self._asset_classes_file_types:
                self._asset_classes_file_types[asset_file] = list()
            for registered_file in self._registered_asset_file_type_classes:
                if registered_file.FILE_TYPE == asset_file:
                    self._asset_classes_file_types[asset_file].append(registered_file)

        for asset_file in self.asset_files:
            if asset_file not in self._asset_classes_file_types:
                self.logger.warning('Asset File Type {} has not associated asset file class!'.format(asset_file))

    def _format_path(self, format_string, path='', **kwargs):
        """
        Resolves the given string with the given path and keyword arguments
        :param format_string: str
        :param path: str
        :param kwargs: dict
        :return: str
        """

        self.logger.debug('Format String: {}'.format(format_string))

        dirname, name, extension = path_utils.split_path(path)
        encoding = locale.getpreferredencoding()
        temp = tempfile.gettempdir()
        if temp:
            temp = temp.decode(encoding)

        username = osplatform.get_user().lower()
        if username:
            username = username.decode(encoding)

        local = os.getenv('APPDATA') or os.getenv('HOME')
        if local:
            local = local.decode(encoding)

        kwargs.update(os.environ)

        labels = {
            "name": name,
            "path": path,
            "user": username,
            "temp": temp,
            "local": local,
            "dirname": dirname,
            "extension": extension,
        }

        kwargs.update(labels)

        resolved_string = six.u(str(format_string)).format(**kwargs)

        LOGGER.debug('Resolved string: {}'.format(resolved_string))

        return path_utils.clean_path(resolved_string)

    def _update_production_info(self):
        """
        Internal callback function that updates current production info of the project
        :return: ArtellaDirectoryMetaData
        """

        production_path = self.get_production_path()
        if not production_path:
            LOGGER.warning(
                'Impossible to retrieve sequences because Production path for {} is not valid: {}!'.format(
                    self.name.title(), production_path))
            return

        production_info = artellalib.get_status(production_path)
        if not production_info:
            LOGGER.warning('Impossible to retrieve sequences data from Artella server!')
            return
        if not isinstance(production_info, artellaclasses.ArtellaDirectoryMetaData):
            LOGGER.warning('Error while retrieving Sequences info from Artella!')
            return

        return production_info


class ArtellaProjectSettings(QSettings, object):
    def __init__(self, project, filename, max_files=10):
        super(ArtellaProjectSettings, self).__init__(filename, QSettings.IniFormat)

        self._project = project
        self._max_files = max_files

        self.setFallbacksEnabled(False)

        self._initialize()

    def has_setting(self, setting_name):
        """
        Returns whether given settings name is currently stored in the settings or not
        :param setting_name: str
        :return: bool
        """

        return self.get(setting_name)

    def get(self, setting_name, default_value=None):
        """
        Returns the setting stored with the given name
        :param setting_name: str
        :param default_value: variant
        :return:
        """

        val = self.value(setting_name)
        if not val:
            return default_value

        return val

    def set(self, setting_name, setting_value):
        """
        Stores a new settings with the given name and the given value
        If the given setting already exists, it will be overwrite
        :param setting_name: str, setting name we want store
        :param setting_value: variant, setting value we want to store
        """

        self.setValue(setting_name, setting_value)

    def _initialize(self):
        """
        Internal function that initializes project settings
        """

        project_name = self._project.get_clean_name()
        self.setValue('{}/name'.format(project_name), project_name)
