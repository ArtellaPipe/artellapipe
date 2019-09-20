#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains penetrating uvs validation implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


import tpDccLib as tp

import pyblish.api


class ValidatePenetratingUVs(pyblish.api.InstancePlugin):
    """
    Checks if a geometry node has its UVs penetrating or not
    """

    label = 'Topology - Penetrating UVs'
    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['model']
    must_pass = True

    def process(self, instance):

        import maya.cmds as cmds

        node = instance.data.get('node', None)
        assert tp.Dcc.object_exists(node), 'No valid node found in current instance: {}'.format(instance)

        nodes_to_check = self._nodes_to_check(node)
        assert nodes_to_check, 'No Nodes to check found!'

        penetrating_uvs_found = list()
        for node in nodes_to_check:
            shape = tp.Dcc.list_shapes(node, full_path=True)
            convert_to_faces = cmds.ls(cmds.polyListComponentConversion(shape, tf=True), fl=True)
            overlapping = (cmds.polyUVOverlap(convert_to_faces, oc=True))
            if overlapping:
                for obj in overlapping:
                    penetrating_uvs_found.append(obj)

        if penetrating_uvs_found:
            msg = 'Penetrating UVs found in following geometry nodes: {}'.format(penetrating_uvs_found)
            if self.must_pass:
                cmds.select(penetrating_uvs_found)
                self.log.info('Geometry nodes with penetrating UVs selected in viewport!')
                self.log.error(msg)
                assert not penetrating_uvs_found, msg
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
