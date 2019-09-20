#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains lamina validation implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


import tpDccLib as tp

import pyblish.api


class ValidateLamina(pyblish.api.InstancePlugin):
    """
    Checks if there are geometry with ngons
    """

    label = 'Topology - Lamina'
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

        lamina_found = list()
        sel_it = OpenMaya.MItSelectionList(meshes_selection_list)
        while not sel_it.isDone():
            face_it = OpenMaya.MItMeshPolygon(sel_it.getDagPath())
            object_name = sel_it.getDagPath().getPath()
            while not face_it.isDone():
                lamina_faces = face_it.isLamina()
                if lamina_faces:
                    face_index = face_it.index()
                    component_name = '{}.f[{}]'.format(object_name, face_index)
                    lamina_found.append(component_name)
                face_it.next(None)
            sel_it.next()

        if lamina_found:
            msg = 'Lamina Faces in the following components: {}'.format(lamina_found)
            if self.must_pass:
                cmds.select(lamina_found)
                self.log.info('Lamina faces selected in viewport!')
                self.log.error(msg)
                assert not lamina_found, msg
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
