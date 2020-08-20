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

from tpDcc.libs.python import osplatform, python, path as path_utils

from tpDcc.libs.qt.core import base, qtutils, image
from tpDcc.libs.qt.widgets import layouts

import artellapipe
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
        """
        Function that opens shader file in user defined text editor
        :return: bool
        """

        shader_path = self.get_shader_path()
        if not os.path.isfile(shader_path):
            LOGGER.warning('Shader File "{}" does not exists!'.format(shader_path))
            return False

        osplatform.open_file(shader_path)

        return True

    def get_shader_path(self):
        """
        Returns path of the shader
        :return: str
        """

        shaders_extensions = artellapipe.ShadersMgr().get_shaders_extensions()
        if not shaders_extensions:
            return None

        for shader_extension in shaders_extensions:
            if not shader_extension.startswith('.'):
                shader_extension = '.{}'.format(shader_extension)

            shaders_paths = artellapipe.ShadersMgr().get_shaders_paths()
            for shaders_path in shaders_paths:
                shader_path = path_utils.clean_path(os.path.join(shaders_path, self._name + shader_extension))
                if not os.path.isfile(shader_path):
                    continue

                return shader_path

    def _load_shader_data(self):
        """
        Internal callback function that loads shader data and updates shader button with proper icon
        """

        shader_path = self.get_shader_path()
        if not shader_path or not os.path.isfile(shader_path):
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


class ShadersViewer(layouts.FlowLayout, object):

    SHADER_VIEWER_WIDGET_CLASS = ShaderViewerWidget

    def __init__(self, project, shaders_path=None, parent=None):
        self._shaders_path = shaders_path
        super(ShadersViewer, self).__init__(parent=parent)

        self._project = project

        # self.setHorizontalSpacing(0)
        # self.setVerticalSpacing(0)
        # self.setContentsMargins(0, 0, 0, 0)
        # self.setSpacing(0)

        self.refresh()

    def set_shaders_path(self, shaders_path):
        self._shaders_path = shaders_path
        self.refresh()

    def add_shader(self, widget):
        """
        Adds a new shader widget into the viewer
        :param widget: QWidget
        """

        self.addWidget(widget)

    def load_shader(self, shader_name):
        """
        Loads given shader name in current DCC
        :param shader_name: str
        """

        artellapipe.ShadersMgr().load_shader(shader_name=shader_name)

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

        shaders_extensions = artellapipe.ShadersMgr().get_shaders_extensions()
        if not shaders_extensions:
            return False

        for shader_extension in shaders_extensions:
            if not shader_extension.startswith('.'):
                shader_extension = '.{}'.format(shader_extension)

            if not self._shaders_path:
                shaders_library_paths = artellapipe.ShadersMgr().get_shaders_paths()
                if not shaders_library_paths:
                    LOGGER.warning('Current Project has no shaders paths defined!')
                    return False
            else:
                shaders_library_paths = python.force_list(self._shaders_path)

            valid_state = True

            invalid_paths = list()
            for shaders_path in shaders_library_paths:
                if not os.path.exists(shaders_path):
                    invalid_paths.append(shaders_path)
            if invalid_paths:
                result = qtutils.show_question(
                    None, 'Shaders Path not found!',
                    'Shaders Path is not sync! To start using this tool you should sync this folder first. '
                    'Do you want to do it?')
                if result == QMessageBox.Yes:
                    artellapipe.ShadersMgr().update_shaders(shaders_paths=invalid_paths)

            for shaders_path in invalid_paths:
                if not os.path.exists(shaders_path):
                    LOGGER.debug('Shader Library Path not found after sync. Something is wrong, please contact TD!')
                    valid_state = False

            if not valid_state:
                return False

            for shaders_path in shaders_library_paths:
                for shader_file in os.listdir(shaders_path):
                    if not shader_file.endswith(shader_extension):
                        LOGGER.warning(
                            'Shader File: "{}" has invalid shader extension! Skipping ...'.format(shader_file))
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
