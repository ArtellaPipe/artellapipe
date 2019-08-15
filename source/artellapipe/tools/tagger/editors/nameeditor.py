#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for name editor
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtWidgets import *

import tpDccLib as tp

from artellapipe.tools.tagger.core import taggereditor, taggerutils


class NameEditor(taggereditor.TaggerEditor, object):

    EDITOR_TYPE = 'Name'

    def __init__(self, project, parent=None):
        super(NameEditor, self).__init__(project=project, parent=parent)

    def ui(self):
        super(NameEditor, self).ui()

        name_lbl = QLabel('Name: ')
        self._name_line = QLineEdit()
        self.main_layout.addWidget(name_lbl)
        self.main_layout.addWidget(self._name_line)

    def setup_signals(self):
        self._name_line.textChanged.connect(partial(self.update_data, None))

    def initialize(self):
        """
        Initializes tagger editor
        """

        pass

    def update_tag_buttons_state(self, sel=None):
        """
        Updates the selection tag attribute of the tag data node
        :param name: str, name of the selection tag to add/remove
        """

        tag_data_node = taggerutils.get_tag_data_node_from_current_selection(sel)
        if tag_data_node is None:
            return

        attr_exists = tp.Dcc.attribute_exists(node=tag_data_node, attribute_name='name')
        if attr_exists:
            name = tp.Dcc.get_attribute_value(node=tag_data_node, attribute_name='name')
            if name is not None and name != '':
                self._name_line.setText(name)

    def fill_tag_node(self, tag_data_node, *args, **kwargs):
        """
        Fills given tag node with the data managed by this editor
        :param tag_data_node: str
        """

        attr_exists = tp.Dcc.attribute_exists(node=tag_data_node, attribute_name='name')
        if not attr_exists:
            tp.Dcc.add_string_attribute(node=tag_data_node, attribute_name='name')

        tp.Dcc.unlock_attribute(node=tag_data_node, attribute_name='name')
        tp.Dcc.set_string_attribute_value(node=tag_data_node, attribute_name='name', attribute_value=self._name_line.text())
        tp.Dcc.lock_attribute(node=tag_data_node, attribute_name='name')
