#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager for Artella assets
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

from tpPyUtils import python, decorators, path as path_utils

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe.register
from artellapipe.utils import exceptions
from artellapipe.core import config
from artellapipe.libs import artella as artella_lib
from artellapipe.libs.artella.core import artellalib, artellaclasses

LOGGER = logging.getLogger()


class ArtellaAssetsManager(object):
    def __init__(self):
        self._project = None

        self._assets = list()
        self._config = None
        self._registered_asset_classes = list()

    @property
    def config(self):
        return self._config

    @property
    def asset_classes(self):
        return self._registered_asset_classes

    @property
    def asset_types(self):
        return self._config.get('types', default=dict()).keys()

    @property
    def assets(self):
        return self._assets

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project
        self._config = config.get_config(project, 'artellapipe-assets')

        self._register_asset_classes()

    def register_asset_class(self, asset_class):
        """
        Registers a new asset class into the project
        :param asset_class: cls
        """

        if asset_class in self._registered_asset_classes:
            LOGGER.warning(
                'Asset Class: "{}" is already registered. Skipping ...'.format(asset_class))
            return False

        self._registered_asset_classes.append(asset_class)
        return True

    def get_asset_types(self):
        """
        Returns a list with all available asset types
        :return: list(str)
        """

        asset_types = self._config.get('types', default={})
        return asset_types.keys()

    def get_asset_type_files(self, asset_type):
        """
        Returns a list with all files available for a specific asset type
        :param asset_type: str
        :return: list(str)
        """

        asset_types = self._config.get('types', default={})
        if asset_type not in asset_types:
            return list()

        return asset_types.get(asset_type, {}).get('files', list())

    def get_default_asset_name(self):
        """
        Returns the default name used by assets
        :return: str
        """

        return self.config.get('default_name', default='New Asset')

    def get_assets_by_type(self, asset_type):

        if not self.is_valid_asset_type(asset_type):
            return None

        return [asset for asset in self.assets if asset.ASSET_TYPE == asset_type]

    def get_assets_path(self):
        """
        Returns path where project assets are located
        :return: str
        """

        self._check_project()

        assets_folder_name = artella_lib.config.get('server', 'assets_folder_name')
        assets_path = os.path.join(self._project.get_path(), assets_folder_name)

        return assets_path

    def is_valid_assets_path(self):
        """
        Returns whether current asset path exists or not
        :return: bool
        """

        assets_path = self.get_assets_path()
        if not assets_path or not os.path.exists(assets_path):
            return False

        return True

    def find_all_assets(self, force=False):
        """
        Returns a list of all assets in the project
        :param force: bool, Whether assets cache updated must be forced or not
        :return: variant, ArtellaAsset or list(ArtellaAsset)
        """

        self._check_project()

        assets_path = self.get_assets_path()
        if not self.is_valid_assets_path():
            LOGGER.warning('Impossible to retrieve assets from invalid path: {}'.format(assets_path))
            return

        if self._assets and not force:
            return self._assets
        else:
            python.clear_list(self._assets)
            tracker = artellapipe.Tracker()
            assets_dict = tracker.all_project_assets()
            if not assets_dict:
                LOGGER.warning("No assets found in current project!")
                return None
            for asset_data in assets_dict:
                new_asset = self.create_asset(asset_data)
                self._assets.append(new_asset)

            return self._assets

    def find_asset(self, asset_name=None, asset_path=None, allow_multiple_instances=False, force=False):
        """
        Returns asset of the project if found
        :param asset_name: str, name of the asset to find
        :param asset_path: str, path where asset is located in disk
        :param allow_multiple_instances: bool, whether to return None if multiple instances of an asset is found;
        otherwise first asset in the list will be return
        :param force: bool, Whether assets cache updated must be forced or not
        :return: Asset or None
        """

        self._check_project()

        assets_found = list()
        all_assets = self.find_all_assets(force=force)
        for asset in all_assets:
            if asset.get_name() == asset_name:
                assets_found.append(asset)

        if len(assets_found) > 1:
            LOGGER.warning('Found Multiple instances of Asset "{} | {}"'.format(asset_name, asset_path))
            if not allow_multiple_instances:
                return assets_found[0]
            else:
                return assets_found

        return assets_found[0]

    def create_asset(self, asset_data):
        """
        Returns a new asset with the given data
        :param asset_data: dict
        """

        category = asset_data.get('category', None)

        if not category:
            return artellapipe.Asset(project=self, asset_data=asset_data)
        else:
            asset_classes = self.asset_classes
            for asset_class in asset_classes:
                if asset_class.ASSET_TYPE == category:
                    return asset_class(project=self._project, asset_data=asset_data)

    def create_asset_in_artella(self, asset_name, asset_path, folders_to_create=None):
        """
        Creates a new asset in Artella
        :param asset_name: str
        :param asset_path: str
        :param folders_to_create: list(str) or None
        """

        valid_create = artellalib.create_asset(asset_name, asset_path)
        if not valid_create:
            LOGGER.warning('Impossible to create Asset {} in Path: {}!'.format(asset_name, asset_path))
            return

        working_folder = artella_lib.config.get('server', 'working_folder')

        if folders_to_create:
            for folder_name in folders_to_create:
                file_path = path_utils.clean_path(os.path.join(asset_path, asset_name, working_folder))
                artellalib.new_folder(file_path, folder_name)

        return True

    def is_valid_asset_type(self, asset_type):
        """
        Returns whether or not given asset type is valid
        :param asset_type: str
        :return: bool
        """

        return asset_type in self.asset_types

    def is_valid_asset_file_type(self, file_type):
        """
        Returns whether the current file type is valid or not for current project
        :param file_type: str
        :return: bool
        """

        return file_type in artellapipe.FilesMgr().files

    def get_asset_file(self, file_type, extension=None):
        """
        Returns asset file object class linked to given file type for current project
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        self._check_project()

        if not self.is_valid_asset_file_type(file_type):
            return

        asset_file_class_found = None
        for asset_file_class in artellapipe.FilesMgr().file_classes:
            if asset_file_class.FILE_TYPE == file_type:
                asset_file_class_found = asset_file_class
                break

        if not asset_file_class_found:
            LOGGER.warning('No Asset File Class found for file of type: "{}"'.format(file_type))
            return

        return asset_file_class_found

    def get_asset_data_file_path(self, asset_path):
        """
        Returns asset data file path of given asset
        :param asset_path: str
        :return: str
        """

        filename_attr = self._config.get('data', 'filename')
        working_folder = artella_lib.config.get('server', 'working_folder')
        return os.path.join(asset_path, working_folder, filename_attr)

    def get_latest_published_versions(self, asset_path, file_type=None):
        """
        Returns all published version of the the different files of the given asset
        file is synchronized
        :param asset_path: str, path of the asset
        :param file_type: str, if given only paths of the given file type will be returned (model, rig, etc)
        :return: list(dict), number of version, name of version and version path
        """

        latest_version = list()

        versions = dict()
        status = artellalib.get_status(asset_path, as_json=True)

        status_data = status.get('data')
        if not status_data:
            LOGGER.error('Impossible to retrieve data from Artella in file: "{}"'.format(asset_path))
            return

        for name, data in status_data.items():
            if name in ['latest', '_latest']:
                continue
            if file_type and file_type not in name:
                continue
            version = artellalib.split_version(name)[1]
            versions[version] = name

        ordered_versions = OrderedDict(sorted(versions.items()))

        current_index = -1
        valid_version = False
        version_found = None
        while not valid_version and current_index >= (len(ordered_versions) * -1):
            version_found = ordered_versions[ordered_versions.keys()[current_index]]
            valid_version = self._check_valid_published_version(asset_path, version_found)
            if not valid_version:
                current_index -= 1
        if valid_version and version_found:
            version_path = path_utils.clean_path(os.path.join(asset_path, '__{}__'.format(version_found)))
            latest_version.append({
                'version': ordered_versions.keys()[current_index],
                'version_name': version_found,
                'version_path': version_path}
            )

        return latest_version

    def _check_project(self):
        """
        Internal function that checks whether or not assets manager has a project set. If not an exception is raised
        """

        if not self._project:
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

    def _register_asset_classes(self):
        """
        Internal function that project asset classes
        """

        if not self._project:
            LOGGER.warning('Impossible to register asset classes because Artella project is not defined!')
            return False

        for asset_type, asset_type_info in self._config.get('types', default={}).items():
            asset_files = asset_type_info.get('files', list())
            full_asset_class = asset_type_info.get('class', None)
            if not full_asset_class:
                LOGGER.warning('No class defined for Asset Type "{}". Skipping ...'.format(asset_type))
                continue
            asset_class_split = full_asset_class.split('.')
            asset_class = asset_class_split[-1]
            asset_module = '.'.join(asset_class_split[:-1])
            LOGGER.info("Registering Asset: {}".format(asset_module))

            try:
                module_loader = loader.find_loader(asset_module)
            except (RuntimeError, ImportError) as exc:
                LOGGER.warning("Impossible to import Asset Module: {} | {} | {}".format(
                    asset_module, exc, traceback.format_exc()))
                continue

            class_found = None
            mod = importlib.import_module(module_loader.fullname)
            for cname, obj in inspect.getmembers(mod, inspect.isclass):
                if cname == asset_class:
                    class_found = obj
                    break

            if not class_found:
                LOGGER.warning('No Asset Class "{}" found in Module: "{}"'.format(asset_class, asset_module))
                continue

            obj.ASSET_TYPE = asset_type
            obj.ASSET_FILES = asset_files

            self.register_asset_class(obj)

        return True


@decorators.Singleton
class ArtellaAssetsManagerSingleton(ArtellaAssetsManager, object):
    def __init__(self):
        ArtellaAssetsManager.__init__(self)


artellapipe.register.register_class('AssetsMgr', ArtellaAssetsManagerSingleton)
