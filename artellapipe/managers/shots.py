#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle shots
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import re
import logging

from tpPyUtils import decorators

import artellapipe.register
from artellapipe.core import config

LOGGER = logging.getLogger()


class ArtellaShotsManager(object):
    def __init__(self):
        self._project = None
        self._shots = list()
        self._config = None

    @property
    def config(self):
        return self._config

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project
        self._config = config.get_config(project, 'artellapipe-shots')

    def get_shot_regex(self):
        """
        Returns regex used to identify solstice shots
        :return:
        """

        shot_regex = self.config.get('shot_regex', default=None)
        if not shot_regex:
            LOGGER.warning('No Shot Regex defined in artellapipe.shots configuration file!')
            return None

        return re.compile(shot_regex)

    @decorators.timestamp
    def get_shots(self, force_update=False):
        """
        Returns all shots of the given sequence name
        :param force_update: bool
        :return: list(ArtellaShot)
        """

        if self._shots and not force_update:
            return self._shots

        if self._production_info and not force_update:
            production_info = self._production_info
        else:
            production_info = self._update_production_info()
        if not production_info:
            return

        sequences = self.get_sequences(force_update=force_update)
        for seq in sequences:
            sequence_path = seq.get_path()
            if not sequence_path:
                LOGGER.warning('Impossible to retrieve path for Sequence: {}!'.format(seq.name))
                continue
            sequence_info = seq.get_info()
            print(sequence_info)

    def get_shots_from_sequence(self, sequence_name, force_update=False):
        """
        Returns shots of the given sequence name
        :param sequence_name: str
        :param force_update: bool
        :return:
        """

        shots = self.get_shots(force_update=force_update)

    def get_shot_name_regex(self):
        """
        Returns regex used to identeify shots
        :return: str
        """

        return re.compile(r"{}".format(self._shot_regex))


@decorators.Singleton
class ArtellaShotsManagerSingleton(ArtellaShotsManager, object):
    def __init__(self):
        ArtellaShotsManager.__init__(self)


artellapipe.register.register_class('ShotsMgr', ArtellaShotsManagerSingleton)
