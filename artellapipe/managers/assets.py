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

import tpDcc as tp
from tpDcc.libs.python import python, decorators, strings, path as path_utils

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe
from artellapipe.utils import exceptions
from artellapipe.core import defines
from artellapipe.libs.artella.core import artellalib, artellaclasses

LOGGER = logging.getLogger('artellapipe')


class AssetsManager(object):

    _assets = list()
    _config = None
    _registered_asset_classes = list()

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tp.ConfigsMgr().get_config(
                config_name='artellapipe-assets',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    @property
    def asset_classes(self):
        if not self.__class__._registered_asset_classes:
            self._register_asset_classes()

        return self.__class__._registered_asset_classes

    @property
    def asset_types(self):
        return self.config.get('types', default=dict()).keys()

    @property
    def assets(self):
        return self.__class__._assets

    @property
    def must_file_types(self):
        return self.config.get('must_file_types', default=list())

    def register_asset_class(self, asset_class):
        """
        Registers a new asset class into the project
        :param asset_class: cls
        """

        if asset_class in self.__class__._registered_asset_classes:
            LOGGER.warning(
                'Asset Class: "{}" is already registered. Skipping ...'.format(asset_class))
            return False

        self.__class__._registered_asset_classes.append(asset_class)
        return True

    def get_asset_categories(self):
        """
        Returns all asset categories of current project
        :return: list(str)
        """

        return self.config.get('types', default=list())

    def get_asset_id_from_node(self, node):
        """
        Returns asset name of the given node
        :param node: str
        :return: str
        """

        node_name = tp.Dcc.node_short_name(node)
        namespace = tp.Dcc.node_namespace(node=node_name, check_node=False)
        if not namespace:
            # LOGGER.warning('Was not possible to find asset name from "{}"'.format(node))
            return False

        if namespace.startswith(':'):
            namespace = namespace[1:]

        return namespace

    def get_asset_from_node(self, node):
        """
        Returns Asset from given node
        :param node: str
        :return: ArtellaAsset
        """

        asset_name = self.get_asset_id_from_node(node=node)
        if not asset_name:
            return None

        asset = self.find_asset(asset_name=asset_name)
        if not asset:
            LOGGER.warning('No asset found for node: {} | {}'.format(node, asset_name))
            return None

        return asset

    def get_asset_types(self):
        """
        Returns a list with all available asset types
        :return: list(str)
        """

        asset_types = self.config.get('types', default={})
        return asset_types.keys()

    def get_asset_type_files(self, asset_type):
        """
        Returns a list with all files available for a specific asset type
        :param asset_type: str
        :return: list(str)
        """

        asset_types = self.config.get('types', default={})
        if asset_type not in asset_types:
            return list()

        return asset_types.get(asset_type, {}).get('files', list())

    def get_default_asset_name(self):
        """
        Returns the default name used by assets
        :return: str
        """

        return self.config.get('default_name', default='New Asset')

    def get_shading_file_type(self):
        """
        Returns shading file type used by shaders
        :return: str
        """

        return self.config.get('shading_file_type', default='shading')

    def get_shaders_mapping_file_type(self):
        """
        Returns shader mapping file type
        :return: str
        """

        return self.config.get('shaders_mapping_file_type', default='shadersmapping')

    def get_default_asset_thumb(self):
        """
        Returns the default thumb used by assets
        :return: str
        """

        return self.config.get('default_thumb', default='default')

    def get_assets_by_type(self, asset_type):
        """
        Returns asset by its type
        :param asset_type: str
        :return: ArtellaAsset
        """

        if not self.is_valid_asset_type(asset_type):
            return None

        return [asset for asset in self.assets if asset and asset.FILE_TYPE == asset_type]

    def open_asset_shaders_file(self, asset):
        """
        Open asset shaders file of the given asset
        :param asset:
        """

        shading_file_type = self.get_shading_file_type()
        file_path = asset.get_file(
            file_type=shading_file_type, status=defines.ArtellaFileStatus.WORKING, fix_path=True)
        valid_open = asset.open_file(file_type=shading_file_type, status=defines.ArtellaFileStatus.WORKING)
        if not valid_open:
            LOGGER.warning('Impossible to open Asset Shading File: {}'.format(file_path))
            return None

    def get_assets_path(self):
        """
        Returns path where project assets are located
        :return: str
        """

        self._check_project()

        assets_folder = artellapipe.project.config.get('assets_folder')
        assets_path = os.path.join(artellapipe.project.get_path(), assets_folder)

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

    def find_all_assets(self, force_update=False, force_login=True):
        """
        Returns a list of all assets in the project
        :param force_update: bool, Whether assets cache updated must be forced or not
        :param force_login: bool, Whether logging to production tracker is forced or not
        :return: variant, ArtellaAsset or list(ArtellaAsset)
        """

        self._check_project()

        if self.__class__._assets and not force_update:
            return self.__class__._assets

        python.clear_list(self.__class__._assets)

        if not artellapipe.Tracker().is_logged() and force_login:
            artellapipe.Tracker().login()
        if not artellapipe.Tracker().is_logged():
            LOGGER.warning(
                'Impossible to find assets of current project because user is not log into production tracker')
            return None
        tracker = artellapipe.Tracker()
        assets_list = tracker.all_project_assets()
        if not assets_list:
            LOGGER.warning("No assets found in current project!")
            return None
        for asset_data in assets_list:
            new_asset = self.create_asset(asset_data)
            if not new_asset:
                continue
            self.__class__._assets.append(new_asset)

        return self.__class__._assets

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
        all_assets = self.find_all_assets(force_update=force) or list()
        for asset in all_assets:
            if asset.get_name() == asset_name:
                assets_found.append(asset)

        if not assets_found:
            return None

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
                if asset_class.FILE_TYPE == category:
                    return asset_class(project=artellapipe.project, asset_data=asset_data)

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

        working_folder = artellapipe.project.get_working_folder()

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

    def get_asset_thumbnail_path(self, asset_name, create_folder=True):
        """
        Returns path where asset thumbnail is or should be located
        If the folder does not exists, the folder will be created
        :param create_folder: bool
        :return: str
        """

        self._check_project()

        data_path = artellapipe.project.get_data_path()
        thumbnails_cache_folder = os.path.join(data_path, 'asset_thumbs_cache')
        if not os.path.isdir(thumbnails_cache_folder) and create_folder:
            os.makedirs(thumbnails_cache_folder)

        return os.path.join(thumbnails_cache_folder, asset_name + '.png')

    def get_asset_data_file_path(self, asset_path):
        """
        Returns asset data file path of given asset
        :param asset_path: str
        :return: str
        """

        filename_attr = self.config.get('data', 'filename')
        working_folder = artellapipe.project.get_working_folder()
        return os.path.join(asset_path, working_folder, filename_attr)

    def get_latest_published_versions(self, asset_path, file_type=None):
        """
        Returns all published version of the the different files of the given asset
        file is synchronized
        :param asset_path: str, path of the asset
        :param file_type: str, if given only paths of the given file type will be returned (model, rig, etc)
        :return: list(dict), number of version, name of version and version path
        """

        self._check_project()

        if artellapipe.project.is_enterprise():
            return self._get_latest_published_versions_enterprise(asset_path, file_type=file_type)
        else:
            return self._get_latest_published_versions_indie(asset_path, file_type=file_type)

    @decorators.timestamp
    def get_scene_assets(self, as_nodes=True, allowed_types=None, allowed_tags=None, node_id=None):
        """
        Returns a list with all assets in the current scene
        :param as_nodes: bool, Whether to return found assets as ArtellaAssetNodes or as strings (asset names)
        :param allowed_types: list(str), List of types asset to filter by. If None, no filter is done
        :param allowed_tags: list(str), List of asset tags to filter by. If None, no filter is done
        :return: list(str) or list(ArtellaAssetNode)
        """

        if not allowed_types:
            allowed_types = list()

        if not allowed_tags:
            allowed_tags = list()

        scene_assets = list()

        all_assets = self.find_all_assets() or list()
        all_ids = dict()
        for asset in all_assets:
            all_ids[asset.get_id()] = asset

        if not allowed_types and not allowed_tags:
            valid_assets = all_assets
        else:
            valid_assets = list()
            for asset in all_assets:
                asset_category = asset.get_category()
                asset_tags = asset.get_tags() or list()
                if asset.FILE_TYPE in allowed_types or asset_category in allowed_types \
                        or asset.FILE_TYPE in allowed_tags:
                    valid_assets.append(asset)
                    continue
                for tag in asset_tags:
                    if tag in allowed_tags:
                        valid_assets.append(asset)
                        break

        if not valid_assets:
            LOGGER.warning('No valid assets found in current scene!')
            return

        all_namespaces = tp.Dcc.list_namespaces()
        for namespace in all_namespaces:
            clean_namespace = namespace[1:] if namespace.startswith(':') else namespace
            clean_namespace = strings.remove_digits_from_end_of_string(clean_namespace)
            if clean_namespace not in all_ids:
                continue
            if node_id and namespace != node_id:
                continue

            namespace_nodes = tp.Dcc.all_nodes_in_namespace(namespace)
            if not namespace_nodes:
                LOGGER.warning('Namespace "{}" is empty!'.format(namespace_nodes))
                continue
            for namespace_node in namespace_nodes:
                split_name = '|{}'.format(namespace)
                if split_name not in namespace_node:
                    continue
                split = namespace_node.split('|{}:'.format(namespace))
                root_node = strings.lstrips(namespace_node, '{}'.format(split[0])).split('|')[1]
                asset_node = all_ids[clean_namespace]
                if as_nodes:
                    asset_node = artellapipe.AssetNode(
                        project=artellapipe.project, node=root_node, asset=asset_node, id=namespace
                    )
                else:
                    asset_node = root_node
                if node_id and asset_node:
                    return asset_node

                scene_assets.append(asset_node)

                break

        return scene_assets

    def get_asset_node_in_scene(self, node_id):
        """
        Returns given node wrapped in AssetNode (if exists)
        :param node_id: str
        :return: ArtellaAssetNode
        """

        self._check_project()

        ns = self.get_asset_id_from_node(node_id)
        if ns:
            node_id = ns
        if not node_id:
            return None

        asset_node = self.get_scene_assets(node_id=node_id)

        return asset_node

    def get_assets_in_shot(self, shot, force_login=True):
        """
        Returns all the assets contained in given shot breakdown defined in production tracker
        :param shot:
        :return:
        """

        if not artellapipe.Tracker().is_logged() and force_login:
            artellapipe.Tracker().login()
        if not artellapipe.Tracker().is_logged():
            LOGGER.warning(
                'Impossible to find assets of current project because user is not log into production tracker')
            return None
        tracker = artellapipe.Tracker()
        assets_in_shots = tracker.all_assets_in_shot(shot)
        if not assets_in_shots:
            LOGGER.warning('No assets found in shot breakdown')
            return None

        found_assets = list()
        for asset_data in assets_in_shots:
            new_asset = self.create_asset(asset_data)
            found_assets.append(new_asset)

        return found_assets

    def get_asset_renderable_shapes(self, asset, remove_namespace=False, full_path=True):
        """
        Returns a list with all renderable shapes of the given asset
        :param remove_namespace: bool
        :return: list(str)
        """

        renderable_shapes = list()

        node_name = asset.get_name()
        if not tp.Dcc.object_exists(node_name):
            LOGGER.warning(
                'Impossible to get renderable shapes because node {} does not exists in current scene!'.format(
                    node_name))
            return renderable_shapes

        transform_relatives = tp.Dcc.list_relatives(
            node=node_name, all_hierarchy=True, full_path=full_path, relative_type='transform',
            shapes=False, intermediate_shapes=False)

        for obj in transform_relatives:
            if not tp.Dcc.object_exists(obj):
                continue
            shapes = tp.Dcc.list_shapes(node=obj, full_path=full_path, intermediate_shapes=False)
            if not shapes:
                continue
            renderable_shapes.extend(shapes)

        if remove_namespace:
            renderable_shapes = [tp.Dcc.node_name_without_namespace(shape) for shape in renderable_shapes]

        return list(set(renderable_shapes))

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

    def _register_asset_classes(self):
        """
        Internal function that  registers project asset classes
        """

        if not hasattr(artellapipe, 'project') or not artellapipe.project:
            LOGGER.warning('Impossible to register asset classes because Artella project is not defined!')
            return False

        for asset_type, asset_type_info in self.config.get('types', default={}).items():
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

            obj.FILE_TYPE = asset_type
            obj.FILES = asset_files

            self.register_asset_class(obj)

        return True

    def _get_latest_published_versions_enterprise(self, asset_path, file_type=None):
        """
        Internal function that implements get_latest_published_versions for Artella Indie
        """

        latest_version = list()

        return latest_version

    def _get_latest_published_versions_indie(self, asset_path, file_type=None):
        """
        Internal function that implements get_latest_published_versions for Artella Indie
        """

        latest_version = list()

        versions = dict()
        status = artellalib.get_status(asset_path, as_json=True)

        status_data = status.get('data')
        if not status_data:
            LOGGER.info('Impossible to retrieve data from Artella in file: "{}"'.format(asset_path))
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
