#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class that defines mixin class for any widget that inherits from QAbstractItemView class
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *


# class ExporterItemViewMixin(object):
#     def __init__(self, *args):
#         self._hover_item = None
#         self._mouse_press_button = None
#         self._current_item = None
#         self._current_selection = list()
#
#     def mouse_press_button(self):
#         """
#         Returns the mouse button that has been pressed
#         :return: Qt.MouseButton
#         """
#
#         return self._mouse_press_button
#
#     def selectionChanged(self, selected, deselected):
#         """
#         Triggered when the current item has been selected or deselected
#         :param selected: QItemSelection
#         :param deselected: QItemSelection
#         """
#
#         selected_items_ = self.selectedItems()
#         if self._current_selection != selected_items_:
#             self._current_selection = selected_items_
#             indexes1 = selected.indexes()
#             selected_items = self.items_from_indexes(indexes1)
#             indexes2 = deselected.indexes()
#             deselected_items = self.items_from_indexes(indexes2)
#             items = selected_items + deselected_items
#             for item in items:
#                 item.selectionChanged()
#
#         QAbstractItemView.selectionChanged(self, selected, deselected)
#
#     def wheelEvent(self, event):
#         """
#         Triggered on any wheel events for the current viewport
#         :param event: QWheelEvent
#         """
#
#         if self.is_control_modifier():
#             event.ignore()
#         else:
#             QAbstractItemView.wheelEvent(self, event)
#
#         item = self.itemAt(event.pos())
#         self.itemUpdateEvent(item, event)
#
#     def keyPressEvent(self, event):
#         """
#         Triggered on user key press events for the current viewport
#         :param event: QKeyEvent
#         """
#
#         item = self.selectedItem()
#         if item:
#             self.itemKeyPressEvent(item, event)
#
#         valid_keys = [
#             Qt.Key_Up,
#             Qt.Key_Left,
#             Qt.Key_Down,
#             Qt.Key_Right
#         ]
#
#         if event.isAccepted():
#             if event.key() in valid_keys:
#                 QAbstractItemView.keyPressEvent(self, event)
#
#     def mousePressEvent(self, event):
#         """
#         Triggered on user mouse press events for the current viewport
#         :param event: QMouseEvent
#         """
#
#         self._mouse_press_button = event.button()
#         item = self.itemAt(event.pos())
#         if item:
#             self.itemMousePressEvent(item, event)
#
#     def mouseReleaseEvent(self, event):
#         """
#         Triggered on user mouse release events for the current viewport
#         :param event: QMouseEvent
#         """
#
#         self._mouse_press_button = None
#         item = self.selectedItem()
#         if item:
#             self.itemMouseReleaseEvent(item, event)
#
#     def mouseMoveEvent(self, event):
#         """
#         Triggered on user mouse move evente for the current viewport
#         :param event: QMouseEvent
#         """
#
#         if self._mouse_press_button == Qt.MiddleButton:
#             item = self.selectedItem()
#         else:
#             item = self.itemAt(event.pos())
#
#         self.itemUpdateEvent(item, event)
#
#     def leaveEvent(self, event):
#         """
#         Triggered when the mouse leaves the widget
#         :param event: QMouseEvent
#         """
#
#         if self._mouse_press_button != Qt.MiddleButton:
#             self.itemUpdateEvent(None, event)
#
#         QAbstractItemView.leaveEvent(self, event)
#
#     def itemUpdateEvent(self, item, event):
#         """
#         Triggered on user key press events for the current viewport
#         :param item: ExporterItem
#         :param event: QKeyEvent
#         """
#
#         self.clean_dirty_objects()
#         if id(self._current_item) != id(item):
#             if self._current_item:
#                 self.itemMouseLeaveEvent(self._current_item, event)
#                 self._current_item = None
#             if item and not self._current_item:
#                 self._current_item = item
#                 self.itemMouseEnterEvent(item, event)
#
#         if self._current_item:
#             self.itemMouseMoveEvent(item, event)
#
#     def itemMouseEnterEvent(self, item, event):
#         """
#         Triggered when the mouse enters the given item
#         :param item: QTreeWidgetItem
#         :param event: QMouseEvent
#         """
#
#         item.mouseEnterEvent(event)
#
#     def itemMouseLeaveEvent(self, item, event):
#         """
#         Triggered when the mouse leaves the given item
#         :param item: QTreeWidgetItem
#         :param event: QMouseEvent
#         """
#
#         item.mouseReleaseEvent(event)
#
#     def itemMouseMoveEvent(self, item, event):
#         """
#         Triggered when the mouse moves within the given item
#         :param item: QTreeWidgetItem
#         :param event: QMouseEvent
#         """
#
#         item.mouseMoveEvent(event)
#
#     def itemMousePressEvent(self, item, event):
#         """
#         Triggered when the mouse is pressed on the given item
#         :param item: QTreeWidgetItem
#         :param event: QMouseEvent
#         """
#
#         item.mousePressEvent(event)
#
#     def itemMouseReleaseEvent(self, item, event):
#         """
#         Triggered when the mouse is released on the given item
#         :param item: QTreeWidgetItem
#         :param event: QMouseEvent
#         """
#
#         item.mouseReleaseEvent(event)
#
#     def itemKeyPressEvent(self, item, event):
#         """
#         Triggered when a key is pressed for the selected item
#         :param item: QTreeWidgetItem
#         :param event: QKeyEvent
#         """
#
#         item.keyPressEvent(event)
#
#     def itemKeyReleaseEvent(self, item, event):
#         """
#         Triggered when a key is released for the selected item
#         :param item: QTreeWidgetItem
#         :param event: QKeyEvent
#         """
#
#         item.keyReleaseEvent(event)
#
#     def clean_dirty_objects(self):
#         """
#         Removes any object that may have been deleted
#         """
#
#         if self._current_item:
#             try:
#                 self._current_item.text(0)
#             except RuntimeError:
#                 self._hover_item = None
#                 self._current_item = None
#                 self._current_selection = None
#
#     def items_widget(self):
#         """
#         Returns True if a control modifiers is currently active or False otherwise
#         :return: bool
#         """
#
#         return self.parent()
#
#     def is_control_modifier(self):
#         """
#         Returns True if a control modifiers is currently active or False otherwise
#         :return: bool
#         """
#
#         modifiers = QApplication.keyboardModifiers()
#         is_alt_modifier = modifiers == Qt.AltModifier
#         is_ctrl_modifier = modifiers == Qt.ControlModifier
#
#         return is_alt_modifier or is_ctrl_modifier
#
#     def items_from_indexes(self, indexes):
#         """
#         Returns a list of TreeWidgetItems associated with the given indexes
#         :param indexes: list(QModelIndex)
#         :return: list(QTreeWidgetItem)
#         """
#
#         items = dict()
#         for index in indexes:
#             item = self.itemFromIndex(index)
#             items[id(item)] = item
#
#         return items.values()
