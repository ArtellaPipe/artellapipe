#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains all constant definitions used by artellapipe-core
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


# Defines environment variable name that can setup to define folder where configuration files are located
ARTELLA_CONFIGURATION_ENV = 'ARTELLA_PROJECT_CONFIGURATIONS_FOLDER'

# Defines the name of the configuration file used by artellapipe to setup project
ARTELLA_PROJECT_CONFIG_FILE_NAME = 'config.yml'

# Defines the name of the changelog file used by artellapipe
ARTELLA_PROJECT_CHANGELOG_FILE_NAME = 'changelog.json'

# Defines the name of the shelf file used by artellapipe to setup project shelf
ARTELLA_PROJECT_SHELF_FILE_NAME = 'shelf.json'

# Defines the name of the menu file used by artellapipe to setup project shelf
ARTELLA_PROJECT_MENU_FILE_NAME = 'menu.json'

# Defines the name of the naing file used by artellapipe for pipeline naming
ARTELLA_PROJECT_DEFAULT_NAMING_FILE_NAME = 'naming.json'

# Defines the name of the version file used by artellapipe to check current tools version
ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME = '__version__.py'

# Defines the name of the attribute that defines the Artella project name
ARTELLA_CONFIG_PROJECT_NAME = 'PROJECT_NAME'

# Defines the name of the attribute that defines the Artella project number
ARTELLA_CONFIG_PROJECT_NUMBER = 'PROJECT_NUMBER'

# Defines the name of the attribute that defines the Artella version file name
ARTELLA_VERSION_FILE_NAME_ATTRIBUTE_NAME = 'PROJECT_VERSION_FILE'

# Defines the name of the attribute that defines the Artella project naming file name
ARTELLA_NAMING_FILE_NAME_ATTRIBUTE_NAME = 'PROJECT_NAMING_FILE'

# Defines the name of the attribute that defines the asset types in the Artella project
ARTELLA_CONFIG_ASSET_TYPES = 'ASSET_TYPES'

# Defines the name of the attribute that defines the asset files types in the Artella project
ARTELLA_CONFIG_ASSET_FILES = 'ASSET_FILES'

# Defines the name of the attribute that defines the list of paths that should be ignored during asset search
ARTELLA_ASSETS_IGNORED_PATHS_ATTRIBUTE_NAME = 'ASSET_IGNORED_PATHS'

# Defines the name of the attribute that defines the dict of file types supported by Artella Assets Viewer
ARTELLA_ASSETS_LIBRARY_SUPPORTED_TYPES_ATTRIBUTE_NAME = 'ASSETS_LIBRARY_SUPPORTED_FILES'

# Defines the name of the attribute that defines the name of the file that stores asset info file created by builder
ARTELLA_ASSET_DATA_FILENAME_ATTRIBUTE_NAME = 'PROJECT_ASSET_DATA_FILENAME'

# Defines the name of the attribute that defines the asset files types that must be published to consider
# an asset ready for production
ARTELLA_CONFIG_ASSET_MUST_FILES_ATTRIBUTE_NAME = 'ASSET_MUST_FILES'

# Define attribute name used to define the list of types that can be used to tag all the elements of the short
ARTELLA_CONFIG_TAG_TYPES_ATTRIBUTE_NAME = 'TAG_TYPES'

# Defines attribute name used to define a dictionary that maps tag types with categories in the Artella Outliner
ARTELLA_CONFIG_OUTLINER_CATEGORIES_ATTRIBUTE_NAME = 'OUTLINER_CATEGORIES'

# Defines attribute name used to define project shot regex
ARTELLA_CONFIG_SHOT_REGEX_ATTRIBUTE_NAME = 'SHOT_REGEX'

# Defines the attribute name used to define shot file extension
ARTELLA_SHOT_EXTENSION_ATTRIBUTE_NAME = 'SHOT_EXTENSION'

# Defines the attribute name used to define shot project file types
ARTELLA_SHOT_FILE_TYPES_ATTRIBUTE_NAME = 'SHOT_FILE_TYPES'

# Defines the name of the attribute that defines the working status of an asset
ARTELLA_CONFIG_ASSET_WIP_STATUS = 'ASSET_WIP_STATUS'

# Defines the name of the attribute that defines the working status of an asset
ARTELLA_CONFIG_ASSET_PUBLISH_STATUS = 'ASSET_PUBLISH_STATUS'

# Defines the name of the attribute that defines the project URL
ARTELLA_PROJECT_URL = 'PROJECT_URL'

# Defines the name of the attribute that defines the project icon
ARTELLA_PROJECT_ICON = 'PROJECT_ICON'

# Defines the name of the attribute that defines the name of the icon used by shelf category button
ARTELLA_CONFIG_SHELF_ICON = 'SHELF_ICON'

# Defines the name of the attribute that defines the name of the icon used by Artella project tray
ARTELLA_CONFIG_TRAY_ICON = 'TRAY_ICON'

# Defines the name of the attribute that defines the Artella project id
ARTELLA_CONFIG_PROJECT_ID = 'PROJECT_ID'

# Defines the name of the attribute that defines the environemtn variable used to store Artella project path
ARTELLA_CONFIG_ENVIRONMENT_VARIABLE = 'PROJECT_ENV_VARIABLE'

# Defines the name of the attribute that defines the paths that need to be registered in Python path
ARTELLA_CONFIG_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME = 'PATHS_TO_REGISTER'

