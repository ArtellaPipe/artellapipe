#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains hard edge validation implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp

import pyblish.api


class ValidateHardEdges(pyblish.api.InstancePlugin):
    """
    Checks if there are geometry with hard edges
    """

    label = 'Topology - Hard Edges'
    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['model']
    must_pass = True

    def process(self, instance):

        import maya.cmds as cmds
        import maya.api.OpenMaya as OpenMaya

        node = instance.data.get('node', None)
        assert tp.Dcc.object_exists(node), 'No valid node found in current instance: {}'.format(instance)

        nodes_to_check = self._nodes_to_check(node)
        assert nodes_to_check, 'No Nodes to check found!'

        meshes_selection_list = OpenMaya.MSelectionList()
        for node in nodes_to_check:
            meshes_selection_list.add(node)

        hard_edges_found = list()
        sel_it = OpenMaya.MItSelectionList(meshes_selection_list)
        while not sel_it.isDone():
            edge_it = OpenMaya.MItMeshEdge(sel_it.getDagPath())
            object_name = sel_it.getDagPath().getPath()
            while not edge_it.isDone():
                if edge_it.isSmooth == False and not edge_it.onBoundary() == False:
                    edge_index = edge_it.index()
                    component_name = '{}.e[{}]'.format(object_name, edge_index)
                    hard_edges_found.append(component_name)
                edge_it.next()
            sel_it.next()

        if hard_edges_found:
            msg = 'Hard Edges in the following components: {}'.format(hard_edges_found)
            if self.must_pass:
                cmds.select(hard_edges_found)
                self.log.info('Edges with hard edges selected in viewport!')
                self.log.error(msg)
                assert not hard_edges_found, msg
            else:
                self.log.warning(msg)

    def _nodes_to_check(self, node):

        valid_nodes = list()
        nodes = tp.Dcc.list_children(node=node, all_hierarchy=True, full_path=True, children_type='transform')
        if not nodes:
            nodes = [node]
        else:
            nodes.append(node)

        for node in nodes:
            shapes = tp.Dcc.list_shapes(node=node, full_path=True)
            if not shapes:
                continue
            valid_nodes.append(node)

        return valid_nodes
