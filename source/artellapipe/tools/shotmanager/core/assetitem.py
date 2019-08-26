#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base definition for property list widgets
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

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.tools.shotmanager.core import defines


class ExporterAssetItem(QObject):

    clicked = Signal(QObject, QEvent)
    contextRequested = Signal(QObject, QAction)

    def __init__(self, asset_node):
        super(ExporterAssetItem, self).__init__()

        self._asset_node = asset_node
        self._attrs = dict()

        self._update_attrs()

    @property
    def asset_node(self):
        return self._asset_node

    @property
    def name(self):
        return self._asset_node.name

    @property
    def short_name(self):
        return self._asset_node.get_short_name()

    @property
    def path(self):
        return self._asset_node.asset_path

    @property
    def attrs(self):
        return self._attrs

    def _update_attrs(self):
        """
        Internal function that updates the attributes of the item
        """

        if self._attrs:
            return

        xform_attrs = tp.Dcc.list_attributes(self._asset_node.name)
        for attr in xform_attrs:
            if attr in defines.MUST_ATTRS:
                self._attrs[attr] = True
            else:
                self._attrs[attr] = False


class AbstractItemWidget(base.BaseWidget, object):

    clicked = Signal(QObject, QEvent)
    contextRequested = Signal(QObject, QAction)

    def __init__(self, asset_file, parent=None):

        self._asset_file = asset_file
        self._is_selectable = True
        self._is_selected = False

        super(AbstractItemWidget, self).__init__(parent)

    def ui(self):
        super(AbstractItemWidget, self).ui()

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumHeight(35)
        self.setMaximumHeight(35)

        self._item_widget = QFrame()
        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')
        self._item_layout = QGridLayout()
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_widget.setLayout(self._item_layout)
        self.main_layout.addWidget(self._item_widget)

    @property
    def asset_file(self):
        """
        Returns asset file of this item
        :return:
        """

        return self._asset_file

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_selected:
                self.deselect()
            else:
                self.select()
            self.clicked.emit(self, event)

    def select(self):
        """
        Selects current item
        """

        if not self._is_selectable:
            return

        self._is_selected = True
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(21,60,97);}')

    def deselect(self):
        """
        Deselects current item
        """

        if not self._is_selectable:
            return

        self._is_selected = False
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

    def set_select(self, select=False):
        """
        Sets wether the item is selected or not
        :param select: bool
        """

        if not self._is_selectable:
            return

        if select:
            self.select()
        else:
            self.deselect()

        return self._is_selected


class ShotAssetItem(AbstractItemWidget, object):
    def __init__(self, asset_file, type=None, parent=None):

        self._type = type

        super(ShotAssetItem, self).__init__(asset_file=asset_file, parent=parent)

    def ui(self):
        super(ShotAssetItem, self).ui()

        self._asset_icon = QLabel()
        self._type_icon = QLabel()
        self._asset_lbl = QLabel(os.path.basename(self._asset_file))
        self._asset_lbl.setToolTip(self._asset_file)

        self._item_layout.addWidget(self._asset_icon, 0, 1, 1, 1)
        self._item_layout.addWidget(self._type_icon, 0, 2, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 3, 1, 1)
        self._item_layout.addWidget(self._asset_lbl, 0, 4, 1, 1)

        self._item_layout.setColumnStretch(5, 6)
        self._item_layout.setAlignment(Qt.AlignLeft)

        if self._type:
            item_icon = self._get_type_icon()
            self._type_icon.setPixmap(item_icon.pixmap(item_icon.actualSize(QSize(20, 20))))

    def set_icon(self, item_icon):
        """
        Sets the icon used by the item
        :param item_icon: QIcon
        """

        self._asset_icon.setPixmap(item_icon.pixmap(item_icon.actualSize(QSize(20, 20))))

    def load(self):
        """
        Function that loads item into current DCC scene
        Overrides in cusotm classes
        """

        pass

    def _get_type_icon(self):
        """
        Internal function that returns the icon depending of the asset file type being used
        :return: QIcon
        """

        return None


class ShotAssetFileItem(AbstractItemWidget, object):

    FILE_TYPE = None
    FILE_ICON = None
    FILE_EXTENSION = None

    def __init__(self, asset_file, asset_data=None, extra_data=None, parent=None):

        self._asset_data = asset_data
        self._extra_data = extra_data

        super(ShotAssetFileItem, self).__init__(asset_file=asset_file, parent=parent)

    def ui(self):
        super(ShotAssetFileItem, self).ui()

        self._asset_icon = QLabel()
        self._asset_icon.setPixmap(self.FILE_ICON.pixmap(self.FILE_ICON.actualSize(QSize(20, 20))))
        self._asset_lbl = QLabel(os.path.basename(self._asset_file))
        self._asset_lbl.setToolTip(self._asset_file)

        self._item_layout.addWidget(self._asset_icon, 0, 1, 1, 1)
        self._item_layout.addWidget(self._asset_lbl, 0, 2, 1, 1)

        self._item_layout.setColumnStretch(2, 5)
        self._item_layout.setAlignment(Qt.AlignLeft)

    def get_data(self):
        """
        Returns data of the current asset file
        Override in custom file types
        :return: dict
        """

        if self._asset_data:
            return self._asset_data

        try:
            with open(self._asset_file) as f:
                asset_data = json.load(f)
        except Exception as e:
            artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))
            return dict()

        return asset_data

    def get_nodes(self):
        """
        Returns nodes that are stored inside asset file
        :return: list
        """

        return list()
