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
