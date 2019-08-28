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

import contextlib
from collections import OrderedDict

from Qt.QtWidgets import *

import tpDccLib as tp

import artellapipe
from artellapipe.tools.playblastmanager.core import defines, plugin

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import gui


@contextlib.contextmanager
def applied_viewport_options(options, panel):
    """
    Context manager for applying options to panel
    :param options: dict
    :param panel: str
    """

    options = dict(defines.ViewportOptions, **(options or {}))
    playblast_widgets = maya.cmds.pluginDisplayFilter(query=True, listFilters=True)
    widget_options = dict()

    for widget in playblast_widgets:
        if widget in options:
            widget_options[widget] = options.pop(widget)

    maya.cmds.modelEditor(panel, edit=True, **options)

    for widget, state in widget_options.items():
        maya.cmds.modelEditor(panel, edit=True, pluginObjects=(widget, state))

    yield


@contextlib.contextmanager
def applied_viewport2_options(options):
    """
    Context manager for setting viewport 2.0 options
    :param options: dict
    """

    options = dict(defines.Viewport2Options, **(options or {}))
    original = dict()

    for option in options.copy():
        try:
            original[option] = maya.cmds.getAttr('hardwareRenderingGlobals.' + option)
        except ValueError:
            options.pop(option)
    for option, value in options.items():
        maya.cmds.setAttr('hardwareRenderingGlobals.' + option, value)

    try:
        yield
    finally:
        for option, value in original.items():
            maya.cmds.setAttr('hardwareRenderingGlobals.' + option, value)


class ViewportOptionsWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to set playblast display settings
    """

    id = 'Viewport Options'

    def __init__(self, project, parent=None):

        self.show_type_actions = list()
        self.show_types = self.get_show_object_tyes()

        super(ViewportOptionsWidget, self).__init__(project=project, parent=parent)

        self.setObjectName(self.label)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(ViewportOptionsWidget, self).ui()

        menus_layout = QHBoxLayout()

        self.display_light_menu = self._build_light_menu()
        self.display_light_menu.setFixedHeight(20)

        self.show_types_btn = QPushButton('Show')
        self.show_types_btn.setFixedHeight(20)
        self.show_types_menu = self._build_show_menu()
        self.show_types_btn.setMenu(self.show_types_menu)

        menus_layout.addWidget(self.display_light_menu)
        menus_layout.addWidget(self.show_types_btn)

        cbx_layout = QGridLayout()
        self.high_quality = QCheckBox()
        self.high_quality.setText('Force Viewport 2.09 + AA')
        self.override_viewport = QCheckBox('Override Viewport Settings')
        self.override_viewport.setChecked(True)
        self.two_sided_lighting = QCheckBox('Two Sided Lighting')
        self.two_sided_lighting.setChecked(False)
        self.shadows = QCheckBox('Shadow')
        self.shadows.setChecked(False)

        cbx_layout.addWidget(self.override_viewport, 0, 0)
        cbx_layout.addWidget(self.high_quality, 0, 1)
        cbx_layout.addWidget(self.two_sided_lighting, 1, 0)
        cbx_layout.addWidget(self.shadows, 1, 1)

        self.main_layout.addLayout(cbx_layout)
        self.main_layout.addLayout(menus_layout)

        self.high_quality.stateChanged.connect(self.optionsChanged)
        self.override_viewport.stateChanged.connect(self.optionsChanged)
        self.override_viewport.stateChanged.connect(self._on_toggle_override)
        self.two_sided_lighting.stateChanged.connect(self.optionsChanged)
        self.shadows.stateChanged.connect(self.optionsChanged)
        self.display_light_menu.currentIndexChanged.connect(self.optionsChanged)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        inputs = {
            'high_quality': self.high_quality.isChecked(),
            'override_viewport_options': self.override_viewport.isChecked(),
            'display_lights': self.display_light_menu.currentIndex(),
            'shadows': self.shadows.isChecked(),
            'two_sided_lighting': self.two_sided_lighting.isChecked()
        }

        inputs.update(self.get_show_inputs())

        return inputs

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        outputs = dict()
        high_quality = self.high_quality.isChecked()
        override_viewport_options = self.override_viewport.isChecked()

        if override_viewport_options:
            outputs['viewport2_options'] = dict()
            outputs['viewport_options'] = dict()

            if high_quality:
                outputs['viewport_options']['rendererName'] = 'vp2Renderer'
                outputs['viewport2_options']['multiSampleEnable'] = True
                outputs['viewport2_options']['multiSampleCount'] = 8

            show_per_type = self.get_show_inputs()
            display_lights = self.get_display_lights()
            outputs['viewport_options'].update(show_per_type)
            outputs['viewport_options'].update(display_lights)
        else:
            outputs = self.parse_active_view()
            outputs.pop('display_options', None)
            outputs.pop('camera', None)
            outputs['viewport_options'].pop('rendererName', None)
            outputs['camera_options'] = {'depthOfField': outputs['camera_options']['depthOfField']}

        return outputs

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin apply_inputs function
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        override_viewport = attrs_dict.get('override_viewport_options', True)
        high_quality = attrs_dict.get('high_quality', True)
        display_light = attrs_dict.get('display_lights', 0)
        two_sided_lighting = attrs_dict.get('two_sided_lighting', False)
        shadows = attrs_dict.get('shadows', False)

        self.high_quality.setChecked(high_quality)
        self.override_viewport.setChecked(override_viewport)
        self.show_types_btn.setEnabled(override_viewport)
        self.display_light_menu.setCurrentIndex(display_light)
        self.shadows.setChecked(shadows)
        self.two_sided_lighting.setChecked(two_sided_lighting)

        for action in self.show_Type_actions:
            system_name = self.show_types[action.text()]
            state = attrs_dict.get(system_name, True)
            action.setChecked(state)

    def get_show_object_tyes(self):
        """
        Returns object types
        :return: list(str)
        """

        results = OrderedDict()

        if tp.is_maya():
            plugin_shapes = gui.get_plugin_shapes()
            results.update(plugin_shapes)

        results.update(defines.OBJECT_TYPES)

        return results

    def get_show_inputs(self):
        """
        Returns checked state of show menu items
        :return: dict, checked show states in the widget
        """

        show_inputs = dict()
        for action in self.show_type_actions:
            lbl = action.text()
            name = self.show_types.get(lbl, None)
            if name is None:
                continue
            show_inputs[name] = action.isChecked()

        return show_inputs

    def get_display_lights(self):
        """
        Returns and parse the currently selected display lights options
        :return: dict, the display light options
        """

        index = self.display_light_menu.currentIndex()
        return {
            'display_lights': self.display_light_menu.itemData(index),
            'shadows': self.shadows.isChecked(),
            'two_sided_lighting': self.two_sided_lighting.isChecked()
        }

    def _build_light_menu(self):
        """
        Internal function used to build different types of lighting for the viewport
        :return: QComboBox
        """

        menu = QComboBox(self)

        display_lights = (
            ("Use Default Lighting", "default"),
            ("Use All Lights", "all"),
            ("Use Selected Lights", "active"),
            ("Use Flat Lighting", "flat"),
            ("Use No Lights", "none")
        )

        for lbl, name in display_lights:
            menu.addItem(lbl, userData=name)

        return menu

    def _build_show_menu(self):
        """
        Internal function used to build the menu to select which objects types are
        shown in the output
        :return: QMenu
        """

        menu = QMenu(self)
        menu.setObjectName('ShowShapesMenu')
        menu.setWindowTitle('Show')
        menu.setFixedWidth(180)
        menu.setTearOffEnabled(False)

        toggle_all = QAction(menu, text='All')
        toggle_none = QAction(menu, text='None')
        menu.addAction(toggle_all)
        menu.addAction(toggle_none)
        menu.addSeparator()

        for shp in self.show_types:
            action = QAction(menu, text=shp)
            action.setCheckable(True)
            action.toggled.connect(self.optionsChanged)
            menu.addAction(action)
            self.show_type_actions.append(action)

        toggle_all.triggered.connect(self._on_toggle_all_visible)
        toggle_none.triggered.connect(self._on_toggle_all_hide)

        return menu

    def parse_view(self, panel):
        """
        Parse the scene, panel and camera looking for their current settings
        :param panel: str
        """

        if not tp.is_maya():
            return dict()

        camera = maya.cmds.modelPanel(panel, query=True, camera=True)
        display_options = dict()
        camera_options = dict()
        viewport_options = dict()
        viewport2_options = dict()

        for key in defines.DisplayOptions:
            if key in defines._DisplayOptionsRGB:
                display_options[key] = maya.cmds.displayRGBColor(key, query=True)
            else:
                display_options[key] = maya.cmds.displayPref(query=True, **{key: True})
        for key in defines.CameraOptions:
            camera_options[key] = tp.Dcc.get_attribute_value(node=camera, attribute_name=key)
        widgets = maya.cmds.pluginDisplayFilter(query=True, listFilters=True)
        for widget in widgets:
            widget = str(widget)
            state = maya.cmds.modelEditor(panel, query=True, queryPluginObjects=widget)
            viewport_options[widget] = state
        for key in defines.ViewportOptions:
            viewport_options[key] = maya.cmds.modelEditor(panel, query=True, **{key: True})
        for key in defines.Viewport2Options.keys():
            attr = 'hardwareRenderingGlobals.{}'.format(key)
            try:
                viewport2_options[key] = maya.cmds.getAttr(attr)
            except ValueError:
                continue

        return {
            "camera": camera,
            "display_options": display_options,
            "camera_options": camera_options,
            "viewport_options": viewport_options,
            "viewport2_options": viewport2_options
        }

    def parse_active_view(self):
        """
        Parses the current settings from the active view
        :return: str
        """

        if not tp.is_maya():
            return dict()

        panel = gui.get_active_panel()
        if not panel or 'modelPanel' not in panel:
            artellapipe.logger.warning('No active model panel found!')
            return dict()

        return self.parse_view(panel)

    def _on_toggle_all_visible(self):
        """
        Internal callback function that set all object types off or on depending
        on the state
        """

        for action in self.show_type_actions:
            action.setChecked(True)

    def _on_toggle_all_hide(self):
        """
        Internal callback function that set all object types off or on depending
        on the state
        """

        for action in self.show_type_actions:
            action.setChecked(False)

    def _on_toggle_override(self):
        """
        Internal callback function that enables or disables show menu when override
        is checked
        """

        state = self.override_viewport.isChecked()
        self.show_types_btn.setEnabled(state)
        self.high_quality.setEnabled(state)
        self.display_light_menu.setEnabled(state)
        self.shadows.setEnabled(state)
        self.two_sided_lighting.setEnabled(state)
