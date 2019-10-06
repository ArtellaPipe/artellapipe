#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for shaders viewer
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpPyUtils import osplatform, path as path_utils

from tpQtLib.core import base, qtutils, image

from artellapipe.utils import shader as shader_utils

LOGGER = logging.getLogger()


class ShaderViewerWidget(base.BaseWidget, object):

    clicked = Signal()

    def __init__(self, project, shader_name, parent=None):

        self._project = project
        self._name = shader_name
        self._menu = None

        super(ShaderViewerWidget, self).__init__(parent=parent)

        self._load_shader_data()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)

        return main_layout

    def ui(self):
        super(ShaderViewerWidget, self).ui()

        self.setMinimumHeight(140)

        self.main_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self._shader_btn = QPushButton()
        self._shader_btn.setMinimumWidth(110)
        self._shader_btn.setMaximumHeight(110)
        self._shader_btn.setMaximumWidth(110)
        self._shader_btn.setMinimumHeight(110)
        self._shader_btn.setIconSize(QSize(100, 100))
        shader_lbl = QLabel(self._name)
        shader_lbl.setAlignment(Qt.AlignCenter)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        self.main_layout.addLayout(button_layout)
        button_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        button_layout.addWidget(self._shader_btn)
        button_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.main_layout.addWidget(shader_lbl)

    def setup_signals(self):
        self._shader_btn.clicked.connect(self.clicked.emit)

    def contextMenuEvent(self, event):
        self._generate_context_menu()
        if not self._menu:
            return
        self._menu.exec_(event.globalPos())

    def open_shader_in_editor(self):
        osplatform.open_file(self.shader_path)

    def get_shader_path(self):
        """
        Returns path of the shader
        :return: str
        """

        shaders_path = self._project.get_shaders_path()
        shaders_extension = str(self._project.shaders_extension)
        if not shaders_extension.startswith('.'):
            shaders_extension = '.{}'.format(shaders_extension)

        return path_utils.clean_path(os.path.join(shaders_path, self._name + shaders_extension))

    def _load_shader_data(self):
        """
        Internal callback function that loads shader data and updates shader button with proper icon
        """

        shader_path = self.get_shader_path()
        if not os.path.isfile(shader_path):
            LOGGER.warning('Shader Data Path {0} for shader {1} is not valid!'.format(shader_path, self._name))
            return

        shader_data = shader_utils.ShadingNetwork.read(shader_path)
        shader_icon = shader_data['icon']
        if not shader_icon:
            return
        shader_icon = shader_icon.encode('utf-8')
        self._shader_btn.setIcon(QPixmap.fromImage(image.base64_to_image(shader_icon)))

    def _generate_context_menu(self):
        self._menu = QMenu(self)
        open_in_editor = self._menu.addAction('Open Shader in external editor')
        self._menu.addAction(open_in_editor)

        open_in_editor.triggered.connect(self.open_shader_in_editor)


class ShaderViewer(QGridLayout, object):

    SHADER_VIEWER_WIDGET_CLASS = ShaderViewerWidget

    def __init__(self, project, grid_size=4, parent=None):
        super(ShaderViewer, self).__init__(parent)

        self._project = project
        self._grid_size = grid_size

        self.setHorizontalSpacing(0)
        self.setVerticalSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

        self.refresh()

    def add_shader(self, widget):
        """
        Adds a new shader widget into the viewer
        :param widget: QWidget
        """

        row = 0
        col = 0
        while self.itemAtPosition(row, col) is not None:
            if col == self._grid_size - 1:
                row += 1
                col = 0
            else:
                col += 1
        self.addWidget(widget, row, col)

    def load_shader(self, shader_name):
        """
        Loads given shader name in current DCC
        :param shader_name: str
        """

        shader_utils.load_shader(project=self._project, shader_name=shader_name)

    def clear(self):
        """
        Clears all shader widgets from the viewer
        """

        for i in range(self.count(), -1, -1):
            item = self.itemAt(i)
            if item is None:
                continue
            item.widget().setParent(None)
            self.removeItem(item)

    def refresh(self):
        """
        Refresh shaders data
        """

        self.clear()

        valid_state = True
        shaders_library_path = self._project.get_shaders_path()
        if not os.path.exists(shaders_library_path):
            result = qtutils.show_question(
                None, 'Shaders Library Path not found!',
                'Shaders Library Path is not sync! To start using this tool you should sync this folder first. '
                'Do you want to do it?')
            if result == QMessageBox.Yes:
                self._project.update_shaders()
                if not os.path.exists(shaders_library_path):
                    LOGGER.debug('Shader Library Path not found after sync. Something is wrong, please contact TD!')
                    valid_state = False
            else:
                valid_state = False

        if not valid_state:
            return

        shaders_extension = self._project.shaders_extension
        if not shaders_extension:
            LOGGER.warning('Current Project Shaders Extension: "{}" is not valid!'.format(shaders_extension))
            return
        if not shaders_extension.startswith('.'):
            shaders_extension = '.{}'.format(shaders_extension)

        for shader_file in os.listdir(shaders_library_path):
            if not shader_file.endswith(shaders_extension):
                LOGGER.warning('Shader File: "{}" has invalid shader extension! Skipping ...'.format(shader_file))
                continue
            shader_name = os.path.splitext(shader_file)[0]
            shader_widget = self.SHADER_VIEWER_WIDGET_CLASS(project=self._project, shader_name=shader_name)
            shader_widget.clicked.connect(partial(self._on_shader_widget_clicked, shader_name))
            self.add_shader(shader_widget)

    def _on_shader_widget_clicked(self, shader_name):
        """
        Internal callback function that is called whe na shader widget is clicked by the user
        :param shader_name: str
        """

        self.load_shader(shader_name=shader_name)
