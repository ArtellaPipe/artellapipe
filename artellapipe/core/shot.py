#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class that defines Artella Shot
"""

from __future__ import print_function, division, absolute_import

import logging

import artellapipe
from artellapipe.core import abstract

LOGGER = logging.getLogger()


class ArtellaShot(abstract.AbstractShot, object):

    def __init_(self, project, shot_data):
        super(ArtellaShot, self).__init__(project=project, shot_data=shot_data)

    @property
    def project(self):
        """
        Returns project linked to this assset
        :return: ArtellaProject
        """

        return self._project

    def get_id(self):
        """
        Implements abstract get_id function
        Returns the id of the shot
        :return: str
        """

        id_attr = artellapipe.ShotsMgr().config.get('data', 'id_attribute')
        asset_id = self._shot_data.get(id_attr, None)
        if not asset_id:
            LOGGER.warning(
                'Impossible to retrieve asset ID because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(id_attr, self._shot_data))
            return None

        return asset_id.rstrip()

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the sequence
        :return: str
        """

        name_attr = artellapipe.ShotsMgr().config.get('data', 'name_attribute')
        shot_name = self._shot_data.get(name_attr, None)
        if not shot_name:
            LOGGER.warning(
                'Impossible to retrieve shot name because shot data does not contains "{}" attribute.'
                '\nSequence Data: {}'.format(name_attr, self._shot_data))
            return None

        return shot_name.rstrip()

    def get_thumbnail_path(self):
        """
        Implements abstract get_path function
        Returns the path where shot thumbnail is located
        :return: str
        """

        thumb_attr = artellapipe.ShotsMgr().config.get('data', 'thumb_attribute')
        thumb_path = self._shot_data.get(thumb_attr, None)

        return thumb_path

    def get_sequence(self):
        """
        Returns the name of the sequence this shot belongs to
        :return: str
        """

        sequence_attr = artellapipe.ShotsMgr().config.get('data', 'sequence_attribute')
        sequence_name = self._shot_data.get(sequence_attr, None)
        if not sequence_name:
            LOGGER.warning(
                'Impossible to retrieve sequence name because shot data does not contains "{}" attribute.'
                '\nSequence Data: {}'.format(sequence_attr, self._shot_data))
            return None

        return sequence_name


artellapipe.register.register_class('Shot', ArtellaShot)
