#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for asset overrides widget
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import json
import traceback

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe


class ShotOverrides(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project
        self._overrides = dict()
        self._loaded_overrides = list()

        super(ShotOverrides, self).__init__(parent=parent)

        self._update_menu()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ShotOverrides, self).ui()

        self.setMouseTracking(True)

        self._load_btn = QPushButton('Load Overrides')
        self._load_btn.setIcon(artellapipe.resource.icon('open'))
        self.main_layout.addWidget(self._load_btn)
        self.main_layout.addLayout(splitters.SplitterLayout())

        scroll_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(scroll_widget)

        self._overrides_layout = QVBoxLayout()
        self._overrides_layout.setContentsMargins(1, 1, 1, 1)
        self._overrides_layout.setSpacing(0)
        self._overrides_layout.setAlignment(Qt.AlignTop)
        scroll_widget.setLayout(self._overrides_layout)
        self.main_layout.addWidget(scroll_area)

    def setup_signals(self):
        self._load_btn.clicked.connect(self._on_load_overrides)

    def get_loaded_overrides(self):
        """
        Returns all loaded overrides
        :return: list
        """

        return [ov.override for ov in self._loaded_overrides]

    def set_overrides(self, overrides):
        """
        self._setup_menubar()
        :param overrides: list
        :return:
        """

        self._overrides = overrides

    def _on_load_overrides(self):
        """
        Internal callback function that is called when Load Overrides button is clicked
        """

        overrides_dlg = QFileDialog(self)
        overrides_dlg.setDirectory(self._project.get_path())
        overrides_dlg.setFileMode(QFileDialog.ExistingFiles)

        override_pattern = ''
        for override_name, override in self._overrides.items():
            new_pattern = '{}(*{})'.format(override.OVERRIDE_NAME, override.OVERRIDE_EXTENSION)
            if override_pattern:
                override_pattern = ', {}'.fomrat(new_pattern)
            else:
                override_pattern = new_pattern
        overrides_dlg.setNameFilter(override_pattern)
        res = overrides_dlg.exec_()
        if not res:
            return

        override_files = overrides_dlg.selectedFiles()
        for override_file in override_files:
            try:
                with open(override_file, 'r') as f:
                    file_data = json.loads(f.read())
            except Exception as e:
                artellapipe.logger.error('Error while loading Override File: {} | {} | {}'.format(override_file, e, traceback.format_exc()))

            file_extension = os.path.splitext(override_file)[-1]
            if not file_extension:
                artellapipe.logger.warning('Impossible to load Override File: {}'.format(override_file))
                continue
            for override_name, override in self._overrides.items():
                if override.OVERRIDE_EXTENSION == file_extension:
                    new_override = override.create_from_data(project=self._project, data=file_data)
                    override_widget = ShotOverrideWidget(override=new_override)
                    self._overrides_layout.addWidget(override_widget)
                    self._loaded_overrides.append(override_widget)

    def _update_menu(self):
        pass
        # add_property_override = QAction('Property', self._overrides_menu)
        # add_shader_override = QAction('Shader', self._overrides_menu)
        # add_shader_property_override = QAction('Shader Property', self._overrides_menu)
        # add_box_bbox = QAction('Box Bounding Box', self._overrides_menu)
        # for action in [add_property_override, add_shader_override, add_shader_property_override, add_box_bbox]:
        #     self._overrides_menu.addAction(action)
        #
        # add_property_override.triggered.connect(self._on_add_property_override)
        # add_shader_override.triggered.connect(self._on_add_shader_override)
        # add_shader_property_override.triggered.connect(self._on_add_shader_property_override)
        # add_box_bbox.triggered.connect(self._on_add_area_curve_override)


class ShotOverrideWidget(base.BaseWidget, object):

    def __init__(self, override, parent=None):

        self._override = override

        super(ShotOverrideWidget, self).__init__(parent=parent)

    @property
    def override(self):
        return self._override

    def ui(self):
        super(ShotOverrideWidget, self).ui()

        self.setMouseTracking(True)

        self._item_widget = QFrame()
        self._item_layout = QGridLayout()
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_layout.setSpacing(0)
        self._item_widget.setLayout(self._item_layout)
        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self.setStyleSheet('background-color: rgb(45,45,45);')
        self.main_layout.addWidget(self._item_widget)

        icon_lbl = QLabel()
        icon_lbl.setMaximumWidth(18)
        icon_lbl.setPixmap(self._override.OVERRIDE_ICON.pixmap(self._override.OVERRIDE_ICON.actualSize(QSize(20, 20))))
        self._target_lbl = QLabel(self._override.OVERRIDE_NAME)
        self._editor_btn = QPushButton('Editor')
        self._editor_btn.setFlat(True)
        self._editor_btn.setIcon(artellapipe.resource.icon('editor'))
        self._save_btn = QPushButton()
        self._save_btn.setFlat(True)
        self._save_btn.setIcon(artellapipe.resource.icon('save'))
        self._delete_btn = QPushButton()
        self._delete_btn.setFlat(True)
        self._delete_btn.setIcon(artellapipe.resource.icon('delete'))

        self._item_layout.addWidget(icon_lbl, 0, 1, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 2, 1, 1)
        self._item_layout.addWidget(self._target_lbl, 0, 3, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 4, 1, 1)
        self._item_layout.addWidget(self._editor_btn, 0, 5, 1, 1)
        self._item_layout.setColumnStretch(6, 7)
        self._item_layout.addWidget(self._save_btn, 0, 8, 1, 1)
        self._item_layout.addWidget(self._delete_btn, 0, 9, 1, 1)

    def setup_signals(self):
        self._editor_btn.clicked.connect(self._on_open_override_editor)
        self._save_btn.clicked.connect(self._on_save_override)
        self._delete_btn.clicked.connect(self._on_remove_override)

    def _on_open_override_editor(self):
        """
        Internal callback function that is called when Editor button is pressed
        """

        pass
        # self._override.show_editor()

    def _on_save_override(self):
        """
        Internal callback function that is called when Save button is pressed
        """

        pass
        # return self._override.save()

    def _on_remove_override(self):
        """
        Internal callback function that is called when Remove button is pressed
        """

        pass

        # valid_remove = self._override.remove_from_node()
        # if valid_remove:
        #     self.removed.emit()
        #
        # return self._override