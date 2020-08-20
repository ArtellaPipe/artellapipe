#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager for Artella Nomenclature
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDcc
from tpDcc.libs.python import python

import artellapipe
from artellapipe.libs.naming.core import naminglib


class NamesManager(object):

    _config = None

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tpDcc.ConfigsMgr().get_config(
                config_name='tpDcc-naming',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='tpDcc',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    def check_node_name(self, node_name):
        """
        Returns whether or not given node corresponds to a valid node name taking into consideration node type
        :param node_name: str
        :return: bool
        """

        parsed_name = self.parse_node_name(node_name)
        if 'node_type' not in parsed_name:
            return False

        for k, v in parsed_name.items():
            if v is None:
                return False

        auto_suffix = self.config.get('auto_suffixes', default=dict()) if self.config else None
        obj_type = self._get_object_type(node_name)

        if self.config and auto_suffix:
            if obj_type not in auto_suffix:
                return True if obj_type == parsed_name['node_type'] else False
            else:
                return True if auto_suffix[obj_type] == parsed_name['node_type'] else False
        else:
            return True if obj_type == parsed_name['node_type'] else False

    def parse_node_name(self, node_name):
        """
        Parses given node name
        :param node_name: str
        :return: list(str)
        """

        if not tpDcc.is_maya():
            artellapipe.logger.warning('Parse Node Name by type functionality is only supported in Maya!')
            return None

        name_lib = naminglib.ArtellaNameLib()
        name_lib.set_active_rule('node')

        return name_lib.parse(node_name)

    def solve_node_name_by_type(self, node_names=None, **kwargs):
        """
        Resolves node name taking into account its type
        In this case, the type of the node will be used to retrieve an an automatic rule
        The rule name will be retrieved using auto_suffix dict from tpDcc-naming configuration file
        :param node_names: str or list, name of the node we want to take name of
        :return: str
        """

        if not tpDcc.is_maya():
            artellapipe.logger.warning('Solve Node Name by type functionality is only supported in Maya!')
            return None

        import tpDcc.dccs.maya as maya
        from tpDcc.dccs.maya.core import name

        name_lib = naminglib.ArtellaNameLib()

        if not self.config:
            artellapipe.logger.warning(
                'Impossible to generate name from node because not naming configuration was found!')
            return None

        auto_suffix = self.config.get('auto_suffixes', default=dict())
        if not auto_suffix:
            artellapipe.logger.warning(
                'Impossible to launch auto suffix functionality because no auto suffixes are defined!')
            return None

        solved_names = dict()
        return_names = list()

        if not node_names:
            node_names = tpDcc.Dcc.selected_nodes()
        if not node_names:
            return
        node_names = python.force_list(node_names)

        for obj_name in node_names:
            obj_uuid = maya.cmds.ls(obj_name, uuid=True)[0]
            if obj_uuid in solved_names:
                artellapipe.logger.warning(
                    'Node with name: "{} and UUID "{}" already renamed to "{}"! Skipping ...'.format(
                        obj_name, obj_uuid, solved_names[obj_name]))
                continue

            obj_type = self._get_object_type(obj_name)
            if obj_type not in auto_suffix:
                rule_name = 'node'
                node_type = obj_type
            else:
                rule_name = auto_suffix[obj_type]
                node_type = auto_suffix[obj_type]

            if not name_lib.has_rule(rule_name):
                if not name_lib.has_rule('node'):
                    artellapipe.logger.warning(
                        'Impossible to rename node "{}" by its type "{}" because rule "{}" it is not defined and '
                        'callback rule "node" either'.format(obj_name, obj_type, rule_name))
                else:
                    rule_name = 'node'

            if rule_name == 'node':
                solved_name = self.solve_name(rule_name, obj_name, node_type=node_type, **kwargs)
            else:
                solved_name = self.solve_name(rule_name, obj_name, **kwargs)
            solved_names[obj_uuid] = solved_name

        if not solved_names:
            return

        for obj_id, solved_name in solved_names.items():
            obj_name = maya.cmds.ls(obj_id, long=True)[0]
            if not solved_names:
                return_names.append(obj_name)
            else:
                new_name = name.rename(obj_name, solved_name, uuid=obj_id, rename_shape=True)
                return_names.append(new_name)

        return return_names

    def solve_name(self, rule_name, *args, **kwargs):
        """
        Resolves name with given rule and attributes
        :param rule_name: str
        :param args: list
        :param kwargs: dict
        """

        name_lib = naminglib.ArtellaNameLib()

        if not rule_name or not name_lib.has_rule(rule_name):
            artellapipe.logger.warning(
                'Impossible to retrieve name because rule name "{}" is not defined!'.format(rule_name))
            return None

        current_rule = name_lib.active_rule()
        name_lib.set_active_rule(rule_name)
        solved_name = name_lib.solve(*args, **kwargs)
        if current_rule:
            if rule_name != current_rule.name:
                name_lib.set_active_rule(current_rule.name)
        else:
            name_lib.set_active_rule(None)

        return solved_name

    def _get_object_type(self, obj_name):
        """
        Internal function that returns object type given a node
        :param obj_name: str
        :return: str
        """

        if not tpDcc.is_maya():
            artellapipe.logger.warning('Solve Node Name by type functionality is only supported in Maya!')
            return None

        import tpDcc.dccs.maya as maya

        # TODO: This code is a duplicated version of the one in
        #  tpDcc.dccs.maya.core.name.auto_suffix_object function. Move this code to a DCC specific function
        obj_type = maya.cmds.objectType(obj_name)
        if obj_type == 'transform':
            shape_nodes = maya.cmds.listRelatives(obj_name, shapes=True, fullPath=True)
            if not shape_nodes:
                obj_type = 'group'
            else:
                obj_type = maya.cmds.objectType(shape_nodes[0])
        elif obj_type == 'joint':
            shape_nodes = maya.cmds.listRelatives(obj_name, shapes=True, fullPath=True)
            if shape_nodes and maya.cmds.objectType(shape_nodes[0]) == 'nurbsCurve':
                obj_type = 'controller'
        if obj_type == 'nurbsCurve':
            connections = maya.cmds.listConnections('{}.message'.format(obj_name))
            if connections:
                for node in connections:
                    if maya.cmds.nodeType(node) == 'controller':
                        obj_type = 'controller'
                        break

        return obj_type
