#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to capture playblasts
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *

import tpDccLib as tp

from tpQtLib.widgets import accordion

from artellapipe.gui import window

from artellapipe.tools.playblastmanager.widgets import presets

if tp.is_maya():
    from tpMayaLib.core import helpers, layer

# ========================================================================================================

_registered_tokens = dict()

# ========================================================================================================


class PlayblastManager(window.ArtellaWindow, object):

    optionsChanged = Signal(dict)
    playblastStart = Signal(dict)
    playblastFinished = Signal(dict)
    viewerStart = Signal(dict)

    LOGO_NAME = 'playblastmanager_logo'

    def __init__(self, project):
        self.playblast_widgets = list()
        self.config_dialog = None

        project_name = project.get_clean_name()

        register_token('<Camera>', camera_token, label='Insert camera name')
        register_token('<Scene>', lambda attrs_dict: tp.Dcc.scene_name() or 'playblast', label='Insert current scene name')

        if tp.is_maya():
            register_token('<RenderLayer>', lambda attrs_dict: layer.get_current_render_layer(), label='Insert active render layer name')
            register_token('<Images>', lambda attrs_dict: helpers.get_project_rule('images'), label='Insert image directory of set project')
            register_token('<Movies>', lambda attrs_dict: helpers.get_project_rule('movie'), label='Insert movies directory of set project')

        register_token('<{}>'.format(project_name), lambda attrs_dict: project.get_path(), label='Insert {} project path'.format(project_name))

        super(PlayblastManager, self).__init__(
            project=project,
            name='ArtellaPlayblastManager',
            title='Playblast Manager',
            size=(710, 445)
        )

    def ui(self):
        super(PlayblastManager, self).ui()

        self._main_widget = accordion.AccordionWidget(parent=self)
        self._main_widget.rollout_style = accordion.AccordionStyle.MAYA

        self.preset_widget = presets.PlayblastPreset(project=self._project, inputs_getter=self.get_inputs, parent=self)
        self.main_widget.add_item('Presets', self.preset_widget, collapsed=False)

        self.main_layout.addWidget(self._main_widget)


def format_tokens(token_str, attrs_dict):
    """
    Replace the tokens with the given strings
    :param token_str: str, filename of the playbalst with tokens
    :param attrs_dict: dict, parsed capture options
    :return: str, formatted filename with all tokens resolved
    """

    if not token_str:
        return token_str

    for token, value in _registered_tokens.items():
        if token in token_str:
            fn = value['fn']
            token_str = token_str.replace(token, fn(attrs_dict))

    return token_str


def register_token(token, fn, label=''):
    assert token.startswith('<') and token.endswith('>')
    assert callable(fn)
    _registered_tokens[token] = {'fn': fn, 'label': label}


def list_tokens():
    return _registered_tokens.keys()


def camera_token(attrs_dict):
    """
    Returns short name of camera from options
    :param attrs_dict: dict, parsed capture options
    """

    camera = attrs_dict['camera']
    camera = camera.rsplit('|', 1)[-1]
    camera = camera.replace(':', '_')

    return camera


def run(project):
    win = PlayblastManager(project=project)
    win.show()

    return win
