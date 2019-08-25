#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for exporter widgets
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import progressbar


class BaseExporter(base.BaseWidget, object):

    EXPORTER_NAME = ''
    EXPORTER_ICON = None
    EXPORTER_FILE = None
    EXPORTER_EXTENSION = None
    EXPORT_BUTTON_TEXT = 'Save'
    EXPORTER_LIST_WIDGET_CLASS = None
    EXPORTER_PROPERTIES_WIDGET_CLASS = None
    EXPORTER_TYPES = list()

    def __init__(self, project, parent=None):

        self._project = project

        super(BaseExporter, self).__init__(parent=parent)

        self._init()

    def ui(self):
        super(BaseExporter, self).ui()

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(main_splitter)

        self._export_list = self.EXPORTER_LIST_WIDGET_CLASS(project=self._project)
        self._properties_widget = self.EXPORTER_PROPERTIES_WIDGET_CLASS()
        main_splitter.addWidget(self._export_list)
        main_splitter.addWidget(self._properties_widget)

        self._progress = progressbar.ArtellaProgressBar(project=self._project)
        self._progress.setVisible(False)
        self.main_layout.addWidget(self._progress   )

        self._save_btn = QPushButton(str(self.EXPORT_BUTTON_TEXT))
        self._save_btn.setIcon(artellapipe.resource.icon('save'))
        self._save_btn.setMinimumHeight(30)
        self._save_btn.setMinimumWidth(100)
        save_layout = QHBoxLayout()
        save_layout.setContentsMargins(0, 0, 0, 0)
        save_layout.setSpacing(0)
        save_layout.addItem(QSpacerItem(15, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        save_layout.addWidget(self._save_btn)
        save_layout.addItem(QSpacerItem(15, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addLayout(save_layout)

    def setup_signals(self):
        self._export_list.itemClicked.connect(self._on_update_properties)
        self._save_btn.clicked.connect(self._on_save)

    def refresh(self):
        """
        Function that refresh exporter data
        :return:
        """
        self._export_list.refresh_exporter()

    def _init(self):
        """
        Function that initializes base exporter data
        """

        self._export_list.init_ui()

    def _on_update_properties(self, asset_widget):
        """
        Internal callback function that is called when an asset updates its properties
        :param asset_widget:
        :return:
        """
        if not asset_widget:
            return
        asset_widget = asset_widget[0]

        if asset_widget and tp.Dcc.object_exists(asset_widget.asset_item.name):
            self._properties_widget.update_attributes(asset_widget)
        else:
            artellapipe.logger.warning('Impossible to update properties because object {} does not exists!'.format(asset_widget.asset_item))
            self._properties_widget.clear_properties()

    def _on_clear_properties(self):
        """
        Internal callback function that is called when properties are clared
        """

        self._properties_widget.clear_properties()

    def _on_save(self):
        """
        Internal callback function that is called when save button is pressed
        Override in custom exports
        """

        pass
