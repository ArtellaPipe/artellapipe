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
ARTELLA_PROJECT_CHANGELOG_FILE_NAME = 'changelog.yml'

# Defines the name of the shelf file used by artellapipe to setup project shelf
ARTELLA_PROJECT_SHELF_FILE_NAME = 'shelf.json'

# Defines the name of the menu file used by artellapipe to setup project shelf
ARTELLA_PROJECT_MENU_FILE_NAME = 'menu.json'

# Defines the name of the naing file used by artellapipe for pipeline naming
ARTELLA_PROJECT_DEFAULT_NAMING_FILE_NAME = 'naming.json'

# Defines the name of the version file used by artellapipe to check current tools version
ARTELLA_PROJECT_DEFAULT_VERSION_FILE_NAME = '__version__.py'

# Defines attribute name used to define a dictionary that maps tag types with categories in the Artella Outliner
ARTELLA_CONFIG_OUTLINER_CATEGORIES_ATTRIBUTE_NAME = 'OUTLINER_CATEGORIES'

# Defines attribute name used to define project shot regex
ARTELLA_CONFIG_SHOT_REGEX_ATTRIBUTE_NAME = 'SHOT_REGEX'

# Defines the attribute name used to define shot file extension
ARTELLA_SHOT_EXTENSION_ATTRIBUTE_NAME = 'SHOT_EXTENSION'

# Defines the attribute name used to define shot project file types
ARTELLA_SHOT_FILE_TYPES_ATTRIBUTE_NAME = 'SHOT_FILE_TYPES'

# Defines the name of the attribute that defines the working status of an asset
ARTELLA_CONFIG_ASSET_PUBLISH_STATUS = 'ASSET_PUBLISH_STATUS'

# Defines the name of the attribute that defines the environemtn variable used to store Artella project path
ARTELLA_CONFIG_ENVIRONMENT_VARIABLE = 'PROJECT_ENV_VARIABLE'

# Defines the name of the attribute that defines the paths that need to be registered in Python path
ARTELLA_CONFIG_FOLDERS_TO_REGISTER_ATTRIBUTE_NAME = 'PATHS_TO_REGISTER'

# Defines the default name used for assets
ARTELLA_DEFAULT_ASSET_NAME = 'New_Asset'

# Defines the name of the attribute for tag info
ARTELLA_TAG_INFO_ATTRIBUTE_NAME = 'tag_info'

# Defines the prefix used to store shot override attributes
ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_PREFX = 'shot_overrides'

# Defines the split used to separate shot override prefix and shot override name in shot override attributes
ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_SEPARATOR = '__'
