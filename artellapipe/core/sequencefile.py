#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for sequence files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging

import artellapipe
from artellapipe.core import file

LOGGER = logging.getLogger()


class ArtellaSequenceFile(file.ArtellaFile, object):
    def __init__(self, file_sequence=None, file_path=None):

        self._sequence = file_sequence

        super(ArtellaSequenceFile, self).__init__(
            file_name=self._sequence.get_name() if self._sequence else None, file_path=file_path)

    @property
    def sequence(self):
        """
        Returns sequence linked to this file type
        :return: ArtellaSequence
        """

        return self._sequence

    def has_valid_object(self):
        """
        Implements base ArtellaFile has_valid_object function
        Returns whether valid object is attached to this file
        :return: bool
        """

        return bool(self._sequence)

    def get_template_dict(self, **kwargs):
        """
        Returns dictionary with the template data for this file
        :return: dict
        """

        return self._sequence.get_template_dict(**kwargs)

    def get_project(self):
        """
        Implements base ArtellaFile get_project function
        Returns project where this sequence file belongs to
        :return: ArtellaProject
        """

        return self._sequence.project

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

        return self._sequence.get_file(
            file_type=file_type, status=status, extension=extension, fix_path=fix_path, version=version)

    def get_path(self):
        """
        Implements base ArtellaFile get_path function
        Returns path of the attached object
        :return: str
        """

        return self._sequence.get_path()

    def get_name(self):
        """
        Returns name of the attached object
        :return: str
        """

        return self._sequence.get_name()

    # def get_extension(self):
    #     """
    #     Returns the extension of the aseet file
    #     :return: str
    #     """
    #
    #     return self.get_project().assets_library_file_types.get()

    def get_latest_published_versions(self):
        """
        Implements base ArtellaFile get_path function
        Returns latest published version of file
        :return: str
        """

        file_path = self.get_path()
        return artellapipe.SequencesMgr().get_latest_published_versions(file_path, file_type=self.FILE_TYPE)
