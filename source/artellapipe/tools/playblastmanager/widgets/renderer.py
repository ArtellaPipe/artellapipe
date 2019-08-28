#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Renderer Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

import tpDccLib as tp

from artellapipe.tools.playblastmanager.core import plugin


class RendererWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to select Maya renderer to use to render playblast
    """

    id = 'Renderer'

    def __init__(self, project, parent=None):

        self._renderers = self.get_renderers()

        super(RendererWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(RendererWidget, self).ui()

        self.renderers = QComboBox()
        self.renderers.addItems(self._renderers.keys())
        self.main_layout.addWidget(self.renderers)
        self.apply_inputs(self.get_defaults())

        self.renderers.currentIndexChanged.connect(self.optionsChanged)

    def get_inputs(self, as_preset=False):
        return {'rendererName': self.get_current_renderer()}

    def get_outputs(self):
        return {'viewport_options': {
            'rendererName': self.get_current_renderer()
        }}

    def apply_inputs(self, attrs_dict):
        reverse_lookup = {value: key for key, value in self._renderers.items()}
        renderer = attrs_dict.get('rendererName', 'vp2Renderer')
        renderer_ui = reverse_lookup.get(renderer)

        if renderer_ui:
            index = self.renderers.findText(renderer_ui)
            self.renderers.setCurrentIndex(index)
        else:
            self.renderers.setCurrentIndex(1)

    def get_defaults(self):
        return {'rendererName': 'vp2Renderer'}

    def get_renderers(self):
        """
        Returns a list with all available renderes for playblast
        :return: list<str>
        """

        renderers = tp.Dcc.get_renderers()

        if tp.is_maya():
            renderers.pop('Stub Renderer')

        return renderers

    def get_current_renderer(self):
        """
        Get current renderer by internal name (non-UI)
        :return: str, name of the renderer
        """

        renderer_ui = self.renderers.currentText()
        renderer = self._renderers.get(renderer_ui, None)
        if renderer is None:
            raise RuntimeError('No valid renderer: {}'.format(renderer_ui))

        return renderer
