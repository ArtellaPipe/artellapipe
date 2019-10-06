#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions for DCC nodes in Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import string
import inspect
import logging

import tpDccLib as tp

from artellapipe.core import defines

LOGGER = logging.getLogger()


class ArtellaDCCNode(object):
    def __init__(self, project, node=None, update_at_init=True):
        super(ArtellaDCCNode, self).__init__()

        self._project = project
        self._node = node
        self._exists = False
        self._valid = False
        self._loaded = False
        self._filename = None
        self._filename_with_copy_number = None
        self._namespace = None
        self._parent_namespace = None
        self._nodes_list = list()

        if update_at_init:
            self.update_info()

    @property
    def node(self):
        """
        Returns DCC node
        :return: str
        """

        return self._node

    @property
    def project(self):
        """
        Returns project attached to this node
        :return: ArtellaProject
        """

        return self._project

    @property
    def exists(self):
        """
        Returns whether current DCC node exists in DCC scene or not
        :return: bool
        """

        return self._exists

    @property
    def is_valid(self):
        """
        Returns whether DCC node is valid or not
        :return: bool
        """

        return self._valid

    @property
    def is_loaded(self):
        """
        Returns whether DCC node exists is loaded or not
        :return: bool
        """

        return self._loaded

    @property
    def filename(self):
        """
        Returns filename of the referenced file of DCC node
        :return: str
        """

        if not self._filename or not not os.path.isfile(self._filename):
            return None

        return self._filename

    @property
    def base_name(self):
        """
        Returns the base name of the referenced file of DCC node
        :return: str
        """

        if not self._filename or not os.path.isfile(self._filename):
            return None

        return os.path.basename(self._filename)

    @property
    def dir_name(self):
        """
        Returns the directory name of the refernced file of DCC node
        :return: str
        """

        if not self._filename or not os.path.isfile(self._filename):
            return None

        return os.path.dirname(self._filename)

    @property
    def namespace(self):
        """
        Returns namespace of the DCC node
        :return: str
        """

        return self._namespace

    @property
    def parent_namespace(self):
        """
        Returns the parent namespace of the DCC node
        :return: str
        """

        return self._parent_namespace

    @property
    def nodes_list(self):
        """
        Returns all children nodes of the DCC node
        :return: str
        """

        return self._nodes_list

    def update_info(self):
        """
        Updates the info of the current DCC node
        """

        if not self._node:
            return False

        self._exists = tp.Dcc.object_exists(self._node)
        if not self._exists:
            return False

        is_referenced = tp.Dcc.node_is_referenced(self._node)
        if not is_referenced:
            self._nodes_list = tp.Dcc.list_children(
                node=self._node, all_hierarchy=True, full_path=True, children_type='transform')
        else:
            self._loaded = tp.Dcc.node_is_loaded(self._node)
            if self._loaded:
                try:
                    self._filename = tp.Dcc.node_filename(self._node, no_copy_number=True)
                    self._valid = True
                except Exception as e:
                    self._valid = False
            self._namespace = tp.Dcc.node_namespace(self._node)
            self._parent_namespace = tp.Dcc.node_parent_namespace(self._node)
            if self._valid:
                self._filename_with_copy_number = tp.Dcc.node_filename(self._node, no_copy_number=False)
                self._nodes_list = tp.Dcc.node_nodes(self._node)

    def change_namespace(self, new_namespace):
        """
        Updates the namespace of the reference stored node
        :param new_namespace: str
        :return: str
        """

        result = None
        try:
            result = tp.Dcc.change_namespace(self.namespace, new_namespace)
        except Exception as e:
            LOGGER.warning(
                'Impossible to change namespace for reference node: "{0}" >> "{1}" to "{2}" --> {3}'.format(
                    self.node, self.namespace, new_namespace, e))

        if result:
            LOGGER.info(
                'Namespace for reference node: "{0}" >> "{1}" to "{2}" changed successfully!'.format(
                    self.node, self.namespace, new_namespace))

        self.update_info()

        return result

    def change_filename(self, new_filename):
        """
        Updates the filename that the current stored reference node is pointing to
        :param new_filename: str
        :return: str
        """

        result = None
        try:
            result = tp.Dcc.change_filename(node=self.node, new_filename=new_filename)
        except Exception as e:
            LOGGER.error(
                'Impossible to change filename for reference node: "{0}" > "{1}" to "{2}" --> {3}'.format(
                    self.node, self.filename, new_filename, e))

        self.update_info()

        return result

    def convert_reference_to_absolute_path(self):
        """
        Updates the current path the stored reference is pointing to from relative to absolute relative to
        the Artella Project path
        :return: str
        """

        fix_path = self._project.fix_path(self.filename.lower())
        if os.path.exists(fix_path):
            self.change_filename(fix_path)
        else:
            LOGGER.warning(
                'Impossible to convert "{0}" to absolute path: "{1}", because new file does not exists!'.format(
                    self.filename, fix_path))

        self.update_info()

    def import_objects(self, with_absolute_path=False):
        """
        Import objects pointed by the stored reference node
        :param with_absolute_path: str, Whether the imported objects should be imported using
        a relative or an absolute path
        :return: str
        """

        result = None

        try:
            if with_absolute_path:
                fix_path = self._project.fix_path(self.filename.lower())
                if os.path.exists(fix_path):
                    self.change_filename(fix_path)

            result = tp.Dcc.import_reference(self.filename)
        except Exception as e:
            LOGGER.error(
                'Impossible to import objects from reference node: "{0}" --> {1}'.format(self.node, e))

        if result:
            LOGGER.info('Imported objects from node: "{}" successfully!'.format(self.node))

        self.update_info()

        return result

    def remove(self):

        if tp.Dcc.node_is_referenced(node=self._node):
            tp.Dcc.node_unreference(self._node)
        else:
            referenced_nodes = list()
            non_referenced_nodes = list()
            for n in self.nodes_list:
                if not tp.Dcc.object_exists(n):
                    LOGGER.warning('Impossible to remove child node: {}!'.format(n))
                    continue
                if tp.Dcc.node_is_referenced(n):
                    referenced_nodes.append(n)
                else:
                    non_referenced_nodes.append(n)
            non_referenced_nodes.append(self._node)

            for ref_node in referenced_nodes:
                if not tp.Dcc.object_exists(ref_node):
                    continue
                tp.Dcc.node_unreference(ref_node)

            for non_ref_node in non_referenced_nodes:
                if not tp.Dcc.object_exists(non_ref_node):
                    continue
                tp.Dcc.delete_object(non_ref_node)

        return True

    def get_tag_node(self):
        """
        Returns tag node associated to this Artella DCC node
        :return: ArtellaTagNode
        """

        if tp.Dcc.attribute_exists(node=self.node, attribute_name='tag_data'):
            tag_data_node = tp.Dcc.list_connections(node=self.node, attribute_name='tag_data')
            if tag_data_node:
                tag_data_node = tag_data_node[0]
                tag_type = tp.Dcc.get_attribute_value(node=tag_data_node, attribute_name='tag_type')
                if tag_type and tag_type == '{}_TAG'.format(self._project.name.upper()):
                    tag_node = self._project.TAG_NODE_CLASS(project=self._project, node=tag_data_node)
                    return tag_node
        elif tp.Dcc.attribute_exists(node=self.node, attribute_name='tag_info'):
            tag_info = tp.Dcc.get_attribute_value(node=self.node, attribute_name='tag_info')
            tag_node = self._project.TAG_NODE_CLASS(project=self._project, node=self.node, tag_info=tag_info)
            return tag_node

    # def load_shaders(self):
    #     """
    #     Loads all the shaders of current asset node
    #     """
    #
    #     tag_node = self.get_tag_node()
    #     if tag_node:
    #         shader.load_scene_shaders(project=self._project, tag_nodes=[tag_node])
    #     else:
    #         artellapipe.logger.warning('Impossible to load shaders on asset: {}'.format(self.base_name))
    #
    # def unload_shaders(self):
    #     """
    #     Unloads all the shaders of current asset node
    #     """
    #
    #     tag_node = self.get_tag_node()
    #     if tag_node:
    #         shader.unload_shaders(project=self._project, tag_nodes=[tag_node])
    #     else:
    #         artellapipe.logger.warning('Impossible to unload shaders on asset: {}'.format(self.base_name))

    def has_overrides(self):
        """
        Returns whether current node has overrides or not
        :return: bool
        """

        user_attrs = tp.Dcc.list_user_attributes(self._node)
        if not user_attrs:
            return False

        for user_attr in user_attrs:
            if user_attr.startswith('{}'.format(defines.ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_PREFX)):
                return True

        return False

    def get_overrides(self):
        """
        Returns overrides of the current asset node
        :return: list
        """

        try:
            from artellapipe.tools.shotmanager.apps import shotassembler
        except ImportError:
            LOGGER.warning('Impossible to get overrides because Shot Assembler Tools is not available!')
            return

        if not self.has_overrides():
            return None

        overrides = list()

        user_attrs = tp.Dcc.list_user_attributes(self._node)
        if not user_attrs:
            return None

        registered_overrides = shotassembler.ShotAssembler.registered_overrides()
        for user_attr in user_attrs:
            if user_attr.startswith(defines.ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_PREFX):
                override_name = user_attr.split(defines.ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_SEPARATOR)
                if not override_name:
                    continue
                override_name = override_name[-1]
                if override_name in registered_overrides:
                    override_class = registered_overrides[override_name]
                    overrides.append(override_class(project=self._project, asset_node=self))

        return overrides

    def has_override(self, override):
        """
        Returns current asset node already ahs given override or not
        :param override: ArtellaBaseOverride
        :return: bool
        """

        overrides = self.get_overrides()
        if not overrides:
            return False

        for ov in overrides:
            if ov.OVERRIDE_NAME == override.OVERRIDE_NAME:
                return True

        return False

    def add_override(self, override_class=None):
        """
        Adds a new override to current asset node
        :param override_class: cls
        """

        if not override_class:
            LOGGER.warning(
                'Override creation tool is not working yet. Use Outliner to add overrides for now.')
            return

        new_override = override_class(project=self._project, asset_node=self)
        override_added = new_override.add_to_node()
        if not override_added:
            return None

        return new_override

    def remove_override(self, override_to_remove):
        """
        Removes given override from current asset node
        :param override_to_remove: variant, cls or ArtellaBaseOverride
        """

        if not override_to_remove:
            LOGGER.warning('No override to remove given!')
            return

        if inspect.isclass(override_to_remove):
            override_to_remove = override_to_remove(project=self._project, asset_node=self)

        override_removed = override_to_remove.remove_from_node()
        if override_removed:
            return override_to_remove

        return False

    def save_override(self, override_to_save, save_path=None):
        """
        Exports given override to disk
        :param override_to_save: variant, cls or ArtellaBaseOverride
        :param save_path: str
        """

        if not override_to_save:
            LOGGER.warning('No Override to save!')
            return

        override_to_save.save(save_path=save_path)

    def save_all_overrides(self, save_path=None):
        """
        Stores all overrides to disk
        :param save_path: str
        :return:
        """

        print('Saving all overrides ...')


