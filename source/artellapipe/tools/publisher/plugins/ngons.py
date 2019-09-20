#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ngons validation implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp

import pyblish.api


class ValidateNGons(pyblish.api.InstancePlugin):
    """
    Checks if there are geometry with ngons
    """

    label = 'Topology - NGons'
    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['model']

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

        ngons_found = list()
        sel_it = OpenMaya.MItSelectionList(meshes_selection_list)
        while not sel_it.isDone():
            face_it = OpenMaya.MItMeshPolygon(sel_it.getDagPath())
            object_name = sel_it.getDagPath().getPath()
            while not face_it.isDone():
                num_of_edges = face_it.getEdges()
                if len(num_of_edges) > 4:
                    face_index = face_it.index()
                    component_name = '{}.f[{}]'.format(object_name, face_index)
                    ngons_found.append(component_name)
                face_it.next(None)
            sel_it.next()

        if ngons_found:
            cmds.select(ngons_found)
            self.log.info('Faces with NGons selected in viewport!')
            assert not ngons_found, 'NGons in the following components: {}'.format(ngons_found)

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