#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains poles validation implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp

import pyblish.api


class ValidatePoles(pyblish.api.InstancePlugin):
    """
    Checks if there are geometry with poles (a vertex is connected to more than 5 edges)
    """

    label = 'Topology - Vertex Poles'
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

        poles_found = list()
        sel_it = OpenMaya.MItSelectionList(meshes_selection_list)
        while not sel_it.isDone():
            vertex_it = OpenMaya.MItMeshVertex(sel_it.getDagPath())
            object_name = sel_it.getDagPath().getPath()
            while not vertex_it.isDone():
                if vertex_it.numConnectedEdges() > 5:
                    vertex_index = vertex_it.index()
                    component_name = '{}.v[{}]'.format(object_name, vertex_index)
                    poles_found.append(component_name)
                vertex_it.next()
            sel_it.next()

        if poles_found:
            msg = 'Vertex Poles in the following components: {}'.format(poles_found)
            if self.must_pass:
                cmds.select(poles_found)
                self.log.info('Vertex Poles selected in viewport!')
                self.log.error(msg)
                assert not poles_found, msg
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
