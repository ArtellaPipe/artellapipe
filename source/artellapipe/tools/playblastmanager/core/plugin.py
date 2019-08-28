#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base implementation for Playblast Plugins
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import python

from tpQtLib.core import base


class PlayblastPlugin(base.BaseWidget, object):

    id = 'DefaultPlayblastPlugin'

    label = ''
    labelChanged = Signal(str)
    optionsChanged = Signal()

    def __init__(self, project, parent=None):

        self._project = project

        super(PlayblastPlugin, self).__init__(parent=parent)

    def __str__(self):
        return self.label or type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    id = python.classproperty(lambda cls: cls.__name__)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        return main_layout

    def validate(self):
        """
        Will ensure that widget outputs are valid and will raise proper errors if necessary
        :return: list<str>
        """

        return list()

    def initialize(self):
        """
        Method used to initialize callbacks on widget
        """

        pass

    def uninitialize(self):
        """
        Un-register any callback created when deleting the widget
        """

        pass

    def get_outputs(self):
        """
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        return {}

    def get_inputs(self, as_preset=False):
        """
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        return {}

    def apply_inputs(self, attrs_dict):
        """
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        pass

    def on_playblast_finished(self, options):
        """
        Internal callback function that is called when a Playblast is generated
        :param options: dict
        """

        pass
