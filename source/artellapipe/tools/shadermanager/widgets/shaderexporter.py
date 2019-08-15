#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Shader Exporter
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import traceback
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDccLib as tp

import artellapipe
from artellapipe.utils import shader as shader_utils

if tp.is_maya():
    from tpMayaLib.core import shader as maya_shader


class ArtellaShaderExportSplash(QSplashScreen, object):
    def __init__(self, *args, **kwargs):
        super(ArtellaShaderExportSplash, self).__init__(*args, **kwargs)

        self.mousePressEvent = self.MousePressEvent
        self._canceled = False

    def MousePressEvent(self, event):
        pass


class ArtellaShaderExporterWidget(QWidget, object):
    def __init__(self, shader_name, layout='horizontal', parent=None):
        super(ArtellaShaderExporterWidget, self).__init__(parent=parent)

        self._name = shader_name

        if layout == 'horizontal':
            main_layout = QHBoxLayout()
        else:
            main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        main_layout.setAlignment(Qt.AlignLeft)
        self.setLayout(main_layout)

        if tp.Dcc.objExists(shader_name):
            self._shader_swatch = maya_shader.get_shader_swatch(self._name)
            main_layout.addWidget(self._shader_swatch)

            if layout == 'horizontal':
                v_div_w = QWidget()
                v_div_l = QVBoxLayout()
                v_div_l.setAlignment(Qt.AlignLeft)
                v_div_l.setContentsMargins(0, 0, 0, 0)
                v_div_l.setSpacing(0)
                v_div_w.setLayout(v_div_l)
                v_div = QFrame()
                v_div.setMinimumHeight(30)
                v_div.setFrameShape(QFrame.VLine)
                v_div.setFrameShadow(QFrame.Sunken)
                v_div_l.addWidget(v_div)
                main_layout.addWidget(v_div_w)

        shader_lbl = QLabel(shader_name)
        main_layout.addWidget(shader_lbl)
        if layout == 'vertical':
            main_layout.setAlignment(Qt.AlignCenter)
            shader_lbl.setAlignment(Qt.AlignCenter)
            shader_lbl.setStyleSheet('QLabel {background-color: rgba(50, 50, 50, 200); border-radius:5px;}')
            shader_lbl.setStatusTip(self.name)
            shader_lbl.setToolTip(self.name)

        do_export_layout = QVBoxLayout()
        do_export_layout.setAlignment(Qt.AlignCenter)
        self.do_export = QCheckBox()
        self.do_export.setChecked(True)
        do_export_layout.addWidget(self.do_export)
        main_layout.addLayout(do_export_layout)

    def export(self, publish=False):

        if self.do_export.isChecked():
            shader_library_path = self._project.get_shaders_path()
            if not os.path.exists(shader_library_path):
                artellapipe.logger.debug('Shader Library {0} not found! Aborting shader export! Contact TD!'.format(shader_library_path))
                return

            if not tp.Dcc.object_exists(self._name):
                artellapipe.logger.debug('Shader {0} does not exists in the scene! Aborting shader export!'.format(self._name))
                return

            px = QPixmap(QSize(100, 100))
            self._shader_swatch.render(px)
            temp_file = os.path.join(shader_library_path, 'tmp.png')
            px.save(temp_file)
            try:
                network = shader_utils.ShadingNetwork.write_network(shaders_path=shader_library_path, shaders=[self._name], icon_path=temp_file, publish=publish)
                exported_shaders = network
            except Exception as e:
                artellapipe.logger.debug('Aborting shader export: {0}'.format(str(e)))
                os.remove(temp_file)
                return
            os.remove(temp_file)

            return exported_shaders
        else:
            return None

    @property
    def name(self):
        return self._name