class ArtellaAssetNode(ArtellaDCCNode, object):
    def __init__(self, project, node=None, **kwargs):
        super(ArtellaAssetNode, self).__init__(project=project, node=node, update_at_init=False)

        if node is not None:
            self._name = node
        else:
            self._name = kwargs.get('name', 'New_Asset')
        self._asset_path = kwargs.get('path', '')             # We use -1, to force the asset path update in first use
        self._category = kwargs.get('category', None)
        self._description = kwargs.get('description', '')
        self._asset = None

        self._current_version = None
        self._latest_version = None
        self._version_folder = dict()

        self.update_info()

    @property
    def name(self):
        """
        Returns the name of the asset
        :return: str
        """

        return self._name

    @property
    def asset_path(self):
        """
        Returns asset path
        :return: str
        """

        # Asset path retrieval is an expensive operation, so we only update it if necessary
        if self._asset_path == '':
            self._asset_path = self._get_asset_path()

        return self._asset_path

    @property
    def asset(self):
        """
        Returns asset linked to this node
        :return: ArtellaAsset
        """

        # NOTE: We must access asset path property through the property getter to make sure that
        # file path is updated
        if not self._asset:
            self._asset = self._project.find_asset(asset_path=self.asset_path, allow_multiple_instances=False)

        return self._asset

    def get_short_name(self, clean=False):
        """
        Returns the short name of the DCC node
        :param clean: bool
        :return: str
        """

        return tp.Dcc.node_short_name(self._name).rstrip(string.digits) if clean else tp.Dcc.node_short_name(self._name)

    def _get_asset_path(self):
        """
        Internal function that returns the asset path of the current node
        :return: str
        """

        assets_path = self._project.get_assets_path()
        if assets_path is None or not os.path.exists(assets_path):
            raise RuntimeError('Assets Path is not valid: {}'.format(assets_path))

        for root, dirs, files in os.walk(assets_path):
            asset_path = root
            asset_name = os.path.basename(root)
            if asset_name == self.get_short_name():
                return os.path.normpath(asset_path)

            clean_name = self.get_short_name(clean=True)
            if asset_name == clean_name:
                return os.path.normpath(asset_path)
