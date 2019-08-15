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
import traceback
import webbrowser
try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote
from collections import OrderedDict

from Qt.QtWidgets import *

import tpDccLib as tp
from tpPyUtils import python, strings, decorators, osplatform, jsonio, path as path_utils, folder as folder_utils
from tpQtLib.core import qtutils

import artellapipe
from artellapipe.core import defines, artellalib, asset, node, syncdialog
from artellapipe.gui import tray

from artellapipe.tools.namemanager import namemanager
from artellapipe.tools.tagger.core import taggerutils


class ArtellaProject(object):

    PROJECT_RESOURCE = None
    TRAY_CLASS = tray.ArtellaTray
    SHELF_CLASS = tp.Shelf
    ASSET_CLASS = asset.ArtellaAsset
    ASSET_NODE_CLASS = node.ArtellaAssetNode
    SYNC_FILES_DIALOG_CLASS = syncdialog.ArtellaSyncFileDialog
    SYNC_PATHS_DIALOG_CLASS = syncdialog.ArtellaSyncPathDialog
    TAG_NODE_CLASS = asset.ArtellaTagNode
    PROJECT_PATH = artellapipe.get_project_path()
    PROJECT_CONFIG_PATH = artellapipe.get_project_config_path()
    PROJECT_CHANGELOG_PATH = artellapipe.get_project_changelog_path()
    PROJECT_SHELF_FILE_PATH = artellapipe.get_project_shelf_path()
    PROJECT_MENU_FILE_PATH = artellapipe.get_project_menu_path()

    def __init__(self, resource, naming_file):
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
        self._version_file = None
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
        self._shaders_extension = None

        self._registered_asset_classes = list()
        self._asset_classes_types = dict()
        self._registered_asset_file_type_classes = list()
        self._asset_classes_file_types = dict()

        self._resource = resource
        self._naming_file = naming_file

        self._nameit = namemanager.NameWidget(self)

        # To make sure that all variables are properly initialized we must call init_config first
        self.init_config()
        self._logger = self.create_logger()[1]

        self._register_asset_classes()
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
    def version_file_path(self):
        """
        Returns version file path
        :return: str
        """

        return path_utils.clean_path(os.path.join(self.get_clean_name(), self._folders_to_register[0], self._version_file))

    @property
    def naming_file(self):
        """
        Returns naming file path
        :return: str
        """

        return self._naming_file

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
        Returns the list of asset files that an asset need to have published to consider the asset ready for production
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

        return self._resource.icon(self._project_icon)

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

        return self._resource.icon(self._tray_icon)

    @property
    def resource(self):
        """
        Returns the class used by the project to load resources (icons, images, fonts, etc)
        :return: Resource
        """

        return self._resource

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
    def shaders_extension(self):
        """
        Returns extension usded by shaders files
        :return: str
        """

        return self._shaders_extension

    # ==========================================================================================================
    # INITIALIZATION & CONFIG
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

    def solve_name(self, rule_name, *args, **kwargs):
        """
        Resolves name with given rule and attributes
        :param rule_name: str
        :param args: list
        :param kwargs: dict
        """

        current_rule = self._nameit.get_active_rule()
        self._nameit.set_active_rule(rule_name)
        solved_name = self._nameit.solve(*args, **kwargs)
        if current_rule:
            if rule_name != current_rule.name:
                self._nameit.set_active_rule(current_rule.name)
        else:
            self._nameit.set_active_rule(None)

        return solved_name

    def get_config_data(self):
        """
        Returns the config data of the project
        :return: dict
        """

        if not self.PROJECT_CONFIG_PATH or not os.path.isfile(self.PROJECT_CONFIG_PATH):
            tp.Dcc.error('Project Configuration File for {} Project not found! {}'.format(self.name.title(), self.PROJECT_CONFIG_PATH))
            return

        with open(self.PROJECT_CONFIG_PATH, 'r') as f:
            project_config_data = json.load(f, object_hook=OrderedDict)
        if not project_config_data:
            tp.Dcc.error('Project Configuration File for {} Project is empty! {}'.format(self.name.title(), self.PROJECT_CONFIG_PATH))
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
        self._project_env_var = project_config_data.get(defines.ARTELLA_CONFIG_ENVIRONMENT_VARIABLE, defines.ARTELLA_DEFAULT_ENVIRONMENT_VARIABLE)
        self._id_number = project_config_data.get(defines.ARTELLA_CONFIG_PROJECT_NUMBER, -1)
        self._id = project_config_data.get(defines.ARTELLA_CONFIG_PROJECT_ID, -1)
        self._full_id = '{}/{}/{}/'.format(defines.ARTELLA_PRODUCTION_FOLDER, self._id_number, self._id)
        self._url = project_config_data.get(defines.ARTELLA_PROJECT_URL, None)
        self._version_file = project_config_data.get(defines.ARTELLA_VERSION_FILE_NAME_ATTRIBUTE_NAME, defines.ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME)
        self._asset_types = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_TYPES, list())
        self._asset_files = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_FILES, list())
        self._asset_must_files = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_MUST_FILES, list())
        self._wip_status = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_WIP_STATUS, None)
        self._publish_status = project_config_data.get(defines.ARTELLA_CONFIG_ASSET_PUBLISH_STATUS, None)
        self._project_icon = project_config_data.get(defines.ARTELLA_PROJECT_ICON, defines.ARTELLA_PROJECT_DEFAULT_ICON)
        self._shelf_icon = project_config_data.get(defines.ARTELLA_CONFIG_SHELF_ICON, None)
        self._tray_icon = project_config_data.get(defines.ARTELLA_CONFIG_TRAY_ICON, None)
        self._folders_to_register = project_config_data.get(defines.ARTELLA_CONFIG_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME, defines.ARTELLA_CONFIG_DEFAULT_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME)
        self._emails = project_config_data.get(defines.ARTELLA_CONFIG_EMAIL_ATTRIBUTE_NAME, list())
        self._progress_bar_color0 = project_config_data.get(defines.ARTELLA_PROGRESS_BAR_COLOR_0_ATTRIBUTE_NAME, '255, 255, 255')
        self._progress_bar_color1 = project_config_data.get(defines.ARTELLA_PROGRESS_BAR_COLOR_1_ATTRIBUTE_NAME, '255, 255, 255')
        self._asset_ignored_paths = project_config_data.get(defines.ARTELLA_ASSETS_IGNORED_PATHS_ATTRIBUTE_NAME, list())
        self._assets_library_file_types = project_config_data.get(defines.ARTELLA_ASSETS_LIBRARY_SUPPORTED_TYPES_ATTRIBUTE_NAME, dict())
        self._asset_data_filename = project_config_data.get(defines.ARTELLA_ASSET_DATA_FILENAME_ATTRIBUTE_NAME, None)
        self._tag_types = project_config_data.get(defines.ARTELLA_CONFIG_TAG_TYPES, list())
        self._outliner_categories = project_config_data.get(defines.ARTELLA_CONFIG_OUTLINER_CATEGORIES, dict())
        self._shot_regex = project_config_data.get(defines.ARTELLA_CONFIG_SHOT_REGEX, '*')
        self._shaders_extension = project_config_data.get(defines.ARTELLA_SHADERS_EXTENSION_ATTRIBUTE_NAME, None)

        if self._id_number == -1 or self._id == -1 or not self._wip_status or not self._publish_status:
            tp.Dcc.error('Project Configuration File for Project: {} is not valid!'.format(self.name))
            return False

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
                os.environ[self._project_env_var] = '{}{}/{}/{}/'.format(artella_var, defines.ARTELLA_PRODUCTION_FOLDER, self._id_number, self._id)
            else:
                self.logger.warning('Impossible to set Artella environment variable!')
        except Exception as e:
            self.logger.debug('Error while setting Solstice Environment Variables. Solstice Tools may not work properly!')
            self.logger.error('{} | {}'.format(e, traceback.format_exc()))

        icons_paths = [
            artellapipe.resource.RESOURCES_FOLDER,
            self.resource.RESOURCES_FOLDER
        ]

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
        project_shelf.create(delete_if_exists=True)
        shelf_file = self.PROJECT_SHELF_FILE_PATH
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
            menu_file = self.PROJECT_SHELF_FILE_PATH
            if menu_file and os.path.isfile(menu_file):
                project_menu.create_menu(file_path=menu_file, parent_menu=menu_name)
        except Exception as e:
            self.logger.warning('Error during {} Tools Menu creation: {} | {}'.format(self.name.title(), e, traceback.format_exc()))

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
                paths_to_return.append(path_utils.clean_path(os.path.join(self.PROJECT_PATH, p)))
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

    def get_path(self, force_update=True):
        """
        Returns path where project is located
        :param force_update: bool, Whether to force the update of project path is environment variables are not setup
        :return: str
        """

        env_var = os.environ.get(self._project_env_var, None)

        # If project environment variable is not setup we f
        if not env_var and force_update:
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
                    raise RuntimeError('{} Project not set up properly after launching Artella. Is Artella Running?'.format(self.name.title()))

        env_var = os.environ.get(self._project_env_var, None)
        if not env_var:
            raise RuntimeError('{} Project not setup properly. Please contact TD to fix this problem'.format(self.name.title()))

        return os.environ.get(self._project_env_var)

    def get_changelog_path(self):
        """
        Returns path where changelog data for Artella project is located
        :return: str
        """

        return self.PROJECT_CHANGELOG_PATH

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

        return path_to_fix

    def relative_path(self, full_path):
        """
        Returns relative path of the given path relative to Project path
        :param full_path: str
        :return: str
        """

        return os.path.relpath(full_path, self.get_path())

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
        new_progress_bar.setStyleSheet("QProgressBar {border: 0px solid grey; border-radius:4px; padding:0px} QProgressBar::chunk {background: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 1, stop: 0 rgb(" + self.progress_bar_color_0 + "), stop: 1 rgb(" + self.progress_bar_color_1 + ")); }")

        return new_progress_bar

    # ==========================================================================================================
    # SYNC
    # ==========================================================================================================

    def sync_files(self, files):
        """
        Creates an return a new instance of the Artella paths sync dialog
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
            artellapipe.logger.warning('File was not saved!')
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
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            return False

        if warn_user:
            msg = 'If changes in file: \n\n{}\n\n are not submitted to Artella yet, submit them before unlocking the file please. \n\n Do you want to continue?'.format(file_path)
            res = tp.Dcc.confirm_dialog(title='Unlock File', message=msg, button=['Yes', 'No'], cancel_button='No', dismiss_string='No')
            if res != tp.Dcc.DialogResult.Yes:
                return False

        artellalib.unlock_file(file_path=file_path)
        if notify:
            self.tray.show_message(title='Unlock File', msg='File unlocked successfully!')

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
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            return False

        short_path = file_path.replace(self.get_assets_path(), '')[1:]

        history = artellalib.get_asset_history(short_path)
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
            comment = qtutils.get_comment(text_message='Make New Version ({}) : {}'.format(current_version, short_path), title='Comment', parent=tp.Dcc.get_main_window())

        if comment:
            artellalib.upload_new_asset_version(file_path=file_path, comment=comment, skip_saving=skip_saving, force=force)
            if notify:
                self.tray.show_message(title='New Working Version', msg='Version {} uploaded to Artella server successfully!'.format(current_version))
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
            return None

        asset_classes = self._asset_classes_file_types[file_type]
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

    def find_all_assets(self, asset_name=None):
        """
        Returns a list of all assets in the project
        :param asset_name: str, If given, a list with the given item will be returned instead
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
            self.logger.warning('Impossible to retrieve Solstice assets because asset data file name is not defined!')
            return

        found_assets = list()

        for root, dirs, files in os.walk(assets_path):
            if dirs and defines.ARTELLA_WORKING_FOLDER in dirs:
                asset_path = path_utils.clean_path(root)
                _asset_name = os.path.basename(root)

                if asset_name and asset_name != _asset_name:
                    continue

                asset_data_file = self.get_asset_data_file_path(asset_path)

                is_ignored = False
                for ignored in self._asset_ignored_paths:
                    if ignored in asset_data_file:
                        is_ignored = True
                        break

                if is_ignored:
                    continue

                if not os.path.isfile(asset_data_file):
                    artellapipe.logger.warning('Impossible to get info of asset "{}". Please sync it! Skipping it ...'.format(_asset_name))
                    continue

                asset_data = jsonio.read_file(asset_data_file)
                asset_data[defines.ARTELLA_ASSET_DATA_ATTR][defines.ARTELLA_ASSET_DATA_NAME_ATTR] = _asset_name
                asset_data[defines.ARTELLA_ASSET_DATA_ATTR][defines.ARTELLA_ASSET_DATA_PATH_ATTR] = asset_path
                asset_category = strings.camel_case_to_string(os.path.basename(os.path.dirname(asset_path)))

                if asset_category in self._asset_types:
                    new_asset = self.create_asset(asset_data=asset_data, category=asset_category)
                else:
                    new_asset = self.create_asset(asset_data=asset_data)

                found_assets.append(new_asset)

        return found_assets

    def find_asset(self, asset_name):
        """
        Returns asset of the project if found
        :param asset_name: str, name of the asset to find
        :return: Asset or None
        """

        asset_founds = self.find_all_assets(asset_name=asset_name)
        if not asset_founds:
            return None

        if len(asset_founds) > 0:
            artellapipe.logger.warning('Found Multiple instances of Asset "{}"'.format(asset_name))

        return asset_founds[0]

    def get_tag_info_nodes(self, as_tag_nodes=False):
        """
        Returns all nodes containing tag info data
        :return: list
        """

        tag_info_nodes = list()
        objs = tp.Dcc.all_scene_objects()
        for obj in objs:
            valid_tag_info_data = tp.Dcc.attribute_exists(node=obj, attribute_name=defines.ARTELLA_TAG_INFO_ATTRIBUTE_NAME)
            if valid_tag_info_data:
                if as_tag_nodes and self.TAG_NODE_CLASS:
                    tag_info = tp.Dcc.get_attribute_value(node=obj, attribute_name=defines.ARTELLA_TAG_INFO_ATTRIBUTE_NAME)
                    obj = self.TAG_NODE_CLASS(project=self, node=obj, tag_info=tag_info)
                tag_info_nodes.append(obj)

        return tag_info_nodes

    @decorators.timestamp
    def get_scene_assets(self, as_nodes=True, allowed_types=None):
        """
        Implements base ArtellaProject get_scene_assets function
        Returns a list with all nodes in the current scene
        :return: list
        """

        asset_nodes = list()

        abc_nodes = self.get_alembics(as_asset_nodes=False, only_roots=True)

        tag_data_nodes = taggerutils.get_tag_data_nodes(project=self, as_tag_nodes=as_nodes)
        for tag_data in tag_data_nodes:
            asset_node = tag_data.get_asset_node()
            if asset_node is None or asset_node in abc_nodes:
                continue
            if allowed_types:
                asset_types = tag_data.get_types()
                allow = [i for i in asset_types if i in allowed_types]
                if allow:
                    asset_nodes.append(asset_node)
            else:
                asset_nodes.append(asset_node)

        tag_info_nodes = self.get_tag_info_nodes(as_tag_nodes=as_nodes)
        for tag_info in tag_info_nodes:
            asset_node = tag_info.get_asset_node()
            if not asset_node:
                continue
            if allowed_types:
                asset_types = tag_info.get_types()
                allow = [i for i in asset_types if i in allowed_types]
                if allow:
                    asset_nodes.append(asset_node)
            else:
                asset_nodes.append(asset_node)

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

    # ==========================================================================================================
    # SHOTS
    # ==========================================================================================================

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
            path_utils.clean_path(os.path.join(artellapipe.get_project_path(), 'tools', 'publisher', 'plugins'))
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
    # PRIVATE
    # ==========================================================================================================

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