class ShaderExporter(QDialog, object):

    SPLASH_FILE_NAME = 'shaders_splash'

    exportFinished = Signal()

    def __init__(self, project, shaders, parent=None):

        self._project = project

        super(ShaderExporter, self).__init__(parent=parent)

        self.setWindowTitle('Solstice Tools - Shader Exporter')

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        splash_pixmap = self._project.resource.pixmap(self.SPLASH_FILE_NAME)
        splash = ArtellaShaderExportSplash(splash_pixmap)
        self._splash_layout = QVBoxLayout()
        self._splash_layout.setAlignment(Qt.AlignBottom)
        splash.setLayout(self._splash_layout)
        self.main_layout.addWidget(splash)

        shaders_layout = QVBoxLayout()
        shaders_layout.setAlignment(Qt.AlignBottom)
        self._splash_layout.addLayout(shaders_layout)
        self._shaders_list = QListWidget()
        self._shaders_list.setMaximumHeight(170)
        self._shaders_list.setFlow(QListWidget.LeftToRight)
        self._shaders_list.setSelectionMode(QListWidget.NoSelection)
        self._shaders_list.setStyleSheet('background-color: rgba(50, 50, 50, 150);')
        shaders_layout.addWidget(self._shaders_list)

        self.export_btn = QPushButton('Export')
        self.publish_btn = QPushButton('Export and Publish')
        self.cancel_btn = QPushButton('Cancel')
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.publish_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.setAlignment(Qt.AlignBottom)
        self._splash_layout.addLayout(buttons_layout)

        progress_layout = QHBoxLayout()
        self._splash_layout.addLayout(progress_layout)

        self._progress_text = QLabel('Exporting and uploading shaders to Artella ... Please wait!')
        self._progress_text.setAlignment(Qt.AlignCenter)
        self._progress_text.setStyleSheet("QLabel { background-color : rgba(0, 0, 0, 180); color : white; }")
        self._progress_text.setVisible(False)
        font = self._progress_text.font()
        font.setPointSize(10)
        self._progress_text.setFont(font)

        progress_layout.addWidget(self._progress_text)

        for shader in shaders:
            if shader in shader_utils.IGNORE_SHADERS:
                continue
            shader_item = QListWidgetItem()
            shader_widget = ArtellaShaderExporterWidget(shader_name=shader, layout='vertical')
            shader_item.setSizeHint(QSize(120, 120))
            shader_widget.setMinimumWidth(100)
            shader_widget.setMinimumHeight(100)
            self._shaders_list.addItem(shader_item)
            self._shaders_list.setItemWidget(shader_item, shader_widget)

        self.export_btn.clicked.connect(partial(self._on_export_shaders, False))
        self.publish_btn.clicked.connect(partial(self._on_export_shaders, True))
        self.cancel_btn.clicked.connect(self.close)

        self.setFixedSize(splash_pixmap.size())

    def export_shaders(self, publish=False):

        exported_shaders = list()

        if self._shaders_list.count() <= 0:
            artellapipe.logger.error('No Shaders To Export. Aborting ....')
            return exported_shaders

        try:
            for i in range(self._shaders_list.count()):
                shader_item = self._shaders_list.item(i)
                shader = self._shaders_list.itemWidget(shader_item)
                self._progress_text.setText('Exporting shader: {0} ... Please wait!'.format(shader.name))
                self.repaint()
                exported_shader = shader.export(publish=publish)
                if exported_shader is not None:
                    if type(exported_shader) == list:
                        exported_shaders.extend(exported_shader)
                    else:
                        exported_shaders.append(exported_shader)
                else:
                    artellapipe.logger.error('Error while exporting shader: {}'.format(shader.name))
        except Exception as e:
            artellapipe.logger.error(str(e))
            artellapipe.logger.error(traceback.format_exc())

        return exported_shaders

    def _on_export_shaders(self, publish=False):
        self.cancel_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.publish_btn.setVisible(False)
        self._progress_text.setVisible(True)
        self.repaint()
        self.export_shaders(publish=publish)
        self.exportFinished.emit()
        artellapipe.logger.debug('Shaders exported successfully!')
        self.close()
