#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager that handles Artella Project DCC tags
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDcc as tp

import artellapipe


class TagsManager(object):

    _config = None

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tp.ConfigsMgr().get_config(
                config_name='artellapipe-tags',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    # Basic definitions for tag attributes
    class TagDefinitions(object):
        SCENE_SELECTION_NAME = 'scene'
        TAG_TYPE_ATTRIBUTE_NAME = 'tag_type'
        TAG_DATA_ATTRIBUTE_NAME = 'tag_data'
        TAG_INFO_ATTRIBUTE_NAME = 'tag_info'
        NODE_ATTRIBUTE_NAME = 'node'
        TAG_DATA_NODE_NAME = 'tag_data'
        TAG_DATA_SCENE_NAME = 'tag_data_scene'

    def get_tag_types(self):
        """
        Returns list of tags types available in current project
        :return: list(str)
        """

        tag_types = self.config.get('types') or list()
        return tag_types

    def get_tag_node(self, project, node):
        """
        Returns tag node associated to this Artella DCC node
        :return: ArtellaTagNode
        """

        if tp.Dcc.attribute_exists(node=node, attribute_name='tag_data'):
            tag_data_node = tp.Dcc.list_connections(node=node, attribute_name='tag_data')
            if tag_data_node:
                tag_data_node = tag_data_node[0]
                tag_type = tp.Dcc.get_attribute_value(node=tag_data_node, attribute_name='tag_type')
                if tag_type and tag_type == '{}_TAG'.format(project.name.upper()):
                    tag_node = artellapipe.TagNode(project=project, node=tag_data_node)
                    return tag_node
        elif tp.Dcc.attribute_exists(node=node, attribute_name='tag_info'):
            tag_info = tp.Dcc.get_attribute_value(node=node, attribute_name='tag_info')
            tag_node = artellapipe.TagNode(project=project, node=node, tag_info=tag_info)
            return tag_node

    def get_current_selection(self):
        """
        Returns current selected node
        :return: str
        """

        selected_nodes = tp.Dcc.selected_nodes()
        if selected_nodes:
            return selected_nodes[0]
        else:
            return 'scene'

    def get_tag_data_node_from_current_selection(self, new_selection=None):
        """
        Returns the tag data node associated to the current selected Maya object
        :return: variant, None || str
        """

        current_selection = self.get_current_selection()

        if new_selection:
            if tp.Dcc.object_exists(new_selection):
                current_selection = new_selection

        if current_selection == 'scene':
            try:
                tag_data_node = tp.Dcc.list_nodes(node_name='tag_data_scene')[0]
            except Exception:
                return None
        else:
            try:
                tag_data_node = tp.Dcc.list_connections(node=current_selection, attribute_name='tag_data')[0]
            except Exception:
                return None

        return tag_data_node

    def select_tag_data_node(self):
        """
        Selects the tag data node associated to the current selected Maya object
        """

        tag_data_node = self.get_tag_data_node_from_current_selection()
        if tag_data_node is None:
            return
        tp.Dcc.select_object(tag_data_node)

    def current_selection_has_metadata_node(self):
        """
        Returns True if the current selection has a valid tag data node associated to it or False otherwise
        :return: bool
        """

        current_selection = self.get_current_selection()

        if current_selection == 'scene':
            if tp.Dcc.object_exists('tag_data_scene'):
                return True
        else:
            if not tp.Dcc.object_exists(current_selection):
                return False
            if tp.Dcc.attribute_exists(node=current_selection, attribute_name='tag_data'):
                if tp.Dcc.list_connections(node=current_selection, attribute_name='tag_data') is not None:
                    return True

        return False

    def check_if_current_selected_metadata_node_has_valid_info(self):
        """
        Returns whether current selected metadat anode has valid info or not
        :param cls:
        :return:
        """

        tag_data_node = self.get_tag_data_node_from_current_selection()
        user_defined_attrs = tp.Dcc.list_user_attributes(node=tag_data_node)
        if user_defined_attrs and len(user_defined_attrs) > 0:
            return True

        return False

    def get_tag_data_nodes(self, project, as_tag_nodes=False):
        """
        Returns all scene tag data nodes in the current scene and for the given project
        :param project: ArtellaProject
        :param as_tag_nodes: bool
        :return: list
        """

        tag_nodes = list()
        objs = tp.Dcc.all_scene_objects()
        for obj in objs:
            valid_tag_data = tp.Dcc.attribute_exists(
                node=obj, attribute_name=self.TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME)
            if valid_tag_data:
                tag_type = tp.Dcc.get_attribute_value(
                    node=obj, attribute_name=self.TagDefinitions.TAG_TYPE_ATTRIBUTE_NAME)
                if tag_type and tag_type == project.tag_type_id:
                    if as_tag_nodes and artellapipe.TagNode:
                        obj = artellapipe.TagNode(project=project, node=obj)
                    tag_nodes.append(obj)

        return tag_nodes

    def get_tag_info_nodes(self, as_tag_nodes=False):
        """
        Returns all nodes containing tag info data
        :return: list
        """

        tag_info_nodes = list()
        objs = tp.Dcc.all_scene_objects()
        for obj in objs:
            valid_tag_info_data = tp.Dcc.attribute_exists(
                node=obj, attribute_name=self.TagDefinitions.TAG_INFO_ATTRIBUTE_NAME)
            if valid_tag_info_data:
                if as_tag_nodes and artellapipe.TagNode:
                    tag_info = tp.Dcc.get_attribute_value(
                        node=obj, attribute_name=self.TagDefinitions.TAG_INFO_ATTRIBUTE_NAME)
                    obj = artellapipe.TagNode(project=self, node=obj, tag_info=tag_info)
                tag_info_nodes.append(obj)

        return tag_info_nodes
