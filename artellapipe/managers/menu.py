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
from functools import partial

from six import string_types

from Qt.QtWidgets import *

from tpPyUtils import decorators
import tpDccLib as tp
from tpQtLib.core import menu

import artellapipe
import artellapipe.register
from artellapipe.utils import resource

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

    def create_main_menu(self):
        # self._menu = self._parent.menuBar().addMenu(self._menu_name)
        self._menu = menu.SearchableMenu(
            objectName=self._menu_object_name, title=self._menu_name, parent=self._parent.menuBar())
        self._parent.menuBar().addMenu(self._menu)
        self._menu.setObjectName(self._menu_object_name)
        self._menu.setTearOffEnabled(True)

    def create_tray_menu(self):
        self._tray_menu = QMenu(parent=self._parent.menuBar())
        self._tray_menu.setIcon(self._project.tray_icon)
        self._parent.menuBar().addMenu(self._tray_menu)
        self._tray_menu.setObjectName(self._tray_object_menu_name)
        self._tray_menu.setTearOffEnabled(True)

        tray_children = self._project.config.get('tray', 'children', default=list())
        for child in tray_children:
            item_lbl = child.get('label', '')
            item_command = child.get('command', '')
            item_icon_name = child.get('icon', '')
            item_tip = child.get('tip', '')
            if not item_lbl:
                continue
            if item_lbl == 'separator':
                self._tray_menu.addSeparator()
            else:
                item_icon = resource.ResourceManager().icon(item_icon_name)
                if item_icon and not item_icon.isNull():
                    new_item = QAction(item_icon, item_lbl, self._tray_menu)
                else:
                    new_item = QAction(self._tray_menu, text=item_lbl)
                if item_command:
                    new_item.triggered.connect(partial(self._launch_command, item_command))
                if item_tip:
                    new_item.setToolTip(item_tip)
                    new_item.setStatusTip(item_tip)
                self._tray_menu.addAction(new_item)

    def create_project_description_menu(self):
        description = '|      [{}]'.format(self._project.get_environment())
        self._project_description_menu = QMenu(description, parent=self._parent.menuBar())
        self._parent.menuBar().addMenu(self._project_description_menu)
        self._project_description_menu.setObjectName(self._project_description_menu_name)
        self._project_description_menu.setTearOffEnabled(False)

    def create_bug_tracker_action(self):
        self._bug_tracker_action = QAction(self._parent.menuBar())
        self._bug_tracker_action.setIcon(resource.ResourceManager().icon('bug'))
        self._parent.menuBar().addAction(self._bug_tracker_action)
        self._bug_tracker_action.setObjectName(self._bug_object_action_name)
        self._bug_tracker_action.triggered.connect(partial(self._launch_tool_by_name, 'bugtracker'))

    def get_menu_names(self):
        """
        Returns a list with the names of the created menus
        :return: list
        """

        return [self._menu_object_name, self._tray_object_menu_name, self._bug_object_action_name,
                self._project_description_menu_name]

    def clean_menus(self):

        if not self._parent:
            return False

        if not self._menu_name or not self._menu_object_name:
            LOGGER.warning('Impossible to clean menus because menu info is not initialized!')
            return False

        for child_widget in self._parent.menuBar().children():
            if child_widget.objectName() in self.get_menu_names():
                LOGGER.debug('Removing old "{}" menu ...'.format(self._project.name, child_widget.objectName()))
                child_widget.deleteLater()

        return True

    def get_menu(self, menu_name):
        """
        Returns the menu object if extsi; otherwise None
        :param str menu_name: name of the menu to get
        :return: QMenu
        """

        if menu_name == self._menu.objectName():
            return self._menu

        return self._sub_menus.get(menu_name)

    def create_menus(self):
        """
        Creates all the menus
        """

        if not self._project:
            LOGGER.warning("Impossible to create menus because project is not defined!")
            return False

        if tp.Dcc == tp.Dccs.Unknown or not self._parent:
            return

        self.clean_menus()
        self.create_project_description_menu()
        self.create_main_menu()

        menu_data = artellapipe.ToolsMgr().get_tool_menus()

        for tool_path, data in menu_data.items():
            for i in iter(data):
                if isinstance(i, string_types) and i == 'separator':
                    self._menu.addSeparator()
                    continue
                self._menu_creator(self._menu, i)

        self.create_tray_menu()
        self.create_bug_tracker_action()

        return True

    def _menu_creator(self, parent_menu, data):
        menu = self.get_menu(data['label'])
        if menu is None and data.get('type', '') == 'menu':
            menu = parent_menu.addMenu(data['label'])
            menu.setObjectName(data['label'])
            menu.setTearOffEnabled(True)
            self._sub_menus[data['label']] = menu

        if 'children' not in data:
            return

        for i in iter(data['children']):
            action_type = i.get('type', 'definition')
            if action_type == 'separator':
                self._menu.addSeparator()
                continue
            elif action_type == 'group':
                sep = self._menu.addSeparator()
                sep.setText(i['label'])
                continue
            elif action_type == 'menu':
                self._menu_creator(menu, i)
                continue
            self._add_action(i, menu)

    def _add_action(self, item_info, parent):
        tool_id = item_info['id']
        tool_type = item_info.get('type', 'definition')
        tool_data = None
        if tool_type == 'definition' or tool_type == 'toolset':
            tool_data = artellapipe.ToolsMgr().get_tool_data_from_id(tool_id)
        if tool_data is None:
            LOGGER.warning('Failed to find Tool: {}, type {}'.format(tool_id, tool_type))
            return
        tool_icon = None
        tool_icon_name = tool_data['config'].data.get('icon', None)
        if tool_icon_name:
            tool_icon = resource.ResourceManager().icon(tool_icon_name)
        tool_menu_ui_data = tool_data['config'].data.get('menu_ui', {})
        label = tool_menu_ui_data.get('label', 'No_label')
        tagged_action = menu.SearchableTaggedAction(label=label, icon=tool_icon, parent=self._parent)
        is_checkable = tool_menu_ui_data.get('is_checkable', False)
        is_checked = tool_menu_ui_data.get('is_checked', False)
        if is_checkable:
            tagged_action.setCheckable(is_checkable)
            tagged_action.setChecked(is_checked)
            tagged_action.connect(partial(self._launch_tool, tool_data))
            if tool_type == 'definition':
                tagged_action.toggled.connect(partial(self._launch_tool, tool_data))
                if tool_menu_ui_data.get('load_on_startup', False):
                    self._launch_tool(tool_data, is_checked)
            elif tool_type == 'toolset':
                tagged_action.toggled.connect(partial(self._launch_tool_by_id, tool_id))
        else:
            if tool_type == 'definition':
                tagged_action.triggered.connect(partial(self._launch_tool, tool_data))
                if tool_menu_ui_data.get('load_on_startup', False):
                    self._launch_tool(tool_data)
            elif tool_type == 'toolset':
                tagged_action.triggered.connect(partial(self._launch_tool_by_id, tool_id))

        icon = tool_menu_ui_data.get('icon', None)
        if icon:
            pass

        tagged_action.tags = set(tool_data['config'].data.get('tags', []))

        parent.addAction(tagged_action)
        LOGGER.debug('Added Action: {}'.format(label))

    def _launch_tool_by_id(self, tool_id, **kwargs):
        # TODO: The reloading only should be done in DEV mode
        artellapipe.ToolsMgr().run_tool(self._project, tool_id, extra_args=kwargs, do_reload=True)

    def _launch_tool_by_name(self, name, **kwargs):
        artellapipe.ToolsMgr().run_tool(
            self._project, name, extra_args=kwargs)

    def _launch_tool(self, tool, *args, **kwargs):
        print('Launching Tool: {}'.format(tool))

    def _launch_command(self, command, *args, **kwargs):
        exec(command)


@decorators.Singleton
class ArtellaMenuManagerSingleton(ArtellaMenuManager, object):
    def __init__(self):
        ArtellaMenuManager.__init__(self)


artellapipe.register.register_class('MenuMgr', ArtellaMenuManagerSingleton)
