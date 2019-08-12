#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains outliner item core widgets
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpQtLib.core import base

import artellapipe


class OutlinerTreeItemWidget(base.BaseWidget, object):

    clicked = Signal(QObject, QEvent)
    doubleClicked = Signal()
    contextRequested = Signal(QObject, QAction)

    def __init__(self, name, parent=None):

        self._parent = parent
        self._long_name = name
        self._name = name.split('|')[-1]
        self._block_callbacks = False
        self._is_selected = False
        self._parent_elem = None
        self._child_elem = dict()

        super(OutlinerTreeItemWidget, self).__init__(parent=parent)

    def ui(self):
        super(OutlinerTreeItemWidget, self).ui()

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self._item_widget = QFrame()
        self._item_layout = QGridLayout()
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_widget.setLayout(self._item_layout)
        self.main_layout.addWidget(self._item_widget)

        self._child_widget = QWidget()
        self.child_layout = QVBoxLayout()
        self.child_layout.setContentsMargins(0, 0, 0, 0)
        self.child_layout.setSpacing(0)
        self._child_widget.setLayout(self.child_layout)
        self.main_layout.addWidget(self._child_widget)

    def add_child(self, widget, category):
        widget.parent_elem = self
        self._child_elem[category] = widget
        self.child_layout.addWidget(widget)


class OutlinerAssetItem(OutlinerTreeItemWidget, object):

    ICON_NAME = 'teapot'
    DISPLAY_BUTTONS = None

    clicked = Signal(QObject, QEvent)

    def __init__(self, asset_node, parent=None):

        self._asset_node = asset_node
        self._expand_enable = True
        self._display_buttons = None

        super(OutlinerAssetItem, self).__init__(name=asset_node.get_short_name(), parent=parent)

    @property
    def asset_node(self):
        """
        Returns wrapped asset node
        :return: ArtellaAssetNode
        """

        return self._asset_node

    @property
    def expand_enable(self):
        """
        Returns whether children are expanded or not
        :return: bool
        """

        return self._expand_enable

    def mousePressEvent(self, event):
        """
        Overrides base OutlinerTreeItemWidget mousePressEvent function
        :param event: QMouseEvent
        """

        if event.button() == Qt.LeftButton:
            if self.is_selected:
                self.deselect()
            else:
                self.select()
            self.clicked.emit(self, event)

    def contextMenuEvent(self, event):
        """
        Overrides base OutlinerTreeItemWidget contextMenuEvent function
        :param event: QMouseEvent
        """

        if not self.is_selected:
            self.select()

        menu = QMenu(self)
        menu.setStyleSheet('background-color: rgb(68,68,68);')
        self._create_menu(menu)
        action = menu.exec_(self.mapToGlobal(event.pos()))
        self.contextRequested.emit(self, action)

    def ui(self):
        super(OutlinerAssetItem, self).ui()

        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

        icon = QIcon()
        icon.addPixmap(QPixmap(':/nudgeDown.png'), QIcon.Normal, QIcon.On)
        icon.addPixmap(QPixmap(':/nudgeRight.png'), QIcon.Normal, QIcon.Off);
        self._expand_btn = QPushButton()
        self._expand_btn.setStyleSheet("QPushButton#expand_btn:checked {background-color: green; border: none}")
        self._expand_btn.setStyleSheet("QPushButton { color:white; } QPushButton:checked { background-color: rgb(55,55, 55); border: none; } QPushButton:pressed { background-color: rgb(55,55, 55); border: none; }")  # \
        self._expand_btn.setFlat(True)
        self._expand_btn.setIcon(icon)
        self._expand_btn.setCheckable(True)
        self._expand_btn.setChecked(True)
        self._expand_btn.setFixedWidth(25)
        self._expand_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self._item_layout.addWidget(self._expand_btn, 0, 0, 1, 1)

        if self.DISPLAY_BUTTONS:
            self._display_buttons = self.DISPLAY_BUTTONS()
            self._item_layout.addWidget(self._display_buttons, 0, 1, 1, 1)
        else:
            self._expand_btn.setVisible(False)

        project_icon = self._asset_node.project.resource.icon(self.ICON_NAME)
        if project_icon.isNull():
            project_icon = artellapipe.resource.icon(self.ICON_NAME)
        pixmap = project_icon.pixmap(project_icon.availableSizes()[-1]).scaled(20, 20, Qt.KeepAspectRatio)
        self._icon_lbl = QLabel()
        self._icon_lbl.setMaximumWidth(18)
        self._icon_lbl.setPixmap(pixmap)
        self._asset_lbl = QLabel(self._name)

        self._item_layout.setColumnStretch(1, 5)
        self._item_layout.setAlignment(Qt.AlignLeft)

        if self._display_buttons:
            self._item_layout.addWidget(self._icon_lbl, 0, 2, 1, 1)
            self._item_layout.addWidget(self._asset_lbl, 0, 3, 1, 1)
            self._expand_enable = True
        else:
            self._item_layout.addWidget(self._icon_lbl, 0, 1, 1, 1)
            self._item_layout.addWidget(self._asset_lbl, 0, 2, 1, 1)
            self._expand_enable = False

        self.collapse()

    def setup_signals(self):
        self._expand_btn.clicked.connect(self._on_toggle_children)
        if self._display_buttons:
            self._display_buttons.view_btn.toggled.connect(partial(self.viewToggled.emit, self))

    def get_file_widget(self, category):
        """
        Returns the widget with the given category
        :param category: str
        :return: QWidget
        """

        return self._child_elem.get(category)

    def expand(self):
        """
        Expands all the children items of the current item
        """

        self._expand_btn.setChecked(True)
        self._toggle_children()

    def collapse(self):
        """
        Collapses all the children items of the current item
        :return:
        """
        self._expand_btn.setChecked(False)
        self._toggle_children()

    def select(self):
        """
        Selects wrapped DCC node in DCC viewport
        """

        pass
        # self.is_selected = True
        # self.item_widget.setStyleSheet('QFrame { background-color: rgb(21,60,97);}')

    def deselect(self):
        """
        Deselects wrapped DCC node from DCC viewport
        """

        self._is_selected = False
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

    def set_select(self, select=False):
        """
        Sets whether wrapped DCC node is selected or not
        :param select: bool
        """

        if select:
            self.select()
        else:
            self.deselect()

        return self.is_selected

    def _create_menu(self, menu):
        """
        Internal function that creates contextual menu of the item
        Overrides to create custom context menu
        :param menu: QMenu
        :return:
        """

        pass

    def _toggle_children(self):
        """
        Toggles all children widgets
        """

        state = self._expand_btn.isChecked()
        self._child_widget.setVisible(state)

    def _on_toggle_children(self):
        """
        Internal callback function that is called when expand button is clicked
        """

        self._toggle_children()


class OutlinerFileItem(OutlinerTreeItemWidget, object):
    def __init__(self, category, parent=None):
        super(OutlinerFileItem, self).__init__(name=category, parent=parent)

    @staticmethod
    def get_category_pixmap():
        return QPixmap(':/out_particle.png')

    def ui(self):
        super(OutlinerFileItem, self).ui()

        self.setMouseTracking(True)

        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self.setStyleSheet('background-color: rgb(68,68,68);')

        pixmap = self.get_category_pixmap()
        icon_lbl = QLabel()
        icon_lbl.setMaximumWidth(18)
        icon_lbl.setPixmap(pixmap)
        self._item_layout.addWidget(icon_lbl, 0, 1, 1, 1)

        self.target_lbl = QLabel(self._name.title())
        self._item_layout.addWidget(self.target_lbl, 0, 2, 1, 1)
