#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility function to work with tagger
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp


def get_current_selection():
    """
    Returns current selected node
    :return: str
    """

    selected_nodes = tp.Dcc.selected_nodes()
    if selected_nodes:
        return selected_nodes[0]
    else:
        return 'scene'


def get_tag_data_node_from_current_selection(new_selection=None):
    """
    Returns the tag data node associated to the current selected Maya object
    :return: variant, None || str
    """

    current_selection = get_current_selection()

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


def select_tag_data_node():
    """
    Selects the tag data node associated to the current selected Maya object
    """

    tag_data_node = get_tag_data_node_from_current_selection()
    if tag_data_node is None:
        return
    tp.Dcc.select_object(tag_data_node)


def current_selection_has_metadata_node():
    """
    Returns True if the current selection has a valid tag data node associated to it or False otherwise
    :return: bool
    """

    current_selection = get_current_selection()

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


def check_if_current_selected_metadata_node_has_valid_info():
    """
    Returns whether current selected metadat anode has valid info or not
    :param cls:
    :return:
    """

    tag_data_node = get_tag_data_node_from_current_selection()
    user_defined_attrs = tp.Dcc.list_user_attributes(node=tag_data_node)
    if user_defined_attrs and len(user_defined_attrs) > 0:
        return True

    return False
