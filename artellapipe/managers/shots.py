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

import os
import logging
import inspect
import traceback
import importlib
from collections import OrderedDict

import tpDcc
from tpDcc.libs.python import decorators, python, path as path_utils

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe
from artellapipe.utils import exceptions
from artellapipe.libs.artella.core import artellalib, artellaclasses

LOGGER = logging.getLogger('artellapipe')


class ShotsManager(object):

    _config = None
    _shots = list()
    _registered_shot_classes = list()

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tpDcc.ConfigsMgr().get_config(
                config_name='artellapipe-shots',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment())

        return self.__class__._config

    @property
    def shot_classes(self):
        if not self.__class__._registered_shot_classes:
            self._register_shot_classes()

        return self.__class__._registered_shot_classes

    @property
    def shot_types(self):
        return self.config.get('types', default=dict()).keys()

    @property
    def shots(self):
        return self.__class__._shots

    def register_shot_class(self, shot_class):
        """
        Registers a new shot class into the project
        :param shot_class: cls
        """

        if shot_class in self.shot_classes:
            LOGGER.warning(
                'Shot Class: "{}" is already registered. Skipping ...'.format(shot_class))
            return False

        self.__class__._registered_shot_classes.append(shot_class)

        return True

    @decorators.timestamp
    def find_all_shots(self, force_update=False, force_login=True):
        """
        Returns all shots of the project
        :param force_update:  bool, Whether shots cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: list(ArtellaShot)
        """

        self._check_project()

        if self.shots and not force_update:
            return self.shots

        python.clear_list(self.__class__._shots)

        if not artellapipe.Tracker().is_logged() and force_login:
            artellapipe.Tracker().login()
        if not artellapipe.Tracker().is_logged():
            LOGGER.warning(
                'Impossible to find shots of current project because user is not log into production tracker')
            return None
        tracker = artellapipe.Tracker()
        shots_list = tracker.all_project_shots()
        if not shots_list:
            LOGGER.warning('No shots found in current project!')
            return None

        for shot_data in shots_list:
            new_shot = self.create_shot(shot_data)
            self.__class__._shots.append(new_shot)

        self.__class__._shots.sort(key=lambda x: x.get_start_frame(), reverse=True)

        return self.shots

    def find_all_shots_in_current_scene(self, force_update=False, force_login=True):
        """
        Returns all nodes that are in current scene
        :param force_update:  bool, Whether shots cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: list(ArtellaShot)
        """

        all_shots = self.find_all_shots(force_update=force_update, force_login=force_login) or list()
        return [shot for shot in all_shots if shot.get_node() is not None]

    def find_non_muted_shots(self, force_update=False, force_login=True):
        """
        Returns all shots in the scene that are not muted
        :param force_update:  bool, Whether shots cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: list(ArtellaShot)
        """

        all_shots = self.find_all_shots_in_current_scene(force_update=force_update, force_login=force_login)
        non_muted_shots = [shot for shot in all_shots if not shot.is_muted()]

        return non_muted_shots

    def find_shot(self, shot_name=None, force_update=False, force_login=True):
        """
        Returns shot of the project if found
        :param shot_name: str, name of the sequence to find
        :param force_update: bool, Whether sequences cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: ArtellaShot
        """

        self._check_project()

        shots_found = list()
        all_shots = self.find_all_shots(force_update=force_update, force_login=force_login) or list()
        for shot in all_shots:
            if shot.get_name() == shot_name:
                shots_found.append(shot)

        if not shots_found:
            return None

        if len(shots_found) > 1:
            LOGGER.warning('Found multiple instances of Shot "{}"'.format(shot_name))

        return shots_found[0]

    def find_shot_in_current_scene(self, shot_name=None, force_update=False, force_login=True):
        """
        Returns shot of the project if found in current scene
        :param shot_name: str, name of the sequence to find
        :param force_update: bool, Whether sequences cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: ArtellaShot
        """

        self._check_project()

        shots_found = list()
        all_shots = self.find_all_shots_in_current_scene(force_update=force_update, force_login=force_login) or list()
        if not shot_name:
            return all_shots

        for shot in all_shots:
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

        return artellapipe.Shot(project=artellapipe.project, shot_data=shot_data)

    def get_shots_from_sequence(self, sequence_name, force_update=False, force_login=True):
        """
        Returns shots of the given sequence name
        :param sequence_name: str
        :param force_update: bool
        :param force_login: bool
        :return:
        """

        sequence_shots = list()
        all_shots = self.find_all_shots(force_update=force_update, force_login=force_login)
        for shot in all_shots:
            if shot.get_sequence() == sequence_name:
                sequence_shots.append(shot)

        return sequence_shots

    def is_valid_shot_type(self, shot_type):
        """
        Returns whether or not given type is a valid shot type
        :param shot_type: str
        :return: bool
        """

        return shot_type in self.shot_types

    def get_shot_file(self, file_type, extension=None):
        """
        Returns shot file object class linked to given file type for current project
        :param file_type: str
        :return: ArtellaShotType
        """

        self._check_project()

        if not artellapipe.FilesMgr().is_valid_file_type(file_type):
            return

        shot_file_class_found = None
        for sequence_file_class in artellapipe.FilesMgr().file_classes:
            if sequence_file_class.FILE_TYPE == file_type:
                shot_file_class_found = sequence_file_class
                break

        if not shot_file_class_found:
            LOGGER.warning('No Shot File Class found for file of type: "{}"'.format(file_type))
            return

        return shot_file_class_found

    def get_latest_published_versions(self, shot_path, file_type=None):
        """
        Returns all published version of the the different files of the given shot
        :param shot_path: str, path of the shot
        :param file_type: str, if given only paths of the given file type will be returned (model, rig, etc)
        :return: list(dict), number of version, name of version and version path
        """

        latest_version = list()

        versions = dict()
        status = artellalib.get_status(shot_path, as_json=True)

        status_data = status.get('data')
        if not status_data:
            LOGGER.info('Impossible to retrieve data from Artella in file: "{}"'.format(shot_path))
            return

        for name, data in status_data.items():
            if name in ['latest', '_latest']:
                continue
            if file_type and file_type not in name:
                continue
            try:
                version = artellalib.split_version(name)[1]
                versions[version] = name
            except Exception as exc:
                pass

        ordered_versions = OrderedDict(sorted(versions.items()))

        current_index = -1
        valid_version = False
        version_found = None
        while not valid_version and current_index >= (len(ordered_versions) * -1):
            version_found = ordered_versions[ordered_versions.keys()[current_index]]
            valid_version = self._check_valid_published_version(shot_path, version_found)
            if not valid_version:
                current_index -= 1
        if valid_version and version_found:
            version_path = path_utils.clean_path(os.path.join(shot_path, '__{}__'.format(version_found)))
            latest_version.append({
                'version': ordered_versions.keys()[current_index],
                'version_name': version_found,
                'version_path': version_path}
            )

        return latest_version

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

    def export_shot(self, shot_name, start_frame=101, new_version=False, comment=None):
        """
        Export shots
        :param shot_name: str
        :param start_frame: 101
        :param new_version: bool
        :param comment: str
        :return:
        """

        shot_layout_file_type = self.config.get('shot_layout_file_type', default='shot_layout')
        shot = self.find_shot(shot_name)
        file_type = shot.get_file_type(shot_layout_file_type)
        if not file_type:
            LOGGER.warning(
                'Impossible to export shot "{}" because file type "{}" was not found!'.format(
                    shot_name, shot_layout_file_type))
            return False

        valid_export = file_type.export_file(start_frame=start_frame)
        if not valid_export:
            LOGGER.warning('Something went wrong while exporting shot: "{}"'.format(shot_name))
            return False

        shot_file_path = file_type.get_file()
        if not shot_file_path or not os.path.exists(shot_file_path):
            LOGGER.warning('Shot was not exported in proper path: "{}"'.format(shot_file_path))
            return False

        if not comment:
            comment = 'Shot "{}" exported!'.format(shot_name)
        if new_version:
            artellapipe.FilesMgr().lock_file(file_path=shot_file_path, notify=False)
            valid_version = artellapipe.FilesMgr().upload_working_version(
                file_path=shot_file_path, skip_saving=True, notify=True, comment=comment)
            if not valid_version:
                LOGGER.warning('Was not possible to upload new version of shot file: {}'.format(shot_file_path))

        return True

    def _check_project(self):
        """
        Internal function that checks whether or not assets manager has a project set. If not an exception is raised
        """

        if not hasattr(artellapipe, 'project') or not artellapipe.project:
            raise exceptions.ArtellaProjectUndefinedException('Artella Project is not defined!')

        return True

    def _check_valid_published_version(self, file_path, version):
        """
        Returns whether the given version is a valid one or not
        :return: bool
        """

        version_valid = True
        version_path = os.path.join(file_path, '__{}__'.format(version))
        version_info = artellalib.get_status(version_path)
        if version_info:
            if isinstance(version_info, artellaclasses.ArtellaHeaderMetaData):
                version_valid = False
            else:
                for n, d in version_info.references.items():
                    if d.maximum_version_deleted and d.deleted:
                        version_valid = False

        return version_valid

    def _register_shot_classes(self):
        """
        Internal function that registers project shot classes
        """

        if not hasattr(artellapipe, 'project') or not artellapipe.project:
            LOGGER.warning('Impossible to register shot classes because Artella project is not defined!')
            return False

        for shot_type, shot_type_info in self.config.get('types', default={}).items():
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
