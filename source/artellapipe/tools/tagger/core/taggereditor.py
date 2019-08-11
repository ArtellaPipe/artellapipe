#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core implementation for tagger editors
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *

from tpPyUtils import decorators

from tpQtLib.core import base

from artellapipe.tools.tagger.core import taggerutils


class TaggerEditor(base.BaseWidget, object):

    dataUpdated = Signal()

    EDITOR_TYPE = None

    def __init__(self, project, parent=None):

        self._project = project

        super(TaggerEditor, self).__init__(parent=parent)

    @property
    def project(self):
        """
        Returns project associated to this editor
        :return: ArtellaProject
        """

        return self._project

    @decorators.abstractmethod
    def initialize(self):
        """
        Initializes tagger editor
        """

        raise NotImplementedError('initialize() function not implemented in {}'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def update_tag_buttons_state(self, sel=None):
        """
        Updates the state of the tag buttons
        :param sel: list(str)
        """

        raise NotImplementedError('update_tag_buttons_state() function not implemented in {}'.format(self.__class__.__name__))

    @decorators.abstractmethod
    def fill_tag_node(self, tag_data_node, *args, **kwargs):
        """
        Fills given tag node with the data managed by this editor
        :param tag_data_node: str
        """

        raise NotImplementedError('fill_tag_node() function not implemented in {}'.format(self.__class__.__name__))

    def update_data(self, data=None, *args, **kwargs):
        """
        Update the data in the tag data node that is managed by this editor
        :param data: variant
        """

        sel = kwargs.pop('sel', None)

        tag_data_node = taggerutils.get_tag_data_node_from_current_selection(sel)
        if tag_data_node is None:
            return

        self.fill_tag_node(tag_data_node, data=data, *args, **kwargs)

        self.dataUpdated.emit()
