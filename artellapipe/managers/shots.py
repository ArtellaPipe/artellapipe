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
import inspect
import traceback
import importlib

from tpPyUtils import decorators, python

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe.register
from artellapipe.core import config
from artellapipe.utils import exceptions

LOGGER = logging.getLogger()


class ArtellaShotsManager(object):
    def __init__(self):
        self._project = None
        self._shots = list()
        self._config = None
        self._registered_shot_classes = list()

    @property
    def config(self):
        return self._config

    @property
    def shot_classes(self):
        return self._registered_shot_classes

    @property
    def shot_types(self):
        return self._config.get('types', default=dict()).keys()

    @property
    def shots(self):
        return self._shots

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project
        self._config = config.get_config(project, 'artellapipe-shots')

        self._register_shot_classes()

    def register_shot_class(self, shot_class):
        """
        Registers a new shot class into the project
        :param shot_class: cls
        """

        if shot_class in self._registered_shot_classes:
            LOGGER.warning(
                'Shot Class: "{}" is already registered. Skipping ...'.format(shot_class))
            return False

        self._registered_shot_classes.append(shot_class)

        return True

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
    def find_all_shots(self, force_update=False):
        """
        Returns all shots of the given sequence
        :param force_update: bool
        :return: list(ArtellaShot)
        """

        self._check_project()

        if self._shots and not force_update:
            return self._shots

        python.clear_list(self._shots)

        tracker = artellapipe.Tracker()
        shots_list = tracker.all_project_shots()
        if not shots_list:
            LOGGER.warning('No shots found in current project!')
            return None

        for shot_data in shots_list:
            new_shot = self.create_shot(shot_data)
            self._shots.append(new_shot)

        return self._shots

    def find_shot(self, shot_name=None, force_update=False):
        """
        Returns shot of the project if found
        :param shot_name: str, name of the sequence to find
        :param force_update: bool, Whether sequences cache updated must be forced or not
        :return: ArtellaShort
        """

        self._check_project()

        shots_found = list()
        all_sequences = self.find_all_shots(force_update=force_update) or list()
        for shot in all_sequences:
            if shot.get_name() == shot_name:
                shots_found.append(shot)

        if not shots_found:
            return None

        if len(shots_found) > 1:
            LOGGER.warning('Found multiple instances of Shot "{}"'.format(shot_name))

        return shots_found[0]

    def create_shot(self, shot_data):
        """
        Returns a new shot with the given data
        :param shot_data: dict
        :return:
        """

        return artellapipe.Shot(project=self._project, shot_data=shot_data)

    @decorators.timestamp
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
        Returns regex used to identify shots
        :return: str
        """

        return re.compile(r"{}".format(self.get_shot_regex()))

    def get_default_shot_name(self):
        """
        Returns the default name used by shots
        :return: str
        """

        return self.config.get('default_name', default='New Shot')

    def get_default_shot_thumb(self):
        """
        Returns the default thumb used by shots
        :return: str
        """

        return self.config.get('default_thumb', default='default')

    def _check_project(self):
        """
        Internal function that checks whether or not assets manager has a project set. If not an exception is raised
        """

        if not self._project:
            raise exceptions.ArtellaProjectUndefinedException('Artella Project is not defined!')

        return True

    def _register_shot_classes(self):
        """
        Internal function that registers project shot classes
        """

        if not self._project:
            LOGGER.warning('Impossible to register shot classes because Artella project is not defined!')
            return False

        for shot_type, shot_type_info in self._config.get('types', default={}).items():
            shot_files = shot_type_info.get('files', list())
            full_shot_class = shot_type_info.get('class', None)
            if not full_shot_class:
                LOGGER.warning('No class defined for Shot Type "{}". Skipping ...'.format(shot_type))
                continue
            shot_class_split = full_shot_class.split('.')
            shot_class = shot_class_split[-1]
            shot_module = '.'.join(shot_class_split[:-1])
            LOGGER.info('Registering Shot: {}'.format(shot_module))

            try:
                module_loader = loader.find_loader(shot_module)
            except (RuntimeError, ImportError) as exc:
                LOGGER.warning("Impossible to import Shot Module: {} | {} | {}".format(
                    shot_module, exc, traceback.format_exc()))
                continue

            class_found = None
            mod = importlib.import_module(module_loader.fullname)
            for cname, obj in inspect.getmembers(mod, inspect.isclass):
                if cname == shot_class:
                    class_found = obj
                    break

            if not class_found:
                LOGGER.warning('No Shot Class "{}" found in Module: "{}"'.format(shot_class, shot_module))
                continue

            obj.FILE_TYPE = shot_type
            obj.FILES = shot_files

            self.register_shot_class(obj)

        return True


@decorators.Singleton
class ArtellaShotsManagerSingleton(ArtellaShotsManager, object):
    def __init__(self):
        ArtellaShotsManager.__init__(self)


artellapipe.register.register_class('ShotsMgr', ArtellaShotsManagerSingleton)
