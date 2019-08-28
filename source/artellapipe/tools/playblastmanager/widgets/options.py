#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Viewport Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

import tpDccLib as tp

from artellapipe.tools.playblastmanager.core import plugin

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import gui


class PlayblastOptionsWidget(plugin.PlayblastPlugin, object):

    id = 'Options'
    label = 'Options'

    def __init__(self, project, parent=None):
        super(PlayblastOptionsWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(PlayblastOptionsWidget, self).ui()

        self.isolate_view = QCheckBox('Use isolate view from active panel')
        self.off_screen = QCheckBox('Render offscreen')

        for widget in [self.isolate_view, self.off_screen]:
            self.main_layout.addWidget(widget)

        self.widgets = {
            'off_screen': self.off_screen,
            'isolate_view': self.isolate_view
        }

        self.apply_inputs(self.get_defaults())

    def setup_signals(self):
        self.isolate_view.stateChanged.connect(self.optionsChanged)
        self.off_screen.stateChanged.connect(self.optionsChanged)

    def get_defaults(self):
        return {
            'off_screen': True,
            'isolate_view': False
        }

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        inputs = dict()
        for key, widget in self.widgets.items():
            state = widget.isChecked()
            inputs[key] = state

        return inputs

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        inputs = self.get_inputs(as_preset=False)
        outputs = dict()
        outputs['off_screen'] = inputs['off_screen']

        if inputs['isolate_view']:
            panel = gui.get_active_editor()
            filter_set = maya.cmds.modelEditor(panel, query=True, viewObjects=True)
            isolate = maya.cmds.sets(filter_set, query=True) if filter_set else None
            outputs['isolate'] = isolate

        return outputs

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin apply_inputs function
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        for key, w in self.widgets.items():
            state = attrs_dict.get(key, None)
            if state is not None:
                w.setChecked(state)

        return attrs_dict
