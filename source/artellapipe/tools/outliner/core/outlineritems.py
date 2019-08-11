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

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpQtLib.core import base


class OutlinerItemWidget(base.BaseWidget, object):

    clicked = Signal(QObject, QEvent)
    doubleClicked = Signal()
    contextRequested = Signal(QObject, QAction)

    def __init__(self, name, parent=None):

        self.parent = parent
        self.long_name = name
        self.name = name.split('|')[-1]
        self.block_callbacks = False
        self.is_selected = False

        super(OutlinerItemWidget, self).__init__(parent=parent)

    def ui(self):
        super(OutlinerItemWidget, self).ui()

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.item_widget = QFrame()
        self.item_layout = QGridLayout()
        self.item_layout.setContentsMargins(0, 0, 0, 0)
        self.item_widget.setLayout(self.item_layout)
        self.main_layout.addWidget(self.item_widget)


class OutlinerTreeItemWidget(OutlinerItemWidget, object):
    def __init__(self, name, parent=None):

        self.parent_elem = None
        self.child_elem = dict()

        super(OutlinerTreeItemWidget, self).__init__(name=name, parent=parent)

    def ui(self):
        super(OutlinerTreeItemWidget, self).ui()

        self.child_widget = QWidget()
        self.child_layout = QVBoxLayout()
        self.child_layout.setContentsMargins(0, 0, 0, 0)
        self.child_layout.setSpacing(0)
        self.child_widget.setLayout(self.child_layout)
        self.main_layout.addWidget(self.child_widget)

    def add_child(self, widget, category):
        widget.parent_elem = self
        self.child_elem[category] = widget
        self.child_layout.addWidget(widget)


class OutlinerAssetItem(OutlinerTreeItemWidget, object):

    clicked = Signal(QObject, QEvent)

    def __init__(self, asset, parent=None):

        self.asset = asset
        self.parent = parent
        self.expand_enable = True

        super(OutlinerAssetItem, self).__init__(asset.get_short_name(), parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_selected:
                self.deselect()
            else:
                self.select()
            self.clicked.emit(self, event)

    def contextMenuEvent(self, event):
        if not self.is_selected:
            self.select()

        menu = QMenu(self)
        menu.setStyleSheet('background-color: rgb(68,68,68);')
        menu = self.create_menu(menu)
        action = menu.exec_(self.mapToGlobal(event.pos()))
        self.contextRequested.emit(self, action)

    def ui(self):
        super(OutlinerAssetItem, self).ui()

        self.item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self.item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

        icon = QIcon()
        icon.addPixmap(QPixmap(':/nudgeDown.png'), QIcon.Normal, QIcon.On)
        icon.addPixmap(QPixmap(':/nudgeRight.png'), QIcon.Normal, QIcon.Off);
        self.expand_btn = QPushButton()
        self.expand_btn.setStyleSheet("QPushButton#expand_btn:checked {background-color: green; border: none}")
        self.expand_btn.setStyleSheet("QPushButton { color:white; } QPushButton:checked { background-color: rgb(55,55, 55); border: none; } QPushButton:pressed { background-color: rgb(55,55, 55); border: none; }")  # \
        self.expand_btn.setFlat(True)
        self.expand_btn.setIcon(icon)
        self.expand_btn.setCheckable(True)
        self.expand_btn.setChecked(True)
        self.expand_btn.setFixedWidth(25)
        self.expand_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.item_layout.addWidget(self.expand_btn, 0, 0, 1, 1)

        self.asset_buttons = self.get_display_widget()
        if self.asset_buttons:
            self.item_layout.addWidget(self.asset_buttons, 0, 1, 1, 1)
        else:
            self.expand_btn.setVisible(False)

        pixmap = self.get_pixmap()
        self.icon_lbl = QLabel()
        self.icon_lbl.setMaximumWidth(18)
        self.icon_lbl.setPixmap(pixmap)
        self.asset_lbl = QLabel(self.name)

        self.item_layout.setColumnStretch(1, 5)
        self.item_layout.setAlignment(Qt.AlignLeft)

        if self.asset_buttons:
            self.item_layout.addWidget(self.icon_lbl, 0, 2, 1, 1)
            self.item_layout.addWidget(self.asset_lbl, 0, 3, 1, 1)
            self.expand_enable = True
        else:
            self.item_layout.addWidget(self.icon_lbl, 0, 1, 1, 1)
            self.item_layout.addWidget(self.asset_lbl, 0, 2, 1, 1)
            self.expand_enable = False

        self.collapse()

    def setup_signals(self):
        self.expand_btn.clicked.connect(self._on_toggle_children)
        if self.asset_buttons:
            self.asset_buttons.view_btn.toggled.connect(partial(self.viewToggled.emit, self))

    def get_display_widget(self):
        return None

    def get_pixmap(self):
        return QPixmap(':/pickGeometryObj.png')

    def create_menu(self, menu):
        return menu

    def get_file_widget(self, category):
        return self.child_elem.get(category)

    def expand(self):
        self.expand_btn.setChecked(True)
        self._on_toggle_children()

    def collapse(self):
        self.expand_btn.setChecked(False)
        self._on_toggle_children()

    def select(self):
        pass
        # self.is_selected = True
        # self.item_widget.setStyleSheet('QFrame { background-color: rgb(21,60,97);}')

    def deselect(self):
        self.is_selected = False
        self.item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')

    def set_select(self, select=False):
        if select:
            self.select()
        else:
            self.deselect()

        return self.is_selected

    def _on_toggle_children(self):
        state = self.expand_btn.isChecked()
        self.child_widget.setVisible(state)


class OutlinerFileItem(OutlinerTreeItemWidget, object):
    def __init__(self, category, parent=None):
        super(OutlinerFileItem, self).__init__(name=category, parent=parent)

    @staticmethod
    def get_category_pixmap():
        return QPixmap(':/out_particle.png')

    def ui(self):
        super(OutlinerFileItem, self).ui()

        self.setMouseTracking(True)

        self.item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self.setStyleSheet('background-color: rgb(68,68,68);')

        pixmap = self.get_category_pixmap()
        icon_lbl = QLabel()
        icon_lbl.setMaximumWidth(18)
        icon_lbl.setPixmap(pixmap)
        self.item_layout.addWidget(icon_lbl, 0, 1, 1, 1)

        self.target_lbl = QLabel(self.name.title())
        self.item_layout.addWidget(self.target_lbl, 0, 2, 1, 1)
