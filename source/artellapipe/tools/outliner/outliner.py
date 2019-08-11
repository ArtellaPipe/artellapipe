#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow to manage scene assets using Artella Pipeline
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import weakref

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import qtutils
from tpQtLib.widgets import stack, splitters

import artellapipe
from artellapipe.gui import window

from artellapipe.tools.outliner.widgets import settings


class ArtellaOutlinerWidget(QWidget, object):

    # Necessary to support Maya dock
    name = 'ArtellaOutlinerWidget'
    title = 'Outliner'

    _instances = list()

    def __init__(self, project, parent=None):

        self._project = project

        main_window = tp.Dcc.get_main_window()
        if parent is None:
            parent = main_window

        super(ArtellaOutlinerWidget, self).__init__(parent=parent)

        if tp.is_maya():
            ArtellaOutlinerWidget._delete_instances()
            self.__class__._instances.append(weakref.proxy(self))

        self.ui()

    @staticmethod
    def _delete_instances():
        for ins in ArtellaOutlinerWidget._instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except Exception:
                pass

            ArtellaOutlinerWidget._instances.remove(ins)
            del ins

    def ui(self):

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        if tp.is_maya():
            self.parent().layout().addLayout(self.main_layout)
        else:
            self.setLayout(self.main_layout)

        self._toolbar = QToolBar()
        self._setup_toolbar()
        self.main_layout.addWidget(self._toolbar)

        self._main_stack = stack.SlidingStackedWidget(self)
        self.main_layout.addWidget(self._main_stack)

        self._outliner_widget = QWidget()
        self._outliner_layout = QVBoxLayout()
        self._outliner_layout.setContentsMargins(2, 2, 2, 2)
        self._outliner_layout.setSpacing(2)
        self._outliner_widget.setLayout(self._outliner_layout)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        top_layout.setAlignment(Qt.AlignCenter)

        self._tags_menu_layout = QHBoxLayout()
        self._tags_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_menu_layout.setSpacing(0)
        self._tags_menu_layout.setAlignment(Qt.AlignTop)
        top_layout.addLayout(self._tags_menu_layout)

        self._tags_btn_grp = QButtonGroup(self)
        self._tags_btn_grp.setExclusive(True)
        tag_types = self._project.tag_types if self._project else list()

        self._outliners_stack = stack.SlidingStackedWidget()
        self._outliner_layout.addLayout(top_layout)
        self._outliner_layout.addLayout(splitters.SplitterLayout())
        self._outliner_layout.addWidget(self._outliners_stack)

        self._settings_widget = settings.ArtellaOutlinerSettings()

        self._main_stack.addWidget(self._outliner_widget)
        self._main_stack.addWidget(self._settings_widget)

        self.update_tags_types(tag_types)

        # self.settingswidget.settingsSaved.connect(self.open_tabs)

    def update_tags_types(self, tags_types):
        """
        Updates current tag categories with the given ones
        :param tags_types: list(str)
        """

        for btn in self._tags_btn_grp.buttons():
            self._tags_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._tags_menu_layout)

        total_buttons = 0
        for tag_type in tags_types:
            new_btn = QPushButton(tag_type.title())
            new_btn.setCheckable(True)
            self._tags_menu_layout.addWidget(new_btn)
            self._tags_btn_grp.addButton(new_btn)
            if total_buttons == 0:
                new_btn.setChecked(True)
            total_buttons += 1

    def _setup_toolbar(self):
        load_scene_shaders_action = QToolButton(self)
        load_scene_shaders_action.setText('Load Shaders')
        load_scene_shaders_action.setToolTip('Load and Apply All Scene Shaders')
        load_scene_shaders_action.setStatusTip('Load and Apply All Scene Shaders')
        load_scene_shaders_action.setIcon(artellapipe.resource.icon('shading_load'))
        load_scene_shaders_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        unload_scene_shaders_action = QToolButton(self)
        unload_scene_shaders_action.setText('Unload Shaders')
        unload_scene_shaders_action.setToolTip('Unload All Scene Shaders')
        unload_scene_shaders_action.setStatusTip('Unload All Scene Shaders')
        unload_scene_shaders_action.setIcon(artellapipe.resource.icon('shading_unload'))
        unload_scene_shaders_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        update_refs_action = QToolButton(self)
        update_refs_action.setText('Sync Assets')
        update_refs_action.setToolTip('Updates all asset references to the latest published version')
        update_refs_action.setStatusTip('Updates all asset references to the latest published version')
        update_refs_action.setIcon(artellapipe.resource.icon('sync_cloud'))
        update_refs_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        settings_action = QToolButton(self)
        settings_action.setText('Settings')
        settings_action.setToolTip('Outliner Settings')
        settings_action.setStatusTip('Outliner Settings')
        settings_action.setIcon(artellapipe.resource.icon('settings'))
        settings_action.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self._toolbar.addWidget(load_scene_shaders_action)
        self._toolbar.addWidget(unload_scene_shaders_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(update_refs_action)
        self._toolbar.addSeparator()
        self._toolbar.addWidget(settings_action)

        # load_scene_shaders_action.clicked.connect(sp.load_shaders)
        # unload_scene_shaders_action.clicked.connect(sp.unload_shaders)
        # settings_action.clicked.connect(self.open_settings)


class SolsticeOutliner(window.ArtellaWindow, object):

    LOGO_NAME = 'outliner_logo'

    def __init__(self, project, parent=None):
        super(SolsticeOutliner, self).__init__(
            project=project,
            name='ManagerWindow',
            title='Manager',
            size=(1100, 900),
            parent=parent
        )

    def ui(self):
        super(SolsticeOutliner, self).ui()

        self._outliner = ArtellaOutlinerWidget()
        self.main_layout.addWidget(self._outliner)


def run(project):
    if tp.is_maya():
        win = window.dock_window(project=project, window_class=ArtellaOutlinerWidget)
        return win
    else:
        win = SolsticeOutliner(project=project)
        win.show()
        return win
