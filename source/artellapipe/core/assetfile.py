#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for asset types
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from artellapipe.core import defines, artellalib


class ArtellaAssetType(object):

    FILE_TYPE = None
    FILE_EXTENSIONS = list()

    def __init__(self, asset):

        self._asset = asset

        self._history = None

        super(ArtellaAssetType, self).__init__()

    @property
    def project(self):
        """
        Returns project where this asset file belongs to
        :return: ArtellaProject
        """

        return self._asset.project

    def get_history(self, status, force_update=False):
        """
        Returns the history of the asset files
        :param status: ArtellaAssetFileStatus
        :param force_update: bool
        :return:
        """

        if self._history and not force_update:
            return self._history

        self._history = self._get_history(status=status)

        return self._history


    def get_working_files_for_file_type(self):
        """
        Returns all working files for this asset type
        :return: list(str)
        """

        print('HELLOOOOOOOOOOOOOOOOOO')

    def get_extension(self):
        """
        Returns the extension of the aseet file
        :return: str
        """

        return self._asset.project.assets_library_file_types.get()

    def _get_history(self, status):
        """
        Internal function that returns the history of the aset files
        Overrides in custom file types if necessary
        :param status: ArtellaAssetFileStatus
        :return:
        """

        asset_name = self._asset.get_name()
        asset_path = self._asset.get_path()
        file_path = os.path.join(asset_path, defines.ARTELLA_WORKING_FOLDER, self.FILE_TYPE, asset_name+self.FILE_EXTENSIONS[0])
        history = artellalib.get_asset_history(file_path=file_path)

        return history