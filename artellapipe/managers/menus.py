#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle tools
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtWidgets import *

import tpDcc
from tpDcc.managers import menus
from tpDcc.libs.python import python

import artellapipe


class MenusManager(menus.MenusManager, object):
    """
    Class that handles all tools
    """

    def create_menus(self, package_name, project=None):
        """
        Overrides base ToolsManager create menus function
        :param package_name: str
        :param project: ArtellaProject
        """

        if not project:
            if hasattr(artellapipe, 'project') and artellapipe.project:
                project = artellapipe.project
        if not project:
            artellapipe.logger.warning('Impossible to create menu because project is not defined!')
            return False

        self._menu_names[package_name] = project.config.get('menu', 'name')
        self._object_menu_names[package_name] = project.config.get('menu', 'object_name')

        self.remove_previous_menus(project=project, package_name=package_name)
        self.create_project_description_menu(package_name=package_name, project=project)
        main_menu = self.create_main_menu(package_name=package_name)
        if not main_menu:
            artellapipe.logger.warning('Impossible to create main menu for "{}"'.format(package_name))
            return False

        menus_config = tpDcc.ConfigsMgr().get_config(
            config_name='artellapipe-menu',
            package_name=project.get_clean_name(),
            root_package_name='artellapipe',
            environment=project.get_environment()
        )
        if not menus_config:
            artellapipe.logger.warning(
                'Impossible to create menu for project "{}" because menu configuration file not found!'.format(
                    project.get_clean_name()))
            return False

        menus_config = menus_config.get('menus', default=list())
        if menus_config:
            for menu_data in menus_config:
                for _, data in menu_data.items():
                    for i in iter(data):
                        if python.is_string(i) and i == 'separator':
                            main_menu.addSeparator()
                            continue
                        self._menu_creator(main_menu, i, project.get_clean_name(), dev=project.is_dev())

        # Tools Menus
        tools_menu_data = self.get_tools_menus() or dict()
        for pkg_name, menu_data in tools_menu_data.items():
            for tool_path, data in menu_data.items():
                for i in iter(data):
                    if python.is_string(i) and i == 'separator':
                        main_menu.addSeparator()
                        continue
                    self._menu_creator(main_menu, i, project.get_clean_name(), dev=project.is_dev())

        self.create_tray_menu(project=project)
        self.create_bug_tracker_action(package_name=package_name)

        return True

    def remove_previous_menus(self, project=None, package_name=None):
        super(MenusManager, self).remove_previous_menus(package_name=package_name)

        if not project:
            if hasattr(artellapipe, 'project') and artellapipe.project:
                project = artellapipe.project
        if not project:
            artellapipe.logger.warning('Impossible to remove menu because project is not defined!')
            return False

        main_win = tpDcc.Dcc.get_main_window()
        parent_menu_bar = main_win.menuBar() if main_win else None
        if not parent_menu_bar:
            return

        menu_object_name = project.config.get('menu', 'object_name')

        for child_widget in parent_menu_bar.children():
            if child_widget == menu_object_name:
                child_widget.deleteLater()

    def create_project_description_menu(self, project, package_name):
        """
        Creates project description menu
        :return:
        """

        if not project:
            if hasattr(artellapipe, 'project') and artellapipe.project:
                project = artellapipe.project
        if not project:
            artellapipe.logger.warning('Impossible to create project description menu because project is not defined!')
            return False

        main_win = tpDcc.Dcc.get_main_window()
        parent_menu_bar = main_win.menuBar() if main_win else None
        if not parent_menu_bar:
            return

        project_description_menu_name = '{}_description'.format(package_name)

        # Remove previous created menu
        for child_widget in parent_menu_bar.children():
            if child_widget.objectName() == project_description_menu_name:
                child_widget.deleteLater()

        description = '|      [{}]'.format(project.get_environment())
        project_description_menu = QMenu(description, parent=parent_menu_bar)
        parent_menu_bar.addMenu(project_description_menu)
        project_description_menu.setObjectName(project_description_menu_name)
        project_description_menu.setTearOffEnabled(False)

    def create_bug_tracker_action(self, package_name):
        """
        Creates bug tracker action
        :return:
        """

        main_win = tpDcc.Dcc.get_main_window()
        parent_menu_bar = main_win.menuBar() if main_win else None
        if not parent_menu_bar:
            return

        bug_object_action_name = '{}_bugTracker'.format(package_name)

        # Remove previous created menu
        for child_widget in parent_menu_bar.children():
            if child_widget.objectName() == bug_object_action_name:
                child_widget.deleteLater()

        bug_tracker_action = QAction(parent_menu_bar)
        bug_tracker_action.setIcon(tpDcc.ResourcesMgr().icon('bug', theme='color'))
        parent_menu_bar.addAction(bug_tracker_action)
        bug_tracker_action.setObjectName(bug_object_action_name)
        bug_tracker_action.triggered.connect(partial(self._launch_tool_by_id, 'artellapipe-tools-bugtracker'))

    def create_tray_menu(self, project=None):
        """
        Creates project tray action
        :return:
        """

        if not project:
            if hasattr(artellapipe, 'project') and artellapipe.project:
                project = artellapipe.project
        if not project:
            artellapipe.logger.warning('Impossible to create tray menu because project is not defined!')
            return False

        main_win = tpDcc.Dcc.get_main_window()
        parent_menu_bar = main_win.menuBar() if main_win else None
        if not parent_menu_bar:
            return

        tray_object_menu_name = project.config.get('tray', 'name')

        # Remove previous created menu
        for child_widget in parent_menu_bar.children():
            if child_widget.objectName() == tray_object_menu_name:
                child_widget.deleteLater()

        tray_menu = QMenu(parent=parent_menu_bar)
        tray_menu.setIcon(project.tray_icon)
        parent_menu_bar.addMenu(tray_menu)
        tray_menu.setObjectName(tray_object_menu_name)
        tray_menu.setTearOffEnabled(True)

        tray_children = project.config.get('tray', 'children', default=list())
        for child in tray_children:
            item_lbl = child.get('label', '')
            item_command = child.get('command', '')
            item_icon_name = child.get('icon', '')
            item_tip = child.get('tip', '')
            if not item_lbl:
                continue
            if item_lbl == 'separator':
                tray_menu.addSeparator()
            else:
                item_icon = tpDcc.ResourcesMgr().icon(item_icon_name, theme='color')
                if item_icon and not item_icon.isNull():
                    new_item = QAction(item_icon, item_lbl, tray_menu)
                else:
                    new_item = QAction(tray_menu, text=item_lbl)
                if item_command:
                    new_item.triggered.connect(partial(self._launch_command, item_command))
                if item_tip:
                    new_item.setToolTip(item_tip)
                    new_item.setStatusTip(item_tip)
                tray_menu.addAction(new_item)

    def _launch_tool_by_id(self, tool_id, **kwargs):
        """
        Internal function that launch a tool by its ID
        :param tool_id: str
        :param kwargs: dict
        """

        project = None
        try:
            project = artellapipe.project
        except Exception:
            pass
        if not project:
            artellapipe.logger.error('Impossible to launch because Artella project is not defined!')
            return None

        is_dev = project.is_dev()

        tpDcc.ToolsMgr().launch_tool_by_id(tool_id, do_reload=is_dev, debug=is_dev, project=project)
