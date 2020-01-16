#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for asset files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging

import artellapipe
from artellapipe.core import defines, file

LOGGER = logging.getLogger()


class ArtellaAssetFile(file.ArtellaFile, object):
    def __init__(self, file_asset=None, file_path=None, file_name=None):

        self._asset = file_asset
        file_name = file_name or self._asset.get_name() if self._asset else None

        super(ArtellaAssetFile, self).__init__(file_name=file_name, file_path=file_path)

    @property
    def asset(self):
        """
        Returns asset linked to this file type
        :return: ArtellaAssset
        """

        return self._asset

    def has_valid_object(self):
        """
        Implements base ArtellaFile has_valid_object function
        Returns whether valid object is attached to this file
        :return: bool
        """

        return bool(self._asset)

    def get_template_dict(self, **kwargs):
        """
        Returns dictionary with the template data for this file
        :param extension: str
        :return: dict
        """

        template_dict = {
            'project_path': self._project.get_path(),
            'asset_name': self._asset.get_name(),
            'asset_type': self._asset.get_category(),
            'file_extension': kwargs.get('extension', self.FILE_EXTENSIONS[0])
        }

        return template_dict

    def get_project(self):
        """
        Implements base ArtellaFile get_project function
        Returns project where this asset file belongs to
        :return: ArtellaProject
        """

        return self._asset.project

    def get_file(self, file_type, status, extension, fix_path=False, version=None):
        """
        Implements base ArtellaFile get_file function
        Returns file of the attached object
        :param file_type: str
        :param status: str
        :param extension: str
        :param fix_path: bool
        :param version: str
        :return: str
        """

        return self._asset.get_file(
            file_type=file_type, status=status, extension=extension, fix_path=fix_path, version=version)

    def get_path(self):
        """
        Implements base ArtellaFile get_path function
        Returns path of the attached object
        :return: str
        """

        return self._asset.get_path()

    def get_name(self):
        """
        Returns name of the attached object
        :return: str
        """

        return self._asset.get_name()

    def get_extension(self):
        """
        Returns the extension of the aseet file
        :return: str
        """

        return self.get_project().assets_library_file_types.get()

    def get_latest_published_versions(self):
        """
        Implements base ArtellaFile get_path function
        Returns latest published version of file
        :return: str
        """

        file_path = self.get_path()
        return artellapipe.AssetsMgr().get_latest_published_versions(file_path, file_type=self.FILE_TYPE)

    def get_file_paths(self, return_first=False, fix_path=True, **kwargs):

        if self.FILE_TYPE not in self._asset.FILES:
            LOGGER.warning(
                'FileType "{}" is not a valid file for Assets of type "{}"'.format(
                    self.FILE_TYPE, self._asset.FILE_TYPE))
            return list()

        file_paths = super(
            ArtellaAssetFile, self).get_file_paths(return_first=return_first, fix_path=fix_path, **kwargs)
        if file_paths:
            return file_paths

        status = kwargs.get('status', defines.ArtellaFileStatus.PUBLISHED)
        if status == defines.ArtellaFileStatus.WORKING:
            file_path = self.get_working_path()
        else:
            file_path = self.get_latest_local_published_path()

        if not file_path:
            return None if return_first else file_paths

        if fix_path:
            file_path = artellapipe.FilesMgr().fix_path(file_path)

        if return_first:
            return file_path
        else:
            return [file_path]
