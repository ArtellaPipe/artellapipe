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

from tpDcc.libs.python import decorators

import artellapipe.register
from artellapipe.libs.naming.core import naminglib


class ArtellaNamesManager(object):
    def __init__(self):
        self._project = None

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project

    def solve_name(self, rule_name, *args, **kwargs):
        """
        Resolves name with given rule and attributes
        :param rule_name: str
        :param args: list
        :param kwargs: dict
        """

        name_lib = naminglib.ArtellaNameLib()

        if not rule_name or not name_lib.has_rule(rule_name):
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


@decorators.Singleton
class ArtellaNamesManagerSingleton(ArtellaNamesManager, object):
    def __init__(self):
        ArtellaNamesManager.__init__(self)


artellapipe.register.register_class('NamesMgr', ArtellaNamesManagerSingleton)
