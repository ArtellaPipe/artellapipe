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


class ArtellaShelfManager(object):

    def create_shelf(self, project):
        """
        Function that should be implemented in specific DCC Shelf Managers to create proper menu
        """

        parent = tp.Dcc.get_main_window()
        shelf_name = project.config.get('shelf', 'name')
        shelf_icon_name = project.config.get('shelf', 'icon_name')
        shelf_icon = tp.ResourcesMgr().icon(shelf_icon_name, key='project')
