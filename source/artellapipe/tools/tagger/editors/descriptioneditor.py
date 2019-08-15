#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for description editor
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


class DescriptionEditor(taggereditor.TaggerEditor, object):

    EDITOR_TYPE = 'Description'

    def __init__(self, project, parent=None):
        super(DescriptionEditor, self).__init__(project=project, parent=parent)

    def ui(self):
        super(DescriptionEditor, self).ui()

        self._description_text = QTextEdit()
        self.main_layout.addWidget(self._description_text)

    def setup_signals(self):
        self._description_text.textChanged.connect(partial(self.update_data, None))

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

        attr_exists = tp.Dcc.attribute_exists(node=tag_data_node, attribute_name='description')
        if attr_exists:
            description = tp.Dcc.get_attribute_value(node=tag_data_node, attribute_name='description')
            if description is not None and description != '':
                self._description_text.setText(description)

    def fill_tag_node(self, tag_data_node, *args, **kwargs):
        """
        Fills given tag node with the data managed by this editor
        :param tag_data_node: str
        """

        attr_exists = tp.Dcc.attribute_exists(node=tag_data_node, attribute_name='description')
        if not attr_exists:
            tp.Dcc.add_string_attribute(node=tag_data_node, attribute_name='description')

        tp.Dcc.unlock_attribute(node=tag_data_node, attribute_name='description')
        tp.Dcc.set_string_attribute_value(node=tag_data_node, attribute_name='description', attribute_value=self._description_text.toPlainText())
        tp.Dcc.lock_attribute(node=tag_data_node, attribute_name='description')
