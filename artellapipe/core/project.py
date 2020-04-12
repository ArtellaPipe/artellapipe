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
import sys
import time
import logging
import tempfile
import datetime
import importlib
import traceback
import webbrowser

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import python, osplatform, fileio, path as path_utils, folder as folder_utils

if python.is_python2():
    from urllib2 import quote
    import pkgutil as loader
else:
    from urllib.parse import quote
    import importlib as loader

import artellapipe
from artellapipe.libs import artella as artella_lib
from artellapipe.libs.artella.core import artellalib
from artellapipe.core import defines

LOGGER = logging.getLogger()


class ArtellaProjectType(object):
    INDIE = 'indie'
    ENTERPRISE = 'enterprise'


class ArtellaProject(object):
    def __init__(self, name, settings=None):
        super(ArtellaProject, self).__init__()

        self._tray = None

        clean_name = self._get_clean_name(name)

        # Register project configurations
        try:
            project_config_mod = importlib.import_module('{}.config'.format(clean_name))
            tp.ConfigsMgr().register_package_configs(
                clean_name, os.path.dirname(project_config_mod.__file__))
        except RuntimeError:
            artellapipe.logger.warning('No Configuration Module found for project: {}'.format(clean_name))

        self._config = tp.ConfigsMgr().get_config(
            config_name='artellapipe-project',
            package_name=clean_name,
            root_package_name='artellapipe',
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

        artella_production_folder = self.get_production_folder()
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

        return tp.ResourcesMgr().icon(self.icon_name, theme=self.icon_resources_folder)

    @property
    def thumb_icon(self):
        """
        Returns thumb icon for the project
        :return: QIcon
        """

        return tp.ResourcesMgr().icon(self.get_clean_name(), category='images', key='project', theme=None)

    @property
    def tray_icon(self):
        """
        Returns icon used by the tray of the project
        :return: QIcon
        """

        return tp.ResourcesMgr().icon(self.tray_icon_name, key='project')

    @property
    def shelf_icon(self):
        """
        Returns icon used by the shelf of the project
        :return: QIcon
        """

        return tp.ResourcesMgr().icon(self.shelf_icon_name, theme=None, key='project')

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
        self._tray = self.create_tray()
        self.create_names_manager()
        self.create_files_manager()
        self.create_assets_manager()
        self.create_tags_manager()
        self.create_shaders_manager()
        self.create_sequences_manager()
        self.create_shots_manager()
        self.create_tasks_manager()
        self.create_media_manager()
        self.create_playblasts_manager()
        self.create_pyblish_manager()
        self.create_dependencies_manager()
        self.create_casting_manager()
        self.create_slack_manager()
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

    def get_toolsets_paths(self):
        """
        Returns path where project toolsets are located
        :return: list(str)
        """

        return list()

    def get_resources_paths(self):
        """
        Returns path where project resources are located
        :return: dict(str, list(str), dict containing resources keys and resources paths
        """

        return dict()

    def get_tag(self):
        """
        Returns the current deployed tag of the project
        :return: str or None
        """

        tag_env_var = '{}_tag'.format(self.get_clean_name())
        return os.environ.get(tag_env_var, None)

    def get_project_type(self):
        """
        Returns the current type of the Artella project. It can be Indie (indie) or Enterprise (enterprise)
        :return: str
        """

        return self._config.get('project_type', default=ArtellaProjectType.INDIE)

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

        import appdirs

        data_path = appdirs.user_data_dir(self.get_clean_name())
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

        from tpDcc.libs.python import log as log_utils

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
            production_folder = self.get_production_folder()
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

        temp_env_var = self.get_temporary_environment_variable()
        os.environ[temp_env_var] = tempfile.gettempdir()
        project_temp_folder = path_utils.clean_path(
            os.path.join(tempfile.gettempdir(), '{}_temp'.format(self.get_clean_name())))
        if not os.path.isdir(project_temp_folder):
            try:
                os.makedirs(project_temp_folder)
            except Exception as exc:
                LOGGER.warning('Impossible to create temporally folder for project "{}"'.format(self.get_clean_name()))
        if os.path.isdir(project_temp_folder):
            os.environ[temp_env_var] = project_temp_folder

        icons_paths = tp.ResourcesMgr().get_resources_paths()

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

        slack_token = self.config.get('slack_token', '')
        slack_channel = self.config.get('slack_channel', '')
        if slack_token and slack_channel:
            os.environ['{}_SLACK_API_TOKEN'.format(self.get_clean_name().upper())] = 'xoxb-{}'.format(slack_token)
            os.environ['{}_SLACK_CHANNEL'.format(self.get_clean_name().upper())] = slack_channel

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

    def create_sequences_manager(self):
        """
        Creates instance of the sequences manager used by the project
        :return: ArtellaSequencesManager
        """

        sequences_manager = artellapipe.SequencesMgr()
        sequences_manager.set_project(self)

        return sequences_manager

    def create_shots_manager(self):
        """
        Creates instance of the shots manager used by the project
        :return: ArtellaShotsManager
        """

        shots_manager = artellapipe.ShotsMgr()
        shots_manager.set_project(self)

        return shots_manager

    def create_tasks_manager(self):
        """
        Creates instance of the tasks manager used by the project
        :return: ArtellaShotsManager
        """

        tasks_manager = artellapipe.TasksMgr()
        tasks_manager.set_project(self)

        return tasks_manager

    def create_media_manager(self):
        """
        Creates instance of hte media manager used by the project
        :return: ArtellaMediaManager
        """

        media_manager = artellapipe.MediaMgr()
        media_manager.set_project(self)

        return media_manager

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

    def create_casting_manager(self):
        """
        Crates instance of the casting manager used by the project
        :return: ArtellaCastingManager
        """

        casting_manager = artellapipe.CastMgr()
        casting_manager.set_project(self)

        return casting_manager

    def create_slack_manager(self):
        """
        Crates instance of the slack manager used by the project
        :return: SlackManager
        """

        slack_manager = artellapipe.SlackMgr()
        slack_manager.set_project(self)

        return slack_manager

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

    def get_temporary_environment_variable(self):
        """
        Returns environment variable used to store temporally path of the project
        :return: str
        """

        return '{}_TEMP'.format(self.get_clean_name().upper())

    def get_temporary_folder(self):
        """
        Returns path where temporally folder for current folder is located
        :return: str
        """

        temp_env = self.get_temporary_environment_variable()
        return os.environ[temp_env]

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

    def notify(self, title, msg):
        """
        Notifies given message to the user
        :param title: str
        :param msg:
        """

        self.tray.show_message(title=title, msg=msg)

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

    def get_drive(self):
        """
        Returns drive Artella project is located
        :return: str
        """

        project_path = self.get_path()
        if not project_path or not os.path.isdir(project_path):
            LOGGER.warning(
                'Impossible to retrieve project path drive because project path does not exists: "{}"'.format(
                    project_path))
            return None

        path_split = os.path.splitdrive(project_path)

        return path_split[0]

    def get_working_folder_name(self):
        """
        Returns working folder name of the current project
        :return: str
        """

        return self._config.get('working_folder')

    def get_working_folder(self):
        """
        Returns production folder of current project
        :return: str
        """

        return artella_lib.config.get('server', self.get_project_type()).get('working_folder')

    def get_production_folder_name(self):
        """
        Returns production folder name of current project
        :return: str
        """

        return self._config.get('production_folder')

    def get_production_folder(self):
        """
        Returns production folder of current project
        :return: str
        """

        return artella_lib.config.get('server', self.get_project_type()).get('production_folder')

    def get_production_path(self):
        """
        Returns path where Production data for current project is stored
        :return: str
        """

        project_path = self.get_path()
        if not project_path:
            LOGGER.warning('Impossible to retrieve productoin path because Artella project is not setup!')
            return

        production_folder_name = self.get_production_folder_name()
        return path_utils.clean_path(os.path.join(project_path, production_folder_name))

    def get_artella_url(self):
        """
        Returns Artella URL of the project
        :return: str
        """

        artella_web = artella_lib.config.get('server', self.get_project_type()).get('url')
        return '{}/project/{}/files'.format(artella_web, self.id)

    def get_artella_assets_url(self):
        """
        Returns URL of the Artella Assets of the project are located
        :return: str
        """

        assets_folder_name = self._config.get('assets_folder', default='Assets')
        return '{}/{}/'.format(self.get_artella_url(), assets_folder_name)

    def update_project(self):
        """
        Sets the current Maya project to the path where Artella project is located inside Artella folder
        """

        try:
            if tp.is_maya():
                import tpDcc.dccs.maya as maya
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
            from tpDcc.dccs.maya.core import helpers
            helpers.clean_student_line()

        if notify:
            self.tray.show_message(title='Save File', msg='File saved successfully!')

        return True

    # ==========================================================================================================
    # ASSETS
    # ==========================================================================================================

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
                            all_abc_roots.append(artellapipe.AssetNode(project=self, node=cnt_root))
                        else:
                            all_abc_roots.append((artellapipe.AssetNode(project=self, node=cnt_root), abc))
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
