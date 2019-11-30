#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains all constant definitions used by artellapipe
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


class ArtellaFileStatus(object):

    WORKING = 'working'
    PUBLISHED = 'published'
    ALL = 'All'

    @classmethod
    def is_valid(cls, status):
        """
        Returns whether given status is valid or not
        :param status: str
        :return: bool
        """

        return status == cls.WORKING or status == cls.PUBLISHED or status == cls.ALL

    @classmethod
    def supported_statuses(cls):
        """
        Returns list of supported Artella Asset File Statuses
        :return: list(str)
        """

        return cls.WORKING, cls.PUBLISHED, cls.ALL


# Defines the name of the changelog file used by artellapipe
ARTELLA_PROJECT_CHANGELOG_FILE_NAME = 'changelog.yml'

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

# Defines the prefix used to store shot override attributes
ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_PREFX = 'shot_overrides'

# Defines the split used to separate shot override prefix and shot override name in shot override attributes
ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_SEPARATOR = '__'
