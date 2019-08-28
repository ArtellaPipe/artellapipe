#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Time Range Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

from artellapipe.tools.playblastmanager.core import plugin


class PanZoomWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to set playblast display settings
    """

    id = 'Pan/Zoom'

    def __init__(self, project, parent=None):
        super(PanZoomWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 0, 5, 0)

        return main_layout

    def ui(self):
        super(PanZoomWidget, self).ui()

        self.pan_zoom = QCheckBox('Use pan/zoom from camera')
        self.pan_zoom.setChecked(True)

        self.main_layout.addWidget(self.pan_zoom)

        self.pan_zoom.stateChanged.connect(self.optionsChanged)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        return {'pan_zoom': self.pan_zoom.isChecked()}

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        if not self.pan_zoom.isChecked():
            return {
                'camera_options': {
                    'panZoomEnabled': 1,
                    'horizontalPan': 0.0,
                    'verticalPan': 0.0,
                    'zoom': 1.0
                }
            }
        else:
            return {}

    def apply_inputs(self, attrs_dict):
        """
         Overrides base ArtellaPlayblastPlugin get_outputs function
         Returns the outputs variables of the Playblast widget as dict
         :return: dict
         """

        self.pan_zoom.setChecked(attrs_dict.get('pan_zoom', True))
