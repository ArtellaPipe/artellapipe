#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for type editor
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import grid

from artellapipe.tools.tagger.core import taggereditor, taggerutils


class TypeEditor(taggereditor.TaggerEditor, object):

    EDITOR_TYPE = 'Type'

    def __init__(self, project, parent=None):
        super(TypeEditor, self).__init__(project=project, parent=parent)

    def ui(self):
        super(TypeEditor, self).ui()

        self._type_grid = grid.GridWidget()
        self._type_grid.setShowGrid(False)
        self._type_grid.setColumnCount(4)
        self._type_grid.horizontalHeader().hide()
        self._type_grid.verticalHeader().hide()
        self._type_grid.resizeRowsToContents()
        self._type_grid.resizeColumnsToContents()
        self.main_layout.addWidget(self._type_grid)

    def initialize(self):
        self._type_grid.clear()

        tag_types = self._project.tag_types
        for tag_type in tag_types:
            tag_widget = TaggerTypeWidget(type_title=tag_type)
            tag_widget._btn.toggled.connect(partial(self.update_data, tag_widget.get_name()))
            self._type_grid.add_widget_first_empty_cell(tag_widget)

    def update_tag_buttons_state(self, sel=None):
        """
        Updates the type tag attribute of the tag data node
        :param name: str, name of the type tag to add/remove
        """

        tag_data_node = taggerutils.get_tag_data_node_from_current_selection(sel)
        if tag_data_node is None:
            return

        self.set_tag_widgets_state(False)

        attr_exists = tp.Dcc.attribute_exists(node=tag_data_node, attribute_name='types')
        if attr_exists:
            types = tp.Dcc.get_attribute_value(node=tag_data_node, attribute_name='types')
            if types is not None and types != '':
                types = types.split()
                for t in types:
                    for i in range(self._type_grid.columnCount()):
                        for j in range(self._type_grid.rowCount()):
                            container_w = self._type_grid.cellWidget(j, i)
                            if container_w is not None:
                                tag_w = container_w.containedWidget
                                tag_name = tag_w.get_name()
                                if tag_name == t:
                                    tag_w._btn.blockSignals(True)
                                    tag_w._btn.setChecked(True)
                                    tag_w._btn.blockSignals(False)

    def fill_tag_node(self, tag_data_node, *args, **kwargs):
        """
        Fills given tag node with the data managed by this editor
        :param tag_data_node: str
        """

        attr_exists = tp.Dcc.attribute_exists(node=tag_data_node, attribute_name='types')
        if not attr_exists:
            tp.Dcc.add_string_attribute(node=tag_data_node, attribute_name='types')

        data = kwargs.get('data', None)

        types = tp.Dcc.get_attribute_value(node=tag_data_node, attribute_name='types')
        if args and args[0]:
            if types is None or types == '':
                types = data
            else:
                types_split = types.split()
                if data in types_split:
                    return
                types_split.append(data)
                types = ''.join(str(e) + ' ' for e in types_split)

            tp.Dcc.unlock_attribute(node=tag_data_node, attribute_name='types')
            tp.Dcc.set_string_attribute_value(node=tag_data_node, attribute_name='types', attribute_value=types)
            tp.Dcc.lock_attribute(node=tag_data_node, attribute_name='types')
        else:
            if types is None or types == '':
                return
            types_split = types.split()
            if data in types_split:
                types_split.remove(data)
            else:
                return
            types = ''.join(str(e) + ' ' for e in types_split)

            tp.Dcc.unlock_attribute(node=tag_data_node, attribute_name='types')
            tp.Dcc.set_string_attribute_value(node=tag_data_node, attribute_name='types', attribute_value=types)
            tp.Dcc.lock_attribute(node=tag_data_node, attribute_name='types')

    def set_tag_widgets_state(self, state=False):
        """
        Disables/Enables all tag buttons on the grid layout
        :param state: bool
        """

        for i in range(self._type_grid.columnCount()):
            for j in range(self._type_grid.rowCount()):
                container_w = self._type_grid.cellWidget(j, i)
                if container_w is not None:
                    tag_w = container_w.containedWidget
                    tag_w._btn.blockSignals(True)
                    tag_w._btn.setChecked(state)
                    tag_w._btn.blockSignals(False)


class TaggerTypeWidget(base.BaseWidget, object):
    def __init__(self, type_title, parent=None):

        self._type_title_name = type_title
        self._type_name = type_title.replace(' ', '_').lower()

        super(TaggerTypeWidget, self).__init__(parent=parent)

    def ui(self):
        super(TaggerTypeWidget, self).ui()

        self._btn = QPushButton(self._type_title_name)
        self._btn.setCheckable(True)
        self.main_layout.addWidget(self._btn)

        type_lbl = QLabel(self._type_title_name)
        type_lbl.setAlignment(Qt.AlignCenter)
        # main_layout.addWidget(type_lbl)

    def get_name(self):
        """
        Returns type name of the tagger widget
        :return: str
        """

        return self._type_name