# Defines the name of the attribute that defines the paths that need to be registered in Python path
ARTELLA_CONFIG_EMAIL_ATTRIBUTE_NAME = 'EMAILS'

# Defines the default name used by Artella projects
ARTELLA_DEFAULT_PROJECT_NAME = 'Artella'

# Defines the default name used for set environment variable for Artella Project
ARTELLA_DEFAULT_ENVIRONMENT_VARIABLE = 'ARTELLA_PROJECT'

# Defines the attribute name used to define progress bar color 0
ARTELLA_PROGRESS_BAR_COLOR_0_ATTRIBUTE_NAME = 'PROGRESS_BAR_COLOR_0'

# Defines the attribute name used to define progress bar color 1
ARTELLA_PROGRESS_BAR_COLOR_1_ATTRIBUTE_NAME = 'PROGRESS_BAR_COLOR_1'

# Defines the attribute name used to define the extension of the shaders files
ARTELLA_SHADERS_EXTENSION_ATTRIBUTE_NAME = 'SHADERS_EXTENSION'

# Defines the attribute name used to define the URL where Playblast presets are located
ARTELLA_PLAYBLAST_PRESETS_URL_ATTRIBUTE_NAME = 'PLAYBLAST_PRESETS_URL'

# Defines the name of the Artella plugin
ARTELLA_MAYA_PLUGIN_NAME = 'Artella.py'

# Defines the name of the Artella executable
ARTELLA_APP_NAME = 'lifecycler'

# Defines the name of the working folder used by Artella
ARTELLA_WORKING_FOLDER = '__working__'

# Defines Artella production folder
ARTELLA_PRODUCTION_FOLDER = '_art/production'

# Defines the environment variable used by Artella to reference to user local installation folder
ARTELLA_ROOT_PREFIX = 'ART_LOCAL_ROOT'

# Defines path to Artella webpage
ARTELLA_WEB = 'https://www.artella.com'

# Defines path to Artella server
ARTELLA_CMS_URL = 'https://cms-static.artella.com'

# Defines file name used by Artella to detect next version name
ARTELLA_NEXT_VERSION_FILE_NAME = 'version_to_run_next'

# Defines default pipeline folder name
ARTELLA_PIPELINE_DEFAULT_FOLDER_NAME = 'pipeline'

# Defines default externals folder name
ARTELLA_PIPELINE_EXTERNALS_DEFAULT_FOLDER_NAME = 'externals'

# Defines default to register
ARTELLA_CONFIG_DEFAULT_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME = ["pipeline", "pipeline/externals"]

# Defines category name for All categories
ARTELLA_ALL_CATEGORIES_NAME = 'All'

# Defines the name of Assets Artella folder
ARTELLA_ASSETS_FOLDER_NAME = 'Assets'

# Defines the name of the Production Artella folder
ARTELLA_PRODUCTION_FOLDER_NAME = 'Production'

# Defines the default name used for assets
ARTELLA_DEFAULT_ASSET_NAME = 'New_Asset'

# Defines the dict attribute used to access asset attributes in standard Artella assets
ARTELLA_ASSET_DATA_ATTR = 'asset'

# Defines the dict attribute used to store asset name in standard Artella assets
ARTELLA_ASSET_DATA_NAME_ATTR = 'name'

# Defines the dict attribute used to store asset path in standard Artella assets
ARTELLA_ASSET_DATA_PATH_ATTR = 'path'

# Defines the dict attribute used to store asset description in standard Artella assets
ARTELLA_ASSET_DATA_DESCRIPTION_ATTR = 'description'

# Defines the dict attribute used to store asset icon in standard Artella assets
ARTELLA_ASSET_DATA_ICON_ATTR = 'icon'

# Defines the dict attribute used to store asset icon format in standard Artella assets
ARTELLA_ASSET_DATA_ICON_FORMAT_ATTR = 'icon_format'

# Defines sync operation that should sync all asset types
ARTELLA_SYNC_ALL_ASSET_TYPES = 'all'

# Defines of art asset type
ARTELLA_ART_ASSET_TYPE = 'art'

# Defines of textures asset type
ARTELLA_TEXTURES_ASSET_TYPE = 'textures'

# Defines of model asset type
ARTELLA_MODEL_ASSET_TYPE = 'model'

# Defines of shading asset type
ARTELLA_SHADING_ASSET_TYPE = 'shading'

# Defines of rig asset type
ARTELLA_RIG_ASSET_TYPE = 'rig'

# Defines of groom asset type
ARTELLA_GROOM_ASSET_TYPE = 'groom'

# Define the asset sync type that synchronizes all asset statuses (working and published)
ARTELLA_SYNC_ALL_ASSET_STATUS = 'all'

# Defines the asset sync type that synchronizes working status
ARTELLA_SYNC_WORKING_ASSET_STATUS = 'working'

# Defines the asset sync type that synchronizes published status
ARTELLA_SYNC_PUBLISHED_ASSET_STATUS = 'published'

# Defines the default extension used by Artella pipeline files
ARTELLA_DEFAULT_ASSET_FILES_EXTENSION = '.ma'

# Defines the name of the attribute for tag info
ARTELLA_TAG_INFO_ATTRIBUTE_NAME = 'tag_info'

# Defines the prefix used to store shot override attributes
ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_PREFX = 'shot_overrides'

# Defines the split used to separate shot override prefix and shot override name in shot override attributes
ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_SEPARATOR = '__'
