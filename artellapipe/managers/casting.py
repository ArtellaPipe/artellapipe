#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager for shot/asset/sequences casting
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging

from tpDcc.libs.python import decorators

import artellapipe
from artellapipe.utils import exceptions

LOGGER = logging.getLogger()


class ArtellaCastingManager(object):
    def __init__(self):
        self._project = None

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project

    def get_ocurrences_of_asset_in_shot(self, asset_name, shot_name, force_update=False):
        """
        Returns the number of ocurrences of given asset in given shot
        :param asset_name: str, name of the asset
        :param shot_name: str, name of the shot
        :return: int or None
        """

        if not self._check_project():
            return None

        asset = artellapipe.AssetsMgr().find_asset(asset_name)
        if not asset:
            LOGGER.warning('Impossible to return occurrences because asset "{}" does not exists!'.format(asset_name))
            return None

        shot = artellapipe.ShotsMgr().find_shot(shot_name)
        if not shot:
            LOGGER.warning('Impossible to return occurrences because shot "{}" does not exists!'.format(shot_name))
            return None

        shot_id = shot.get_id()

        tracker = artellapipe.Tracker()
        total_occurrences = tracker.get_occurrences_of_asset_in_shot(shot_id, asset_name, force_update=force_update)

        return total_occurrences

    def _check_tracker(self, force_login=True):
        """
        Internal function that checks whether or not production tracking is ready to be used with this manager
        :return: bool
        """

        if not artellapipe.Tracker().is_logged() and force_login:
            artellapipe.Tracker().login()
        if not artellapipe.Tracker().is_logged():
            LOGGER.warning(
                'Impossible to find casting of current project because user is not log into production tracker')
            return None

    def _check_project(self):
        """
        Internal function that checks whether or not casting manager has a project set. If not an exception is raised
        """

        if not self._project:
            raise exceptions.ArtellaProjectUndefinedException('Artella Project is not defined!')

        return True


@decorators.Singleton
class ArtellaCastingManagerSingleton(ArtellaCastingManager, object):
    def __init__(self):
        ArtellaCastingManager.__init__(self)


artellapipe.register.register_class('CastMgr', ArtellaCastingManagerSingleton)
