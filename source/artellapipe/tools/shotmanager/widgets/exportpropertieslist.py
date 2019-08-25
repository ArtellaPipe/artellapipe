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

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import attributes

import artellapipe


class BaseAttributeWidget(base.BaseWidget, object):

    toggled = Signal(str, bool)

    def __init__(self, node, attr_name, attr_widget, attr_value=None, parent=None):

        self._node = node
        self._attr_name = attr_name
        self._attr_widget = attr_widget

        super(BaseAttributeWidget, self).__init__(parent=parent)

        # if attr_value:
        #     self.set_value(attr_value)

    def ui(self):
        super(BaseAttributeWidget, self).ui()

        self._item_widget = QFrame()
        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self._item_widget.setStyleSheet('QFrame { background-color: rgb(55,55,55);}')
        self._item_layout = QHBoxLayout()
        self._item_layout.setAlignment(Qt.AlignLeft)
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_widget.setLayout(self._item_layout)
        self.main_layout.addWidget(self._item_widget)
        self._item_layout.addWidget(self._attr_widget)

        self.setMinimumHeight(25)

    def setup_signals(self):
        self._attr_widget.cbx.toggled.connect(self._on_toggle_cbx)

    @property
    def name(self):
        """
        Returns name of the attribute
        :return: str
        """

        return self._attr_name

    @property
    def node(self):
        """
        Returns wrapped asset node of the attribute
        :return:
        """

        return self._node

    @property
    def attribute_editor(self):
        """
        Returns linked attribute editor of the attribute
        :return: BaseEditor
        """

        return self._attr_widget

    def check(self):
        """
        Checks the attribute
        """

        self._attr_widget.cbx.blockSignals(False)
        self._attr_widget.cbx.setChecked(True)
        self._attr_widget.cbx.blockSignals(True)

    def uncheck(self):
        """
        Unchecks the attribute
        """

        self._attr_widget.cbx.blockSignals(False)
        self._attr_widget.cbx.setChecked(False)
        self._attr_widget.cbx.blockSignals(True)

    # def set_value(self, value):
    #     pass
    #
    # def hide_check(self):
    #     self.attr_cbx.hide()
    #

    # def toggle(self):
    #     self.attr_cbx.blockSignals(True)
    #     self.attr_cbx.setChecked(not self.attr_cbx.isChecked())
    #     self.attr_cbx.blockSignals(False)
    #
    # def lock(self):
    #     if self.attr_widget:
    #         self.attr_widget.setEnabled(False)
    #
    # def unlock(self):
    #     if self.attr_widget:
    #         self.attr_widget.setEnabled(True)

    def _on_toggle_cbx(self, flag):
        """
        Internal callback function that is called when checkbox is toggled
        :param flag: bool
        """

        self.toggled.emit(self.name, flag)


class BasePropertiesListWidget(attributes.AttributeEditor, object):
    def __init__(self, name, label, title, parent=None):

        self._current_asset = None

        super(BasePropertiesListWidget, self).__init__(
            name=name,
            label=label,
            parent=parent
        )

        self.set_title(title)

    def get_attributes_layout(self):
        """
        Overrides base AttributeEditor get_attributes_layout function
        :return: QLayout
        """

        attributes_layout = QGridLayout()
        attributes_layout.setContentsMargins(5, 5, 5, 5)
        attributes_layout.setAlignment(Qt.AlignTop)

        return attributes_layout

    def update_attributes(self, asset_widget):
        """
        Function that updates all the attributes in the properties list
        :param asset_widget: QWidget
        """

        if asset_widget.asset_item == self._current_asset:
            return

        self.clear_layout(reset_title=False)

        self._current_asset = asset_widget.asset_item

        xform_attrs = tp.Dcc.list_attributes(asset_widget.asset_item.name)
        for attr in xform_attrs:
            new_attr = self.add_attribute(attr)
            if self._current_asset.attrs[new_attr.name] is True:
                new_attr.check()
            else:
                new_attr.uncheck()

    def add_attribute(self, attr_name):
        """
        Adds a new attribute into the properties list
        :param attr_name:
        :return:
        """
        if not self._current_asset:
            return

        new_attr = attributes.map_widget(attr_type='bool', name=attr_name)
        attr_widget = BaseAttributeWidget(node=self._current_asset, attr_name=attr_name, attr_widget=new_attr)

        current_rows = self._main_group_layout.rowCount()
        attr_lbl = QLabel(attr_name)
        self._main_group_layout.addWidget(attr_lbl, current_rows, 0, 1, 1, Qt.AlignRight)
        self._main_group_layout.addWidget(attr_widget, current_rows, 1)

        attr_widget.toggled.connect(self._on_update_attribute)

        return attr_widget

#     def all_attributes(self):
#         """
#         Returns all the attributes widgets in the properties list
#         :return: list(QWidget)
#         """
#
#         all_attrs = list()
#         while self._props_layout.count():
#             child = self._props_layout.takeAt(0)
#             if child.widget() is not None:
#                 all_attrs.append(child.widget())
#
#         return all_attrs
#
#     def clear_properties(self):
#         """
#         Clears all the properties in the properties list
#         """
#
#         del self.widgets[:]
#         while self._props_layout.count():
#             child = self._props_layout.takeAt(0)
#             if child.widget() is not None:
#                 child.widget().deleteLater()
#         self._props_layout.setSpacing(0)
#         self._props_layout.addStretch()
#
    def _on_update_attribute(self, attr_name, flag):
        """
        Internal callback function that is called when an attribute is updated
        :param attr_name: str
        :param flag: bool
        """

        if not self._current_asset:
            return

        if attr_name not in self._current_asset.attrs.keys():
            artellapipe.logger.warning('Impossible to udpate attribute {} because node {} has no that attribute!'.format(attr_name, self._current_asset.asset_item))
            return

        self._current_asset.attrs[attr_name] = flag
