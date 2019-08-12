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


class OutlinerTree(base.BaseWidget, object):
    """
    Core class to create outliner widgets
    """

    ALLOWED_TYPES = None

    def __init__(self, project, parent=None):

        self._project = project
        self._widget_tree = defaultdict(list)
        self._widgets = list()

        super(OutlinerTree, self).__init__(parent=parent)

    @staticmethod
    def get_file_widget_by_category(category, parent=None):
        """
        Returns file widget by the given categoyr
        Overrides in specific outliners
        :param category: str
        :param parent:
        """

        return None

    def mousePressEvent(self, event):
        """
        Overrides BaseWidget mousePressEvent function
        :param event: QMouseEvent
        """

        if event.button() == Qt.LeftButton:
            tp.Dcc.clear_selection()

    def ui(self):
        super(OutlinerTree, self).ui()

        self.setMouseTracking(True)

        top_layout = QGridLayout()
        top_layout.setAlignment(Qt.AlignLeft)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self.main_layout.addLayout(top_layout)

        self._refresh_btn = QPushButton()
        self._refresh_btn.setIcon(artellapipe.resource.icon('refresh'))
        self._refresh_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._expand_all_btn = QPushButton()
        self._expand_all_btn.setIcon(artellapipe.resource.icon('expand'))
        self._expand_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._collapse_all_btn = QPushButton()
        self._collapse_all_btn.setIcon(artellapipe.resource.icon('collapse'))
        self._collapse_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        top_layout.addWidget(self._refresh_btn, 0, 0, 1, 1)
        top_layout.addWidget(self._expand_all_btn, 0, 1, 1, 1)
        top_layout.addWidget(self._collapse_all_btn, 0, 2, 1, 1)

        scroll_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(scroll_widget)

        self._outliner_layout = QVBoxLayout()
        self._outliner_layout.setContentsMargins(1, 1, 1, 1)
        self._outliner_layout.setSpacing(0)
        self._outliner_layout.addStretch()
        scroll_widget.setLayout(self._outliner_layout)
        self.main_layout.addWidget(scroll_area)

    def setup_signals(self):
        self._refresh_btn.clicked.connect(self._on_refresh_outliner)
        self._expand_all_btn.clicked.connect(self._on_expand_all_assets)
        self._collapse_all_btn.clicked.connect(self._on_collapse_all_assets)

    def append_widget(self, asset):
        """
        Adds a new outliner widget into it
        :param asset: OutlinerItem
        """

        self._widgets.append(asset)
        self._outliner_layout.insertWidget(0, asset)

    def remove_widget(self, asset):
        """
        Removes an outliner widget from it
        :param asset: OutlinerItem
        """

        raise NotImplementedError('remove_widget function is not implemente yet!')

    def clear_items(self):
        """
        Clears all the items in the outliner
        :return:
        """
        del self._widgets[:]
        while self._outliner_layout.count():
            child = self._outliner_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        self._outliner_layout.setSpacing(0)
        self._outliner_layout.addStretch()

    def refresh_outliner(self):
        """
        Refresh the items in the outliner
        """

        self._widget_tree = defaultdict(list)
        self.clear_items()
        self._init()
        can_expand = False
        for w in self._widgets:
            if w.expand_enable:
                can_expand = True
        if not can_expand:
            self._expand_all_btn.setVisible(False)
            self._collapse_all_btn.setVisible(False)

    def _init(self):
        """
        Internal callback function that initializes the outliner
        Overrides in custom outliners
        """

        pass

    def _on_refresh_outliner(self):
        """
        Internal callback function that is called when Refresh button is clicked
        :return:
        """

        self.refresh_outliner()

    def _on_expand_all_assets(self):
        """
        Internal callback function that is called when Expand button is clicked
        """

        for asset_widget in self._widget_tree.keys():
            asset_widget.expand()

    def _on_collapse_all_assets(self):
        """
        Internal callback function that is called when Collapse button is clicked
        """

        for asset_widget in self._widget_tree.keys():
            asset_widget.collapse()

    def _on_item_clicked(self, widget, event):
        if widget is None:
            artellapipe.solstice.logger.warning('Selected Asset is not valid!')
            return

        asset_name = widget.asset.name
        item_state = widget.is_selected
        if tp.Dcc.object_exists(asset_name):
            is_modified = event.modifiers() == Qt.ControlModifier
            if not is_modified:
                tp.Dcc.clear_selection()

            for asset_widget, file_items in self._widget_tree.items():
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
        for asset_widget, file_items in self._widget_tree.items():
            if '|{}'.format(asset_widget.asset.name) in selection:
                asset_widget.select()
            else:
                asset_widget.deselect()
