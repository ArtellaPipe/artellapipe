#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Display Options Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import  contextlib

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.widgets import color

from artellapipe.tools.playblastmanager.core import defines, plugin

if tp.is_maya():
    import tpMayaLib as maya


@contextlib.contextmanager
def applied_display_options(options):
    """
    Context manager for setting background color display options
    :param options: dict
    """

    options = dict(defines.DisplayOptions, **(options or {}))
    colors = ['background', 'backgroundTop', 'backgroundBottom']
    preferences = ['displayGradient']
    original = dict()

    for clr in colors:
        original[clr] = maya.cmds.displayRGBColor(clr, query=True) or list()
    for preference in preferences:
        original[preference] = maya.cmds.displayPref(query=True, **{preference: True})
    for clr in colors:
        value = options[clr]
        maya.cmds.displayRGBColor(clr, *value)
    for preference in preferences:
        value = options[preference]
        maya.cmds.displayPref(**{preference: value})

    try:
        yield
    finally:
        for clr in colors:
            maya.cmds.displayRGBColor(clr, *original[clr])
        for preference in preferences:
            maya.cmds.displayPref(**{preference: original[preference]})


class DisplayOptionsWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to set playblast display settings
    """

    id = 'Display Options'

    BACKGROUND_DEFAULT = [0.6309999823570251, 0.6309999823570251, 0.6309999823570251]
    TOP_DEFAULT = [0.5350000262260437, 0.6169999837875366, 0.7020000219345093]
    BOTTOM_DEFAULT = [0.052000001072883606, 0.052000001072883606, 0.052000001072883606]
    COLORS = {"background": BACKGROUND_DEFAULT,
              "backgroundTop": TOP_DEFAULT,
              "backgroundBottom": BOTTOM_DEFAULT}
    LABELS = {"background": "Background",
              "backgroundTop": "Top",
              "backgroundBottom": "Bottom"}

    def __init__(self, project, parent=None):

        self._colors = dict()

        super(DisplayOptionsWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(DisplayOptionsWidget, self).ui()

        self.override = QCheckBox('Override Display Options')

        self.display_type = QComboBox()
        self.display_type.addItems(['Solid', 'Gradient'])

        self._color_layout = QHBoxLayout()
        for lbl, default in self.COLORS.items():
            self._add_color_picker(self._color_layout, lbl, default)

        self.main_layout.addWidget(self.override)
        self.main_layout.addWidget(self.display_type)
        self.main_layout.addLayout(self._color_layout)

        self._on_toggle_override()

        self.override.toggled.connect(self._on_toggle_override)
        self.override.toggled.connect(self.optionsChanged)
        self.display_type.currentIndexChanged.connect(self.optionsChanged)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        inputs = {'override_display': self.override.isChecked()}
        for lbl, w in self._colors.items():
            inputs[lbl] = w.color

        return inputs

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        outputs = dict()

        if not tp.is_maya():
            return outputs

        if self.override.isChecked():
            outputs['displayGradient'] = self.display_gradient()
            for lbl, w in self._colors.items():
                outputs[lbl] = w.color
        else:
            outputs['displayGradient'] = maya.cmds.displayPref(query=True, displayGradient=True)
            for key in self.COLORS.keys():
                clr = maya.cmds.displayRGBColor(key, query=True)
                outputs[key] = clr

        return {'display_options': outputs}

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin apply_inputs function
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        for lbl, w in self._colors.items():
            default = self.COLORS.get(lbl, [0, 0, 0])
            value = attrs_dict.get(lbl, default)
            w.color = value

        override = attrs_dict.get('override_display', False)
        self.override.setChecked(override)

    def display_gradient(self):
        """
        Returns whether the background should be displayed as gradient
        If True, the colors will use the top and bottom colors to define
        the gradient otherwise the background color will be used as solid color
        :return: bool, True if background is gradient, False otherwise
        """

        return self.display_type.currentText() == 'Gradient'

    def _add_color_picker(self, layout, label, default):
        """
        Internal function that creates a picker with a label and a button to select a color
        :param layout: QLayout, layout to add color picker to
        :param label: str, systen name for the color type (egp: backgorundTop)
        :param default: list, default color to start with
        :return: solstice_color.ColorPicker
        """

        l = QVBoxLayout()
        lbl = QLabel(self.LABELS[label])
        color_picker = color.ColorPicker()
        color_picker.color = default
        l.addWidget(lbl)
        l.addWidget(color_picker)
        l.setAlignment(lbl, Qt.AlignCenter)
        layout.addLayout(l)
        color_picker.valueChanged.connect(self.optionsChanged)
        self._colors[label] = color_picker

        return color_picker

    def _on_toggle_override(self):
        """
        Internal function that is called when override is toggled
        Enable or disabled the color pickers and background type widgets bases on the current state of the override
        checkbox
        """

        state = self.override.isChecked()
        self.display_type.setEnabled(state)
        for w in self._colors.values():
            w.setEnabled(state)
