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
import time
import locale
import logging
import tempfile
import datetime
import importlib
import traceback
import webbrowser
from collections import OrderedDict

import six

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import python, decorators, osplatform, fileio, path as path_utils, folder as folder_utils
import tpDccLib as tp

if python.is_python2():
    from urllib2 import quote
    import pkgutil as loader
else:
    from urllib.parse import quote
    import importlib as loader

import artellapipe
from artellapipe.libs import artella as artella_lib
from artellapipe.libs.artella.core import artellalib, artellaclasses
from artellapipe.core import defines, config, node, sequence, shot
from artellapipe.utils import resource

LOGGER = logging.getLogger()


class ArtellaProject(object):

    SHELF_CLASS = tp.Shelf
    SEQUENCE_CLASS = sequence.ArtellaSequence
    SHOT_CLASS = shot.ArtellaShot
    ASSET_NODE_CLASS = node.ArtellaAssetNode

    def __init__(self, name, settings=None):
        super(ArtellaProject, self).__init__()

        self._tray = None

        self._production_info = None
        self._sequences = list()
        self._shots = list()

        # To make sure that all variables are properly initialized we must call init_config first
        clean_name = self._get_clean_name(name)
        self._config = config.ArtellaConfiguration(
            project_name=clean_name,
            config_name='artellapipe-project',
            environment=os.environ.get('{}_env'.format(self._get_clean_name(name)), 'DEVELOPMENT'),
            config_dict={
                'title': clean_name.title(),
                'project_lower': clean_name.replace(' ', '').lower(),
                'project_upper': clean_name.replace(' ', '').upper(),
            }
        )
        self._config_data = self._config.data

        self._settings = settings
        self.init_settings()

    def __getattr__(self, attr_name):
        if attr_name not in self._config_data:
            raise AttributeError('{} has no attribute {}'.format(self.__class__.__name__, attr_name))

        attr_data = self._config_data[attr_name]
        return attr_data

    # ==========================================================================================================
    # PROPERTIES
    # ==========================================================================================================

    # NOTE: All the properties defined in the project settings file are accessible as properties by the project.

    @property
    def config(self):
        """
        Returns configuration object of the project
        :return: ArtellaConfiguration
        """

        return self._config

    @property
    def config_data(self):
        """
        Returns configuration data of the project
        :return: dict
        """

        return self._config_data

    @property
    def settings(self):
        """
        Returns the settings of the project
        :return: ArtellaProjectSettings
        """

        return self._settings

    @property
    def full_id(self):
        """
        Returns full ID of the project
        :return: str
        """

        artella_production_folder = artellalib.config.get('server', {}).get('production_folder')
        if not artella_production_folder:
            LOGGER.warning('Impossible to retrieve Artella project ID!')
            return None

        return '{}/{}/{}/'.format(artella_production_folder, self.id_number, self.id)

    @property
    def id_path(self):
        """
        Returns ID path of this Artella project
        :return: str
        """

        return '{}{}{}'.format(self.id_number, os.sep, self.id)

    @property
    def icon(self):
        """
        Returns project icon
        :return: QIcon
        """

        return resource.ResourceManager().icon(self.icon_name, theme=self.icon_resources_folder)

    @property
    def tray_icon(self):
        """
        Returns icon used by the tray of the project
        :return: QIcon
        """

        return resource.ResourceManager().icon(self.tray_icon_name, key='project')

    @property
    def shelf_icon(self):
        """
        Returns icon used by the shelf of the project
        :return: QIcon
        """

        return resource.ResourceManager().icon(self.shelf_icon_name, theme=None, key='project')

    @property
    def tray(self):
        """
        Returns the tray used by the Artella project
        :return: Tray
        """

        return self._tray

    # ==========================================================================================================
    # INITIALIZATION, CONFIG & SETTINGS
    # ==========================================================================================================

    def init(self, force_skip_hello=False):
        """
        This function initializes Artella project
        :param force_skip_hello: bool, Whether the hello window should be showed or not
        """

        self.update_paths()
        self.set_environment_variables()
        self.create_shelf()
        self.create_menu()
        self._tray = self.create_tray()
        self.create_names_manager()
        self.create_files_manager()
        self.create_assets_manager()
        self.create_tags_manager()
        self.create_shaders_manager()
        self.create_shots_manager()
        self.create_playblasts_manager()
        self.create_pyblish_manager()
        self.create_shots_manager()
        self.create_dependencies_manager()
        self.create_production_tracker()
        self.update_project()
        self._update_dcc_ui()

    def get_environment(self):
        """
        Returns current project environment ("DEVELOPMENT" or "PRODUCTION")
        :return: str or None
        """

        tag_env_var = '{}_env'.format(self.get_clean_name())
        return os.environ.get(tag_env_var, 'DEVELOPMENT')

    def is_dev(self):
        """
        Returns current environment is development one or not
        :return: bool
        """

        current_environment = self.get_environment()
        return not current_environment or current_environment == 'DEVELOPMENT'

    def get_tag(self):
        """
        Returns the current deployed tag of the project
        :return: str or None
        """

        tag_env_var = '{}_tag'.format(self.get_clean_name())
        return os.environ.get(tag_env_var, None)

    def get_project_path(self):
        """
        Returns path where default Artella project is located
        :return: str
        """

        try:
            pkg_loader = loader.find_loader('{}.loader'.format(self._get_clean_name(self.name)))
        except Exception:
            pkg_loader = loader.find_loader('artellapipe.loader')

        return path_utils.clean_path(os.path.dirname(pkg_loader.filename))

    def get_configurations_folder(self):
        """
        Returns folder where project configuration files are loaded
        :return: str
        """

        print('bjblblbl')

        try:
            pkg_loader = loader.find_loader('{}.config'.format(self._get_clean_name(self.name)))
        except ImportError:
            pkg_loader = loader.find_loader('artellapipe.config')

        print(pkg_loader.filename)

        return path_utils.clean_path(os.path.dirname(pkg_loader.filename))

    def get_changelog_path(self):
        """
        Returns path where default Artella project changelog is located
        :return: str
        """

        return path_utils.clean_path(
            os.path.join(self.get_project_path(), defines.ARTELLA_PROJECT_CHANGELOG_FILE_NAME))

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

        try:
            mod = importlib.import_module(self.get_clean_name())
            mod_path = os.path.join(
                os.path.dirname(os.path.abspath(mod.__file__)), defines.ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME)
            if os.path.isfile(mod_path):
                return mod_path
            else:
                return path_utils.clean_path(
                    os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME))
        except (RuntimeError, ImportError) as exc:
            return path_utils.clean_path(
                os.path.join(self.get_configurations_folder(), defines.ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME))

    def get_version(self):
        """
        Returns the current version of the tools
        :return: str
        """

        version_file_path = self.get_version_path()
        if not os.path.isfile(version_file_path):
            LOGGER.warning('No Version File found "{}" for project "{}"!'.format(version_file_path, self.name))
            return

        version_data = fileio.get_file_lines(version_file_path)
        if not version_data:
            LOGGER.warning('Version File "{}" does not contain any version information!'.format(version_file_path))
            return

        for line in version_data:
            if not line.startswith('__version__'):
                continue
            version_split = line.split('=')
            if not version_split:
                LOGGER.warning('Version data in file "{}" is not formatted properly!'.format(version_file_path))
                return

            return version_split[-1].strip()[1:-1]

        return 'Not Found!'

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

        return self._get_clean_name(self.name)

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

        LOGGER.debug('Initializing environment variables for: {}'.format(self.name))

        # In development mode we do not want to send Sentry exceptions or messages
        if self.is_dev():
            os.environ['SKIP_SENTRY_EXCEPTIONS'] = 'True'

        try:
            if tp.Dcc.get_name() == tp.Dccs.Unknown:
                mtime = time.time()
                date_value = datetime.datetime.fromtimestamp(mtime)
                artellalib.get_spigot_client(app_identifier='{}.{}'.format(self.name.title(), date_value.year))
            artellalib.update_local_artella_root()
            root_prefix = artella_lib.config.get('app', 'root_prefix')
            production_folder = artella_lib.config.get('server', 'production_folder')
            artella_var = os.environ.get(root_prefix, None)
            LOGGER.debug('Artella environment variable is set to: {}'.format(artella_var))
            if artella_var and os.path.exists(artella_var):
                os.environ[self.env_var] = '{}{}/{}/{}/'.format(
                    artella_var, production_folder, self.id_number, self.id)
            else:
                LOGGER.warning('Impossible to set Artella environment variable!')
        except Exception as e:
            LOGGER.debug(
                'Error while setting {0} Environment Variables. {0} Pipeline Tools may not work properly!'.format(
                    self.name.title()))
            LOGGER.error('{} | {}'.format(e, traceback.format_exc()))

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

        LOGGER.debug('=' * 100)
        LOGGER.debug("{} Pipeline initialization completed!".format(self.name))
        LOGGER.debug('=' * 100)
        LOGGER.debug('*' * 100)
        LOGGER.debug('-' * 100)
        LOGGER.debug('\n')

    def create_shelf(self):
        """
        Creates Artella Project shelf
        """

        if tp.Dcc == tp.Dccs.Unknown:
            return False

        shelf_manager = artellapipe.ShelfMgr()
        shelf_manager.set_project(self)

        return shelf_manager

    def create_menu(self):
        """
        Creates Artella Project menu
        """

        if tp.Dcc == tp.Dccs.Unknown:
            return False

        menu_manager = artellapipe.MenuMgr()
        menu_manager.set_project(self)

        return menu_manager

    def create_names_manager(self):
        """
        Creates instance of the assets manager used by the project
        :return: ArtellaAssetsManager
        """

        names_manager = artellapipe.NamesMgr()
        names_manager.set_project(self)

        return names_manager

    def create_assets_manager(self):
        """
        Creates instance of the assets manager used by the project
        :return: ArtellaAssetsManager
        """

        if tp.Dcc == tp.Dccs.Unknown:
            return None

        assets_manager = artellapipe.AssetsMgr()
        assets_manager.set_project(self)

        return assets_manager

    def create_files_manager(self):
        """
        Creates instance of the files manager used by the project
        :return: ArtellaFilesManager
        """

        assets_manager = artellapipe.FilesMgr()
        assets_manager.set_project(self)

        return assets_manager

    def create_tags_manager(self):
        """
        Creates instance of the tags manager used by the project
        :return: ArtellaTagsManager
        """

        tags_manager = artellapipe.TagsMgr()
        tags_manager.set_project(self)

        return tags_manager

    def create_shaders_manager(self):
        """
        Creates instance of the shaders manager used by the project
        :return: ArtellaShadersManager
        """

        shaders_manager = artellapipe.ShadersMgr()
        shaders_manager.set_project(self)

        return shaders_manager

    def create_shots_manager(self):
        """
        Creates instance of the shots manager used by the project
        :return: ArtellaShotsManager
        """

        shots_manager = artellapipe.ShotsMgr()
        shots_manager.set_project(self)

        return shots_manager

    def create_playblasts_manager(self):
        """
       Creates instance of the playblasts manager used by the project
       :return: ArtellaPlayblastsManager
       """

        playblasts_manager = artellapipe.PlayblastsMgr()
        playblasts_manager.set_project(self)

        return playblasts_manager

    def create_pyblish_manager(self):
        """
       Creates instance of the Pyblish plugins manager used by the project
       :return: ArtellaPyblishPluginsManager
       """

        pyblish_manager = artellapipe.PyblishMgr()
        pyblish_manager.set_project(self)

        return pyblish_manager

    def create_dependencies_manager(self):
        """
        Crates instance of the dependencies manager used by the project
        :return: ArtellaDependenciesManager
        """

        deps_manager = artellapipe.DepsMgr()
        deps_manager.set_project(self)

        return deps_manager

    def create_production_tracker(self):
        """
        Creates instance of the production tracker used by the project
        :return: ArtellaProductionTracker
        """

        if tp.Dcc == tp.Dccs.Unknown:
            return None

        production_tracker = artellapipe.Tracker()
        production_tracker.set_project(self)

        return production_tracker

    def get_folders_to_register(self, full_path=True):
        """
        Returns folders to register paths
        :param full_path: bool, Whether to return full path of the folder or not
        :return: list(str)
        """

        if not self.paths_to_register:
            return list()

        if not full_path:
            return self.paths_to_register
        else:
            paths_to_return = list()
            for p in self.paths_to_register:
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
                LOGGER.debug(str(msg))
        else:
            LOGGER.debug(str(msg))

    # ==========================================================================================================
    # TRAY
    # ==========================================================================================================

    def create_tray(self):
        """
        Creates Artella Project tray
        """

        LOGGER.debug('Creating {} Tools Tray ...'.format(self.name.title()))
        tray = artellapipe.Tray(project=self)

        return tray

    def open_documentation(self):
        """
        Opens Plot Twist documentation web page in browser
        """

        if not self.documentation_url:
            LOGGER.warning('Project "{}" does not define a Documentation URL!'.format(self.name))
            return

        webbrowser.open(self.documentation_url)

    def open_webpage(self):
        """
        Opens Plot Twist official web page in browser
        """

        if not self.url:
            LOGGER.warning('Project "{}" does not define a Project URL!'.format(self.name))
            return

        webbrowser.open(self.url)

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

        webbrowser.open("mailto:%s?subject=%s" % (','.join(self.emails), quote(title)))

    # ==========================================================================================================
    # PROJECT
    # ==========================================================================================================

    def get_path(self, force_update=False):
        """
        Returns path where project is located
        :param force_update: bool, Whether to force the update of project path is environment variables are not setup
        :return: str
        """

        env_var = os.environ.get(self.env_var, None)

        if not env_var or force_update:
            self.update_project()
            env_var = os.environ.get(self.env_var, None)

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

        env_var = os.environ.get(self.env_var, None)
        if not env_var:
            raise RuntimeError(
                '{} Project not setup properly. Please contact TD to fix this problem'.format(self.name.title()))

        return os.environ.get(self.env_var)

    def get_production_path(self):
        """
        Returns path where Production data for current project is stored
        :return: str
        """

        project_path = self.get_path()
        if not project_path:
            LOGGER.warning('Impossible to retrieve productoin path because Artella project is not setup!')
            return

        production_folder_name = artella_lib.config.get('server', 'production_folder_name')
        return path_utils.clean_path(os.path.join(project_path, production_folder_name))

    def get_artella_url(self):
        """
        Returns Artella URL of the project
        :return: str
        """

        artella_web = artella_lib.config.get('server', 'url')
        return '{}/project/{}/files'.format(artella_web, self.id)

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
                LOGGER.debug('Setting {} Project ...'.format(self.name))
                project_folder = os.environ.get(self.env_var, 'folder-not-defined')
                if project_folder and os.path.exists(project_folder):
                    maya.cmds.workspace(project_folder, openWorkspace=True)
                    LOGGER.debug('{} Project setup successfully! => {}'.format(self.name, project_folder))
                else:
                    LOGGER.warning('Unable to set {} Project! => {}'.format(self.name, project_folder))
        except Exception as e:
            LOGGER.error('{} | {}'.format(str(e), traceback.format_exc()))

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
            "rgb(" + self.progress_bar.color0 + "), stop: 1 rgb(" + self.progress_bar.color1 + ")); }")

        return new_progress_bar

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

    # ==========================================================================================================
    # ASSETS
    # ==========================================================================================================

    @decorators.timestamp
    def get_scene_assets(self, as_nodes=True, allowed_types=None):
        """
        Returns a list with all nodes in the current scene
        :return: list
        """

        asset_nodes = list()

        abc_nodes = self.get_alembics(as_asset_nodes=False, only_roots=True)

        tag_data_nodes = artellapipe.TagsMgr().get_tag_data_nodes(project=self, as_tag_nodes=True)
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
    # PRIVATE
    # ==========================================================================================================

    def _get_clean_name(self, name):
        """
        Internal function that returns a cleaned version of the given project name
        :param name: str
        :return: str
        """

        return name.replace(' ', '').lower()

    def _create_new_settings(self):
        """
        Creates new empty settings file
        :return: QtSettings
        """

        return ArtellaProjectSettings(project=self, filename=self.get_settings_file())

    def _format_path(self, format_string, path='', **kwargs):
        """
        Resolves the given string with the given path and keyword arguments
        :param format_string: str
        :param path: str
        :param kwargs: dict
        :return: str
        """

        LOGGER.debug('Format String: {}'.format(format_string))

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

    def _update_dcc_ui(self):
        """
        Internal function that updates DCC update taking into account different project attributes
        """

        if self.is_dev() and tp.Dcc != tp.Dccs.Unknown:
            main_win = tp.Dcc.get_main_window()
            if main_win and hasattr(main_win, 'menuBar'):
                menubar = main_win.menuBar()
                menubar.setStyleSheet(
                    "QMenuBar { background: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 1, stop: 0 "
                    "rgb(" + self.dev_color0 + "), stop: 1 rgb(" + self.dev_color1 + ")); }")
                # menubar.setStyleSheet('QMenuBar { background-color: rgba(255, 255, 0, 75); }')


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
