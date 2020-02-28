#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager that handles Artella Project DCC Shelf
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDcc as tp
from tpDcc.libs.python import decorators

import artellapipe.register


class ArtellaShelfManager(object):
    def __init__(self):
        self._project = None
        self._shelf_name = None
        self._parent = tp.Dcc.get_main_window()

    def set_project(self, project):
        self._project = project
        self._shelf_name = project.config.get('shelf', 'name')
        self._shelf_icon_name = project.config.get('shelf', 'icon_name')
        self._shelf_icon = tp.ResourcesMgr().icon(self._shelf_icon_name, key='project')
        self.create_shelf()

    @decorators.abstractmethod
    def create_shelf(self):
        """
        Function that should be implemented in specific DCC Shelf Managers to create proper menu
        """

        pass


@decorators.Singleton
class ArtellaShelfManagerSingleton(ArtellaShelfManager, object):
    def __init__(self):
        ArtellaShelfManager.__init__(self)


artellapipe.register.register_class('ShelfMgr', ArtellaShelfManagerSingleton)
