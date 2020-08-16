#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle sequences
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


class SequencesManager(object):

    _config = None
    _sequences = list()
    _registered_sequence_classes = list()

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tpDcc.ConfigsMgr().get_config(
                config_name='artellapipe-sequences',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment())

        return self.__class__._config

    @property
    def sequence_classes(self):
        if not self.__class__._registered_sequence_classes:
            self._register_sequence_classes()

        return self.__class__._registered_sequence_classes

    @property
    def sequence_types(self):
        return self.config.get('types', default=dict()).keys()

    @property
    def sequences(self):
        return self.__class__._sequences

    def register_sequence_class(self, sequence_class):
        """
        Registers a new sequence class into the project
        :param sequence_class: cls
        """

        if sequence_class in self.sequence_classes:
            LOGGER.warning(
                'Sequence Class: "{}" is already registered. Skipping ...'.format(sequence_class))
            return False

        self.__class__._registered_sequence_classes.append(sequence_class)

        return True

    @decorators.timestamp
    def find_all_sequences(self, force_update=False, force_login=True):
        """
        Returns a list of all sequences in the current project
        :param force_update: bool, Whether sequences cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: list(ArtellaSequence))
        """

        self._check_project()

        if self.sequences and not force_update:
            return self.sequences

        python.clear_list(self.__class__._sequences)

        if not artellapipe.Tracker().is_logged() and force_login:
            artellapipe.Tracker().login()
        if not artellapipe.Tracker().is_logged():
            LOGGER.warning(
                'Impossible to find sequences of current project because user is not log into production tracker')
            return None
        tracker = artellapipe.Tracker()
        sequences_list = tracker.all_project_sequences()
        if not sequences_list:
            LOGGER.warning('No sequences found in current project!')
            return None

        for sequence_data in sequences_list:
            new_sequence = self.create_sequence(sequence_data)
            self.__class__._sequences.append(new_sequence)

        return self.sequences

    def find_sequence(self, sequence_name=None, force_update=False):
        """
        Returns sequence of the project if found
        :param sequence_name: str, name of the sequence to find
        :param force_update: bool, Whether sequences cache updated must be forced or not
        :return: ArtellaSequence
        """

        self._check_project()

        sequences_found = list()
        all_sequences = self.find_all_sequences(force_update=force_update) or list()
        for sequence in all_sequences:
            if sequence.get_name() == sequence_name:
                sequences_found.append(sequence)

        if not sequences_found:
            return None

        if len(sequences_found) > 1:
            LOGGER.warning('Found multiple instances of Sequence "{}"'.format(sequence_name))

        return sequences_found[0]

    def get_sequence_names(self):
        """
        Returns the names of all the sequences in the current project
        :return: list(str)
        """

        self._check_project()

        all_sequences = self.find_all_sequences()
        if not all_sequences:
            return None

        return [sequence.get_name() for sequence in all_sequences]

    def create_sequence(self, sequence_data):
        """
        Returns a new sequence wit the given data
        :param sequence_data: dict
        :return:
        """

        return artellapipe.Sequence(project=artellapipe.project, sequence_data=sequence_data)

    def is_valid_sequence_type(self, sequence_type):
        """
        Returns whether or not given asset type is valid
        :param sequence_type: str
        :return: bool
        """

        return sequence_type in self.sequence_types

    def get_sequence_file(self, file_type, extension=None):
        """
        Returns sequence file object class linked to given file type for current project
        :param file_type: str
        :return: ArtellaSequenceType
        """

        self._check_project()

        if not artellapipe.FilesMgr().is_valid_file_type(file_type):
            return

        sequence_file_class_found = None
        for sequence_file_class in artellapipe.FilesMgr().file_classes:
            if sequence_file_class.FILE_TYPE == file_type:
                sequence_file_class_found = sequence_file_class
                break

        if not sequence_file_class_found:
            LOGGER.warning('No Sequence File Class found for file of type: "{}"'.format(file_type))
            return

        return sequence_file_class_found

    def get_latest_published_versions(self, sequence_path, file_type=None):
        """
        Returns all published version of the the different files of the given sequence
        :param sequence_path: str, path of the sequence
        :param file_type: str, if given only paths of the given file type will be returned (model, rig, etc)
        :return: list(dict), number of version, name of version and version path
        """

        latest_version = list()

        versions = dict()
        status = artellalib.get_status(sequence_path, as_json=True)

        status_data = status.get('data')
        if not status_data:
            LOGGER.info('Impossible to retrieve data from Artella in file: "{}"'.format(sequence_path))
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
            valid_version = self._check_valid_published_version(sequence_path, version_found)
            if not valid_version:
                current_index -= 1
        if valid_version and version_found:
            version_path = path_utils.clean_path(os.path.join(sequence_path, '__{}__'.format(version_found)))
            latest_version.append({
                'version': ordered_versions.keys()[current_index],
                'version_name': version_found,
                'version_path': version_path}
            )

        return latest_version

    def get_default_sequence_name(self):
        """
        Returns the default name used by sequences
        :return: str
        """

        return self.config.get('default_name', default='New Sequence')

    def get_default_sequence_thumb(self):
        """
        Returns the default thumb used by sequences
        :return: str
        """

        return self.config.get('default_thumb', default='default')

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

    def _register_sequence_classes(self):
        """
        Internal function that registers project sequence classes
        """

        if not hasattr(artellapipe, 'project') or not artellapipe.project:
            LOGGER.warning('Impossible to register sequence classes because Artella project is not defined!')
            return False

        for sequence_type, sequence_type_info in self.config.get('types', default={}).items():
            sequence_files = sequence_type_info.get('files', list())
            full_sequence_class = sequence_type_info.get('class', None)
            if not full_sequence_class:
                LOGGER.warning('No class defined for Sequence Type "{}". Skipping ...'.format(sequence_type))
                continue
            sequence_class_split = full_sequence_class.split('.')
            sequence_class = sequence_class_split[-1]
            sequence_module = '.'.join(sequence_class_split[:-1])
            LOGGER.info('Registering Sequence: {}'.format(sequence_module))

            try:
                module_loader = loader.find_loader(sequence_module)
            except (RuntimeError, ImportError) as exc:
                LOGGER.warning("Impossible to import Sequence Module: {} | {} | {}".format(
                    sequence_module, exc, traceback.format_exc()))
                continue

            class_found = None
            mod = importlib.import_module(module_loader.fullname)
            for cname, obj in inspect.getmembers(mod, inspect.isclass):
                if cname == sequence_class:
                    class_found = obj
                    break

            if not class_found:
                LOGGER.warning('No Sequence Class "{}" found in Module: "{}"'.format(sequence_class, sequence_module))
                continue

            obj.FILE_TYPE = sequence_type
            obj.FILES = sequence_files

            self.register_sequence_class(obj)

        return True
