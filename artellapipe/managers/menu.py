#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager that handles Artella Project DCC Menu
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging

from tpPyUtils import decorators
import tpDccLib as tp

import artellapipe
import artellapipe.register

LOGGER = logging.getLogger()


class ArtellaMenuManager(object):
    def __init__(self):
        self._project = None
        self._menu = None
        self._tray_menu = None
        self._project_description_menu = None
        self._bug_tracker_action = None
        self._sub_menus = {}
        self._menu_name = None
        self._menu_object_name = None
        self._tray_object_menu_name = None
        self._project_description_menu_name = None
        self._bug_object_action_name = None
        self._parent = tp.Dcc.get_main_window()

    def set_project(self, project):
        self._project = project
        self._menu_name = project.config.get('menu', 'name')
        self._menu_object_name = project.config.get('menu', 'object_name')
        self._tray_object_menu_name = project.config.get('tray', 'name')
        self._project_description_menu_name = '{}_description'.format(self._menu_name)
        self._bug_object_action_name = '{}_bugTracker'.format(self._menu_name)
        self.create_menus()

    @decorators.abstractmethod
    def create_menus(self):
        """
        Function that should be implemented in specific DCC Menu Managers to create proper menu
        """

        pass

    def _launch_tool_by_id(self, tool_id, **kwargs):
        """
        Internal function that launch a tool by its ID
        :param tool_id: str
        :param kwargs: dict
        """

        # TODO: The reloading only should be done in DEV mode
        artellapipe.ToolsMgr().run_tool(self._project, tool_id, extra_args=kwargs, do_reload=True)

    def _launch_tool_by_name(self, name, **kwargs):
        """
        Internal function that launch a tool by its name
        :param name: str
        :param kwargs: dict
        """

        artellapipe.ToolsMgr().run_tool(self._project, name, extra_args=kwargs)

    def _launch_tool(self, tool, *args, **kwargs):
        print('Launching Tool: {}'.format(tool))

    def _launch_command(self, command, *args, **kwargs):
        """
        Internal function that launches the given Python command
        :param command: str
        :param args: list
        :param kwargs: dict
        """

        exec(command)


@decorators.Singleton
class ArtellaMenuManagerSingleton(ArtellaMenuManager, object):
    def __init__(self):
        ArtellaMenuManager.__init__(self)


artellapipe.register.register_class('MenuMgr', ArtellaMenuManagerSingleton)
