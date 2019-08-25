#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base definition for export list widgets
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpQtLib.core import base
from tpQtLib.widgets import button, search

import artellapipe


class BaseExportList(base.BaseWidget, object):

    itemClicked = Signal(object)
    refresh = Signal()

    def __init__(self, project, parent=None):

        self._project = project

        super(BaseExportList, self).__init__(parent=parent)

    def ui(self):
        super(BaseExportList, self).ui()

        self.setMouseTracking(True)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        self.main_layout.addLayout(top_layout)

        refresh_icon = artellapipe.resource.icon('refresh')
        self._refresh_btn = button.IconButton(refresh_icon, icon_padding=2, parent=self)
        self._refresh_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        top_layout.addWidget(self._refresh_btn)
        self._controls_filter = search.SearchFindWidget(parent=self)
        top_layout.addWidget(self._controls_filter)

        self._assets_list = BaseExportTree(parent=self)
        self.main_layout.addWidget(self._assets_list)

    def setup_signals(self):
        self._refresh_btn.clicked.connect(self._on_refresh_exporter)
        self._controls_filter.textChanged.connect(self._on_filter_assets_list)
        self._assets_list.itemSelectionChanged.connect(lambda: self.itemClicked.emit(self._assets_list.selectedItems()))

    def init_ui(self):
        """
        Function that is called during initialization
        Override in custom export lists
        """

        pass

    def clear_exporter_list(self):
        """
        Cleans all the items in the list
        """

        self._assets_list.clear()

    def refresh_exporter(self):
        """
        Function that refresh exporter data
        """

        self._refresh_exporter()

    def _on_filter_assets_list(self, filter_text):
        """
        This function is called each time the user enters text in the search line widget
        Shows or hides elements in the list taking in account the filter_text
        :param filter_text: str, current text
        """

        for i in range(self._assets_list.topLevelItemCount()):
            item = self._assets_list.topLevelItem(i)
            item.setHidden(filter_text not in item.text(0))

    def _on_refresh_exporter(self):
        """
        Internal callback function that is called when Refresh button is pressed by the user
        """

        self._refresh_exporter()

    def count(self):
        """
        Function that returns the total number of items in the list
        :return: int
        """

        root = self._assets_list.invisibleRootItem()
        return root.childCount()

    def item_at(self, index):
        """
        Function that returns item located in the given index
        :param index: int
        :return: Item
        """

        root = self._assets_list.invisibleRootItem()
        if index < 0 or index > self.count() - 1:
            return None

        return root.child(index)

    def asset_at(self, index):
        """
        Returns item wrapped asset located in the given index
        :param index: int
        :return: Asset
        """

        item = self.item_at(index)
        if not item:
            return None

        return item.asset_item

    def _refresh_exporter(self):
        """
        Internal function that refreshes exporter data
        """

        self.clear_exporter_list()
        self.init_ui()
        self.refresh.emit()


class BaseExportTree(QTreeWidget, object):
    def __init__(self, parent=None):
        super(BaseExportTree, self).__init__(parent=parent)

        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            '''
            QTreeView{alternate-background-color: #3b3b3b;}
            QTreeView::item {padding:3px;}
            QTreeView::item:!selected:hover {
                background-color: #5b5b5b;
                margin-left:-3px;
                border-left:0px;
            }
            QTreeView::item:selected {
                background-color: #48546a;
                border-left:2px solid #6f93cf;
                padding-left:2px;
            }
            QTreeView::item:selected:hover {
                background-color: #586c7a;
                border-left:2px solid #6f93cf;
                padding-left:2px;
            }
            '''
        )

    def mousePressEvent(self, event):
        item = self.indexAt(event.pos())
        selected = self.selectionModel().isSelected(item)
        super(BaseExportTree, self).mousePressEvent(event)
        if item.row() == -1 and item.column() == -1 or selected:
            self.clearSelection()
            index = QModelIndex()
            self.selectionModel().setCurrentIndex(index, QItemSelectionModel.Select)
