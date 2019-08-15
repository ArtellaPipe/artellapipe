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

import tpDccLib as tp

import artellapipe


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

        if not os.path.isfile(self._filename):
            return None

        return self._filename

    @property
    def base_name(self):
        """
        Returns the base name of the referenced file of DCC node
        :return: str
        """

        if not os.path.isfile(self._filename):
            return None

        return os.path.basename(self._filename)

    @property
    def dir_name(self):
        """
        Returns the directory name of the refernced file of DCC node
        :return: str
        """

        if not os.path.isfile(self._filename):
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
            self._nodes_list = tp.Dcc.list_children(node=self._node, all_hierarchy=True, full_path=True, children_type='transform')
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
            artellapipe.logger.warning('Impossible to change namespace for reference node: "{0}" >> "{1}" to "{2}" --> {3}'.format(self.node, self.namespace, new_namespace, e))

        if result:
            artellapipe.logger.info('Namespace for reference node: "{0}" >> "{1}" to "{2}" changed successfully!'.format(self.node, self.namespace, new_namespace))

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
            artellapipe.logger.error('Impossible to change filename for reference node: "{0}" > "{1}" to "{2}" --> {3}'.format(self.node, self.filename, new_filename, e))

        self.update_info()

        return result

    def convert_reference_to_absolute_path(self):
        """
        Updates the current path the stored reference is pointing to from relative to absolute relative to the Artella Project path
        :return: str
        """

        fix_path = self._project.fix_path(self.filename.lower())
        if os.path.exists(fix_path):
            self.change_filename(fix_path)
        else:
            artellapipe.logger.warning('Impossible to convert "{0}" to absolute path: "{1}", because new file does not exists!'.format( self.filename, fix_path))

        self.update_info()

    def import_objects(self, with_absolute_path=False):
        """
        Import objects pointed by the stored reference node
        :param with_absolute_path: str, Whether the imported objects should be imported using a relative or an absolute path
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
            artellapipe.logger.error('Impossible to import objects from reference node: "{0}" --> {1}'.format(self.node, e))

        if result:
            artellapipe.logger.info('Imported objects from node: "{}" successfully!'.format(self.node))

        self.update_info()

        return result

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

    def get_tag_info_node(self):
        """
        Returns tag node associated to this Artella DCC node retrieved from tag info attribute
        :return: ArtellaTagDataNode
        """

        if tp.Dcc.attribute_exists(node=self.node, attribute_name='tag_info'):
            tag_info = tp.Dcc.get_attribute_value(node=self.node, attribute_name='tag_info')
            tag_node = self._project.TAG_NODE_CLASS(project=self._project, node=self.node, tag_info=tag_info)
            return tag_node


class ArtellaAssetNode(ArtellaDCCNode, object):
    def __init__(self, project, node=None, **kwargs):
        super(ArtellaAssetNode, self).__init__(project=project, node=node, update_at_init=False)

        if node is not None:
            self._name = node
        else:
            self._name = kwargs.get('name', 'New_Asset')
        self._asset_path = kwargs.get('path', -1)               # We use -1, to force the asset path update in first use
        self._category = kwargs.get('category', None)
        self._description = kwargs.get('description', '')

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
        if self._asset_path == -1:
            self._asset_path = self._get_asset_path()

        return self._asset_path

    def get_short_name(self, clean=False):
        """
        Returns the short name of the DCC node
        :param clean: bool
        :return: str
        """

        return tp.Dcc.node_short_name(self._name).rstrip(string.digits) if clean else self._name

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
