#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core widgets for Solstice Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from collections import defaultdict

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base

import artellapipe


class BaseOutliner(base.BaseWidget, object):
    def __init__(self, parent=None):

        self.widget_tree = defaultdict(list)
        self.callbacks = list()
        self.widgets = list()

        super(BaseOutliner, self).__init__(parent=parent)

    @staticmethod
    def get_file_widget_by_category(category, parent=None):
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            tp.Dcc.clear_selection()

    def ui(self):
        super(BaseOutliner, self).ui()

        self.setMouseTracking(True)

        self.top_layout = QGridLayout()
        self.top_layout.setAlignment(Qt.AlignLeft)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(2)
        self.main_layout.addLayout(self.top_layout)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(artellapipe.resource.icon('refresh'))
        self.refresh_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.expand_all_btn = QPushButton()
        self.expand_all_btn.setIcon(artellapipe.resource.icon('expand'))
        self.expand_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.collapse_all_btn = QPushButton()
        self.collapse_all_btn.setIcon(artellapipe.resource.icon('collapse'))
        self.collapse_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.top_layout.addWidget(self.refresh_btn, 0, 0, 1, 1)
        self.top_layout.addWidget(self.expand_all_btn, 0, 1, 1, 1)
        self.top_layout.addWidget(self.collapse_all_btn, 0, 2, 1, 1)

        scroll_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(scroll_widget)

        self.outliner_layout = QVBoxLayout()
        self.outliner_layout.setContentsMargins(1, 1, 1, 1)
        self.outliner_layout.setSpacing(0)
        self.outliner_layout.addStretch()
        scroll_widget.setLayout(self.outliner_layout)
        self.main_layout.addWidget(scroll_area)

    def setup_signals(self):
        self.refresh_btn.clicked.connect(self._on_refresh_outliner)
        self.expand_all_btn.clicked.connect(self._on_expand_all_assets)
        self.collapse_all_btn.clicked.connect(self._on_collapse_all_assets)

    def init_ui(self):
        pass

    def allowed_types(self):
        return None

    def add_callbacks(self):
        pass

    def remove_callbacks(self):
        for c in self.callbacks:
            try:
                self.callbacks.remove(c)
                del c
            except Exception as e:
                artellapipe.solstice.logger.error('Impossible to clean callback {}'.format(c))
                artellapipe.solstice.logger.error(str(e))

        self.callbacks = list()
        self.scrip_jobs = list()

    def append_widget(self, asset):
        self.widgets.append(asset)
        self.outliner_layout.insertWidget(0, asset)

    def remove_widget(self, asset):
        pass

    def clear_outliner_layout(self):
        del self.widgets[:]
        while self.outliner_layout.count():
            child = self.outliner_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        self.outliner_layout.setSpacing(0)
        self.outliner_layout.addStretch()

    def refresh_outliner(self):
        self._on_refresh_outliner()

    def _on_refresh_outliner(self, *args):
        self.widget_tree = defaultdict(list)
        self.clear_outliner_layout()
        self.init_ui()
        can_expand = False
        for w in self.widgets:
            if w.expand_enable:
                can_expand = True
        if not can_expand:
            self.expand_all_btn.setVisible(False)
            self.collapse_all_btn.setVisible(False)


    def _on_expand_all_assets(self):
        for asset_widget in self.widget_tree.keys():
            asset_widget.expand()

    def _on_collapse_all_assets(self):
        for asset_widget in self.widget_tree.keys():
            asset_widget.collapse()

    def _on_item_clicked(self, widget, event):
        if widget is None:
            artellapipe.solstice.logger.warning('Selected Asset is not valid!')
            artellapipe

        asset_name = widget.asset.name
        item_state = widget.is_selected
        if tp.Dcc.object_exists(asset_name):
            is_modified = event.modifiers() == Qt.ControlModifier
            if not is_modified:
                tp.Dcc.clear_selection()

            for asset_widget, file_items in self.widget_tree.items():
                if asset_widget != widget:
                    continue
                if is_modified and widget.is_selected:
                    tp.Dcc.select_object(asset_widget.asset.name, add=True)
                else:
                    asset_widget.deselect()
                    tp.Dcc.select_object(asset_widget.asset.name, deselect=True)

            widget.set_select(item_state)
            if not is_modified:
                tp.Dcc.select_object(asset_name)
        else:
            self._on_refresh_outliner()

    def _on_selection_changed(self, *args):
        selection = tp.Dcc.selected_nodes(full_path=True)
        for asset_widget, file_items in self.widget_tree.items():
            if '|{}'.format(asset_widget.asset.name) in selection:
                asset_widget.select()
            else:
                asset_widget.deselect()
