#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for shot files
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


class ArtellaShotFile(file.ArtellaFile, object):
    def __init__(self, file_shot=None, file_path=None):

        self._shot = file_shot

        super(ArtellaShotFile, self).__init__(
            file_name=self._shot.get_name() if self._shot else None, file_path=file_path)

    @property
    def shot(self):
        """
        Returns shot linked to this file type
        :return: ArtellaShot
        """

        return self.shot

    def has_valid_object(self):
        """
        Implements base ArtellaFile has_valid_object function
        Returns whether valid object is attached to this file
        :return: bool
        """

        return bool(self._shot)

    def get_template_dict(self, **kwargs):
        """
        Returns dictionary with the template data for this file
        :return: dict
        """

        return self._shot.get_template_dict(**kwargs)

    def get_project(self):
        """
        Implements base ArtellaFile get_project function
        Returns project where this sequence file belongs to
        :return: ArtellaProject
        """

        return self._shot.project

    def get_file(self, status=defines.ArtellaFileStatus.WORKING, extension=None, fix_path=False, version=None):
        """
        Implements base ArtellaFile get_file function
        Returns file of the attached object
        :param status: str
        :param extension: str
        :param fix_path: bool
        :param version: str
        :return: str
        """

        return self._shot.get_file(
            file_type=self.FILE_TYPE, status=status, extension=extension, fix_path=fix_path, version=version)

    def get_path(self):
        """
        Implements base ArtellaFile get_path function
        Returns path of the attached object
        :return: str
        """

        return self._shot.get_path()

    def get_name(self):
        """
        Returns name of the attached object
        :return: str
        """

        return self._shot.get_name()

    def get_latest_published_versions(self):
        """
        Implements base ArtellaFile get_path function
        Returns latest published version of file
        :return: str
        """

        file_path = self.get_path()
        return artellapipe.SequencesMgr().get_latest_published_versions(file_path, file_type=self.FILE_TYPE)
