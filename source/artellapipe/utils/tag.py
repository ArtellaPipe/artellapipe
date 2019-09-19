#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions to work with ArtellaPipe tag nodes
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp


def get_tag_node(project, node):
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
                tag_node = project.TAG_NODE_CLASS(project=project, node=tag_data_node)
                return tag_node
    elif tp.Dcc.attribute_exists(node=node, attribute_name='tag_info'):
        tag_info = tp.Dcc.get_attribute_value(node=node, attribute_name='tag_info')
        tag_node = project.TAG_NODE_CLASS(project=project, node=node, tag_info=tag_info)
        return tag_node
