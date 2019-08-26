#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to manage Light Rigs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpPyUtils import folder as folder_utils

import tpDccLib as tp

from tpQtLib.core import base, qtutils
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.core import defines
from artellapipe.gui import window


# ===============================================================================================

_import_icon = artellapipe.resource.icon('import')
_reference_icon = artellapipe.resource.icon('reference')
_open_icon = artellapipe.resource.icon('open')

# ===============================================================================================


class LightRig(base.BaseWidget, object):
    def __init__(self, project, name, parent=None):

        self._project = project
        self._name = name

        super(LightRig, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)

        return main_layout

    def ui(self):
        super(LightRig, self).ui()

        self.setMaximumSize(QSize(120, 140))
        self.setMinimumSize(QSize(120, 140))

        self._light_btn = QPushButton()
        self._light_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._light_btn.setIcon(self._project.resource.icon(self._name.lower(), theme='lightrigs'))
        self._light_btn.setIconSize(QSize(120, 140))
        self._title_lbl = QLabel(self._name)
        self._title_lbl.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self._light_btn)
        self.main_layout.addWidget(self._title_lbl)

        self._light_menu = QMenu(self)
        open_action = QAction(_open_icon, 'Open Light Rig', self._light_menu)
        import_action = QAction(_import_icon, 'Import Light Rig', self._light_menu)
        reference_action = QAction(_reference_icon, 'Reference Light Rig', self._light_menu)
        self._light_menu.addAction(open_action)
        self._light_menu.addAction(import_action)
        self._light_menu.addAction(reference_action)

        self._light_btn.clicked.connect(self._on_reference_light_rig)
        open_action.triggered.connect(self._on_open_light_rig)
        import_action.triggered.connect(self._on_import_light_rig)
        reference_action.triggered.connect(self._on_reference_light_rig)

    def contextMenuEvent(self, event):
        self._light_menu.exec_(event.globalPos())

    @property
    def name(self):
        """
        Returns the name of the light rig
        :return: str
        """

        return self._name

    def _get_light_rig_name(self):
        """
        Returns name of the light rig
        :return: str
        """

        # TODO: We should use naming manager to generate this name
        return 'LR_{}.ma'.format(self._name.title()).replace(' ', '_')

    def _on_open_light_rig(self):
        """
        Internal callback function that is called when the user wants to open a light rig
        """

        if tp.Dcc.scene_is_modified():
            tp.Dcc.save_current_scene(force=False)

        light_rigs_path = self._project.get_light_rigs_path()
        if not light_rigs_path:
            artellapipe.logger.warning('Project {} has no Light Rigs!'.format(self._project.name.title()))
            return

        light_rig_name = self._get_light_rig_name()
        light_rig = os.path.join(light_rigs_path, defines.ARTELLA_WORKING_FOLDER, self._name.title(), light_rig_name)
        if not os.path.exists(light_rig):
            artellapipe.logger.error('Light Rig File {} does not exists!'.format(light_rig_name))
            return False
        return tp.Dcc.open_file(light_rig, force=True)

    def _on_import_light_rig(self):
        """
        Internal callback function that is called when the user wants to import a light rig
        """

        light_rigs_path = self._project.get_light_rigs_path()
        if not light_rigs_path:
            artellapipe.logger.warning('Project {} has no Light Rigs!'.format(self._project.name.title()))
            return

        light_rig_name = self._get_light_rig_name()
        light_rig = os.path.join(light_rigs_path, defines.ARTELLA_WORKING_FOLDER, self._name.title(), light_rig_name)
        if not os.path.exists(light_rig):
            artellapipe.logger.error('Light Rig File {} does not exists!'.format(light_rig_name))
            return False

        return tp.Dcc.import_file(light_rig, force=True)

    def _on_reference_light_rig(self):
        """
        Internal callback function that is called when the user wants to reference a light rig
        """

        light_rigs_path = self._project.get_light_rigs_path()
        if not light_rigs_path:
            artellapipe.logger.warning('Project {} has no Light Rigs!'.format(self._project.name.title()))
            return

        light_rig_name = self._get_light_rig_name()
        light_rig = os.path.join(light_rigs_path, defines.ARTELLA_WORKING_FOLDER, self._name.title(), light_rig_name)
        print(light_rig)
        if not os.path.exists(light_rig):
            artellapipe.logger.error('Light Rig File {} does not exists!'.format(light_rig_name))
            return False

        return tp.Dcc.reference_file(light_rig, force=True)


class ArtellaLightRigManager(window.ArtellaWindow, object):

    LOGO_NAME = 'lightrigsmanager_logo'
    LIGHT_RIG_CLASS = LightRig

    def __init__(self, project):
        super(ArtellaLightRigManager, self).__init__(
            project=project,
            name='LightRigManagerWindow',
            title='Light Rigs Manager',
            size=(100, 150)
        )

    def ui(self):
        super(ArtellaLightRigManager, self).ui()

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(0)
        self.main_layout.addLayout(buttons_layout)

        self._open_btn = QToolButton()
        self._open_btn.setIcon(artellapipe.resource.icon('open'))
        self._sync_btn = QToolButton()
        self._sync_btn.setIcon(artellapipe.resource.icon('sync'))
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        buttons_layout.addWidget(self._open_btn)
        buttons_layout.addWidget(splitters.get_horizontal_separator_widget())
        buttons_layout.addWidget(self._sync_btn)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.main_layout.addLayout(splitters.SplitterLayout())

        self._light_rigs_layout = QHBoxLayout()
        self._light_rigs_layout.setContentsMargins(5, 5, 5, 5)
        self._light_rigs_layout.setSpacing(5)
        self._light_rigs_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.addLayout(self._light_rigs_layout)

        self._update_ui()

    def setup_signals(self):
        self._open_btn.clicked.connect(self._on_open_light_rigs_folder)
        self._sync_btn.clicked.connect(self._on_sync_light_rigs)

    def _update_ui(self):
        valid_light_rigs = self._project.get_light_rigs_path()
        if not valid_light_rigs:
            return
        working_path = os.path.join(valid_light_rigs, defines.ARTELLA_WORKING_FOLDER)
        if not os.path.exists(working_path):
            return

        qtutils.clear_layout(self._light_rigs_layout)
        for f in os.listdir(working_path):
            light_rig = self.LIGHT_RIG_CLASS(project=self._project, name=f)
            self._light_rigs_layout.addWidget(light_rig)

    def _on_open_light_rigs_folder(self):
        light_rigs_path = os.path.join(self._project.get_light_rigs_path(), defines.ARTELLA_WORKING_FOLDER)
        if os.path.exists(light_rigs_path):
            folder_utils.open_folder(light_rigs_path)

    def _on_sync_light_rigs(self):
        self._project.sync_paths([self._project.get_light_rigs_path()])
        self._update_ui()


def run(project):
    win = ArtellaLightRigManager(project=project)
    win.show()

    return win
