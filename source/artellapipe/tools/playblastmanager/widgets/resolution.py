#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Resolution Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import math
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from artellapipe.tools.playblastmanager.core import plugin


class ScaleSettings(object):
    SCALE_WINDOW = 'From Window'
    SCALE_RENDER_SETTINGS = 'From Render Settings'
    SCALE_CUSTOM = 'Custom'


class ResolutionWidget(plugin.PlayblastPlugin, object):

    id = 'Resolution'

    resolutionChanged = Signal()

    def __init__(self, project, parent=None):
        super(ResolutionWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(ResolutionWidget, self).ui()

        self.mode = QComboBox()
        self.mode.addItems([ScaleSettings.SCALE_WINDOW, ScaleSettings.SCALE_RENDER_SETTINGS, ScaleSettings.SCALE_CUSTOM])
        self.mode.setCurrentIndex(1)

        self.resolution = QWidget()
        resolution_layout = QHBoxLayout()
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(6)
        self.resolution.setLayout(resolution_layout)

        width_lbl = QLabel('Width')
        width_lbl.setFixedWidth(40)
        self.width = QSpinBox()
        self.width.setMinimum(0)
        self.width.setMaximum(99999)
        self.width.setValue(1920)

        height_lbl = QLabel('Height')
        height_lbl.setFixedWidth(40)
        self.height = QSpinBox()
        self.height.setMinimum(0)
        self.height.setMaximum(99999)
        self.height.setValue(1080)

        resolution_layout.addWidget(width_lbl)
        resolution_layout.addWidget(self.width)
        resolution_layout.addWidget(height_lbl)
        resolution_layout.addWidget(self.height)

        self.scale_result = QLineEdit()
        self.scale_result.setReadOnly(True)

        self.percent_layout = QHBoxLayout()
        self.percent_lbl = QLabel('Scale')
        self.percent = QDoubleSpinBox()
        self.percent.setMinimum(0.01)
        self.percent.setSingleStep(0.05)
        self.percent.setValue(1.0)
        self.percent_presets_layout = QHBoxLayout()
        self.percent_presets_layout.setSpacing(4)
        for value in [0.25, 0.5, 0.75, 1.0, 2.0]:
            btn = QPushButton(str(value))
            self.percent_presets_layout.addWidget(btn)
            btn.setFixedWidth(35)
            btn.clicked.connect(partial(self.percent.setValue, value))
        self.percent_layout.addWidget(self.percent_lbl)
        self.percent_layout.addWidget(self.percent)
        self.percent_layout.addLayout(self.percent_presets_layout)

        self.main_layout.addWidget(self.mode)
        self.main_layout.addWidget(self.resolution)
        self.main_layout.addLayout(self.percent_layout)
        self.main_layout.addWidget(self.scale_result)

        self._on_mode_changed()
        self._on_resolution_changed()

        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        self.mode.currentIndexChanged.connect(self._on_resolution_changed)
        self.percent.valueChanged.connect(self._on_resolution_changed)
        self.width.valueChanged.connect(self._on_resolution_changed)
        self.height.valueChanged.connect(self._on_resolution_changed)

        self.mode.currentIndexChanged.connect(self.optionsChanged)
        self.percent.valueChanged.connect(self.optionsChanged)
        self.width.valueChanged.connect(self.optionsChanged)
        self.height.valueChanged.connect(self.optionsChanged)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        return {'mode': self.mode.currentText(),
                'width': self.width.value(),
                'height': self.height.value(),
                'percent': self.percent.value()}

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        mode = self.mode.currentText()
        if mode == ScaleSettings.SCALE_CUSTOM:
            width = self.width.value()
            height = self.height.value()
        elif mode == ScaleSettings.SCALE_RENDER_SETTINGS:
            width = tp.Dcc.get_default_render_resolution_width()
            height = tp.Dcc.get_default_render_resolution_height()
        elif mode == ScaleSettings.SCALE_WINDOW:
            width = tp.Dcc.get_viewport_resolution_width()
            height = tp.Dcc.get_viewport_resolution_height()
        else:
            raise NotImplementedError('Unsupported scale mode: {}'.format(mode))

        scale = [width, height]
        percentage = self.percent.value()
        scale = [math.floor(x * percentage) for x in scale]

        return {'width': scale[0], 'height': scale[1]}

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin apply_inputs function
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        mode = attrs_dict.get('mode', ScaleSettings.SCALE_RENDER_SETTINGS)
        width = int(attrs_dict.get('width', 1920))
        height = int(attrs_dict.get('height', 1080))
        percent = float(attrs_dict.get('percent', 1.0))

        self.mode.setCurrentIndex(self.mode.findText(mode))
        self.width.setValue(width)
        self.height.setValue(height)
        self.percent.setValue(percent)

    def _get_output_resolution(self):
        """
        Internal function that returns the ouput resolution
        :return: list(int, int)
        """

        options = self.get_outputs()
        return int(options['width']), int(options['height'])

    def _on_mode_changed(self):
        """
        Internal callback function that updates the width/height enabled state when mode changes
        """

        if self.mode.currentText() != ScaleSettings.SCALE_CUSTOM:
            self.width.setEnabled(False)
            self.height.setEnabled(False)
            self.resolution.hide()
        else:
            self.width.setEnabled(True)
            self.height.setEnabled(True)
            self.resolution.show()

    def _on_resolution_changed(self):
        """
        Internal callback function that updates the resolution label
        """

        width, height = self._get_output_resolution()
        lbl = 'Resolution: {}x{}'.format(width, height)
        self.scale_result.setText(lbl)
        self.label = 'Resolution ({}x{})'.format(width, height)
        self.labelChanged.emit(self.label)
