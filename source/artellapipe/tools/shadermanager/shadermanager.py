# -*- coding: utf-8 -*-

"""
Tool to export/import shader files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

from artellapipe.core import assetsviewer, shadersviewer
from artellapipe.gui import window


class ShaderManager(window.ArtellaWindow, object):

    LOGO_NAME = 'shadermanager_logo'

    ASSETS_VIEWER_CLASS = assetsviewer.CategorizedAssetViewer

    def __init__(self, project):
        super(ShaderManager, self).__init__(
            project=project,
            name='ArtellaAlembicManager',
            title='Shader Manager',
            size=(1400, 800)
        )

        self._init()

    def ui(self):
        super(ShaderManager, self).ui()

        # self.main_layout.setAlignment(Qt.AlignTop)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        top_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(top_layout)

        top_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self._export_sel_btn = QToolButton()
        self._export_sel_btn.setText('Export Selected Materials')
        self._export_sel_btn.setMinimumWidth(40)
        self._export_sel_btn.setMinimumHeight(40)
        top_layout.addWidget(self._export_sel_btn)
        self._export_all_btn = QToolButton()
        self._export_all_btn.setText('Export All Scene Materials')
        self._export_all_btn.setMinimumWidth(40)
        self._export_all_btn.setMaximumHeight(40)
        top_layout.addWidget(self._export_all_btn)
        self._sync_shaders_btn = QToolButton()
        self._sync_shaders_btn.setText('Sync Shaders from Artella')
        self._sync_shaders_btn.setMinimumWidth(40)
        self._sync_shaders_btn.setMaximumHeight(40)
        top_layout.addWidget(self._sync_shaders_btn)
        self._open_shaders_path_btn = QToolButton()
        self._open_shaders_path_btn.setText('Open Shaders Library Path')
        self._open_shaders_path_btn.setMinimumWidth(40)
        self._open_shaders_path_btn.setMaximumHeight(40)
        top_layout.addWidget(self._open_shaders_path_btn)

        top_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        # ===========================================================================================

        shader_splitter = QSplitter(Qt.Horizontal)
        shader_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(shader_splitter)

        shader_widget = QWidget()
        shader_scroll = QScrollArea()
        shader_scroll.setWidgetResizable(True)
        shader_scroll.setWidget(shader_widget)
        self.shader_viewer = shadersviewer.ShaderViewer(project=self._project, grid_size=2)
        shader_scroll.setMinimumWidth(900)
        self.shader_viewer.setAlignment(Qt.AlignTop)
        shader_widget.setLayout(self.shader_viewer)

        self._assets_viewer = self.ASSETS_VIEWER_CLASS(
            project=self._project,
            column_count=2,
            parent=self
        )
        self._assets_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # self._asset_viewer.setMinimumWidth(420)
        shader_splitter.addWidget(self._assets_viewer)
        shader_splitter.addWidget(shader_scroll)

    def setup_signals(self):
        pass
        # self._export_sel_btn.clicked.connect(self._export_selected_shaders)
        # self._export_all_btn.clicked.connect(self._export_all_shaders)
        # self._sync_shaders_btn.clicked.connect(self.update_shaders_from_artella)
        # self._open_shaders_path_btn.clicked.connect(self._open_shaders_path)

    def _init(self):
        """
        Internal function that checks shaders library validity and initializes shaders viewer properly
        :return:
        """

def run(project):
    win = ShaderManager(project=project)
    win.show()

    return win
