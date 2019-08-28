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

import os
import contextlib

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import osplatform

import tpDccLib as tp

from tpQtLib.widgets import accordion

import artellapipe
from artellapipe.gui import window, dialog
from artellapipe.tools.playblastmanager.core import plugin
from artellapipe.tools.playblastmanager.widgets import presets, preview, viewport, displayoptions, cameras, codec, options, panzoom, renderer, resolution, save, timerange
from artellapipe.tools.playblastmanager.plugins import mask

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import helpers, layer, gui, playblast

# ========================================================================================================

_registered_tokens = dict()

# ========================================================================================================


class DefaultPlayblastOptions(plugin.PlayblastPlugin, object):

    def get_outputs(self):
        outputs = dict()
        scene = parse_current_scene()
        outputs['sound'] = scene['sound']
        outputs['show_ornaments'] = True
        outputs['camera_options'] = dict()
        outputs['camera_options']['overscan'] = 1.0
        outputs['camera_options']['displayFieldChart'] = False
        outputs['camera_options']['displayFilmGate'] = False
        outputs['camera_options']['displayFilmOrigin'] = False
        outputs['camera_options']['displayFilmPivot'] = False
        outputs['camera_options']['displayGateMask'] = False
        outputs['camera_options']['displayResolution'] = False
        outputs['camera_options']['displaySafeAction'] = False
        outputs['camera_options']['displaySafeTitle'] = False

        return outputs


class PlayblastManager(window.ArtellaWindow, object):

    optionsChanged = Signal(dict)
    playblastStart = Signal(dict)
    playblastFinished = Signal(dict)
    viewerStart = Signal(dict)

    VERSION = '0.0.2'
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
        self._main_widget.add_item('Presets', self.preset_widget, collapsed=False)

        self.preview_widget = preview.PlayblastPreview(options=self.get_outputs, validator=self.validate, parent=self)
        self._main_widget.add_item('Preview', self.preview_widget, collapsed=False)

        self.default_options = DefaultPlayblastOptions(project=self._project)
        self.playblast_widgets.append(self.default_options)

        self.time_range = timerange.TimeRangeWidget(project=self._project)
        self.cameras = cameras.CamerasWidget(project=self._project)
        self.resolution = resolution.ResolutionWidget(project=self._project)
        self.mask = mask.MaskWidget(project=self._project)
        self.save = save.SaveWidget(project=self._project)

        for widget in [self.cameras, self.resolution, self.time_range, self.mask, self.save]:
            widget.initialize()
            widget.optionsChanged.connect(self._on_update_settings)
            self.playblastFinished.connect(widget.on_playblast_finished)

            if widget == self.save:
                item = self._main_widget.add_item(widget.id, widget, collapsed=False)
            else:
                item = self._main_widget.add_item(widget.id, widget, collapsed=True)
            self.playblast_widgets.append(widget)
            if item is not None:
                widget.labelChanged.connect(item.setTitle)

        # We force the reload of the camera plugin title
        self.cameras._on_update_label()
        self.resolution._on_resolution_changed()

        self.playblastStart.connect(self.mask.create_mask)

        self.capture_btn = QPushButton('C A P T U R E')
        self.main_layout.addWidget(self.capture_btn)

        self.main_layout.addWidget(self._main_widget)
        self.main_layout.addWidget(self.capture_btn)

    def setup_signals(self):
        self.capture_btn.clicked.connect(self._on_capture)
        self.preset_widget.configOpened.connect(self.show_config)
        self.preset_widget.presetLoaded.connect(self.apply_inputs)
        self.apply_inputs(inputs=self._read_configuration())

    def validate(self):
        """
        Will ensure that widget outputs are valid and will raise proper errors if necessary
        :return: list<str>
        """

        errors = list()
        for widget in self.playblast_widgets:
            if hasattr(widget, 'validate'):
                widget_errors = widget.validate()
                if widget_errors:
                    errors.extend(widget_errors)

        if errors:
            message_title = '{} Validation Error(s)'.format(len(errors))
            message = '\n'.join(errors)
            QMessageBox.critical(self, message_title, message, QMessageBox.Ok)
            return False

        return True

    def get_inputs(self, as_preset=False):
        """
        Returns a dict with proper input variables as keys of the dictionary
        :param as_preset: bool
        :return: dict
        """

        inputs = dict()
        config_widgets = self.playblast_widgets
        config_widgets.append(self.preset_widget)
        for widget in config_widgets:
            widget_inputs = widget.get_inputs(as_preset=as_preset)
            if not isinstance(widget_inputs, dict):
                artellapipe.logger.warning('Widget inputs are not a valid dictionary "{0}" : "{1}"'.format(widget.id, widget_inputs))
                return
            if not widget_inputs:
                continue
            inputs[widget.id] = widget_inputs

        return inputs

    def get_outputs(self):
        """
          Returns the outputs variables of the Playblast widget as dict
          :return: dict
          """

        outputs = dict()
        for widget in self.playblast_widgets:
            if hasattr(widget, 'get_outputs'):
                widget_outputs = widget.get_outputs()
                if not widget_outputs:
                    continue
                for key, value in widget_outputs.items():
                    if isinstance(value, dict) and key in outputs:
                        outputs[key].update(value)
                    else:
                        outputs[key] = value

        return outputs

    def apply_inputs(self, inputs):
        """
        Applies the given dict of attributes to the widget
        :param inputs: dict
        """

        if not inputs:
            return

        widgets = self.playblast_widgets
        widgets.append(self.preset_widget)
        for widget in widgets:
            widget_inputs = inputs.get(widget.id, None)
            if not widget_inputs:
                widget_inputs = dict()
            # if not widget_inputs:
            #     continue
            # if widget_inputs:
            widget.apply_inputs(widget_inputs)

    def show_config(self):
        """
        Shows advanced configuration dialog
        """

        self._build_configuration_dialog()

        geometry = self.geometry()
        self.config_dialog.move(QPoint(geometry.x() + 30, geometry.y()))
        self.config_dialog.exec_()

    def _build_configuration_dialog(self):
        """
        Build configuration dialog to store configuration widgets in
        """

        self.config_dialog = PlayblastTemplateConfigurationDialog()

    def _read_configuration(self):
        inputs = dict()
        path = self.settings().fileName()
        if not os.path.isfile(path) or os.stat(path).st_size == 0:
            return inputs

        for section in self.settings().groups:
            if section == self.objectName().lower():
                continue
            inputs[section] = dict()

            print('Section: {}'.format(section))

            # props = self.settings.items(section)
            # for prop in props:
            #     inputs[section][str(prop[0])] = str(prop[1])

        return inputs

    def _store_configuration(self):
        pass
        # inputs = self.get_inputs(as_preset=False)
        # for widget_id, attrs_dict in inputs.items():
        #     if not self.settings.has_section(widget_id):
        #         self.settings.add_section(widget_id)
        #     for attr_name, attr_value in attrs_dict.items():
        #         self.settings.set(widget_id, attr_name, attr_value)
        # self.settings.update()

    def _on_update_settings(self):
        """
        Internal callback function that is called when options are updated
        """

        self.optionsChanged.emit(self.get_outputs)
        self.preset_widget.presets.setCurrentIndex(0)

    def _on_capture(self):
        valid = self.validate()
        if not valid:
            return

        options = self.get_outputs()
        filename = options.get('filename', None)

        self.playblastStart.emit(options)

        if filename is not None:
            print('Creating capture')

        options['filename'] = filename
        options['filename'] = capture_scene(options=options)

        self.playblastFinished.emit(options)

        filename = options['filename']

        viewer = options.get('viewer', False)
        if viewer:
            if filename and os.path.exists(filename):
                self.viewerStart.emit(options)
                osplatform.open_file(file_path=filename)
            else:
                raise RuntimeError('Cannot open playblast because file "{}" does not exists!'.format(filename))

        return filename


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


def parse_current_scene():
    """
    Parse current Maya scene looking for settings related with play blasts
    :return: dict
    """

    time_control = maya.mel.eval("$gPlayBackSlider = $gPlayBackSlider")

    return {
        'start_frame': maya.cmds.playbackOptions(query=True, minTime=True),
        'end_frame': maya.cmds.playbackOptions(query=True, maxTime=True),
        'width': maya.cmds.getAttr('defaultResolution.width'),
        'height': maya.cmds.getAttr('defaultResolution.height'),
        'compression': maya.cmds.optionVar(query='playblastCompression'),
        'filename': (maya.cmds.optionVar(query='playblastFile') if maya.cmds.optionVar(query='playblastSaveToFile') else None),
        'format': maya.cmds.optionVar(query='playblastFormat'),
        'off_scren': (True if maya.cmds.optionVar(query='playblastOffscreen') else False),
        'show_ornaments': (True if maya.cmds.optionVar(query='playblastShowOrnaments') else False),
        'quality': maya.cmds.optionVar(query='playblastQuality'),
        'sound': maya.cmds.timeControl(time_control, query=True, sound=True) or None
    }


def capture_scene(options):
    """
    Capturing using scene settings
    :param options: dict, collection of output options
    :return: str, path to playblast file
    """

    filename = options.get('filename', '%TEMP%')
    artellapipe.logger.info('Capturing to {}'.format(filename))
    options = options.copy()

    # Force viewer to False in call to capture because we have our own viewer opening call to allow a signal
    # to trigger between playblast and viewer
    options['viewer'] = False
    options.pop('panel', None)

    path = capture(**options)
    path = playblast.fix_playblast_output_path(path)

    return path


def capture(**kwargs):
    """
    Creates a playblast in an independent panel
    :param kwargs:
    """

    if not tp.is_maya():
        artellapipe.logger.warning('Playblast is only supported in Maya!')
        return

    filename = kwargs.get('filename', None)
    camera = kwargs.get('camera', 'persp')
    sound = kwargs.get('sound', None)
    width = kwargs.get('width', tp.Dcc.get_default_render_resolution_width())
    height = kwargs.get('height', tp.Dcc.get_default_render_resolution_height())
    format = kwargs.get('format', 'qt')
    compression = kwargs.get('compression', 'H.264')
    quality = kwargs.get('quality', 100)
    maintain_aspect_ratio = kwargs.get('maintain_aspect_ratio', True)
    frame = kwargs.get('frame', None)
    start_frame = kwargs.get('start_frame', tp.Dcc.get_start_frame())
    end_frame = kwargs.get('end_frame', tp.Dcc.get_end_frame())
    complete_filename = kwargs.get('complete_filename', None)
    off_screen = kwargs.get('off_screen', False)
    isolate = kwargs.get('isolate', None)
    viewer = kwargs.get('viewer', None)
    show_ornaments = kwargs.get('show_ornaments', True)
    overwrite = kwargs.get('overwrite', False)
    frame_padding = kwargs.get('frame_padding', 4)
    raw_frame_numbers = kwargs.get('raw_frame_numbers', False)
    camera_options = kwargs.get('camera_options', None)
    display_options = kwargs.get('display_options', None)
    viewport_options = kwargs.get('viewport_options', None)
    viewport2_options = kwargs.get('viewport2_options', None)

    camera = camera or 'persp'
    if not tp.Dcc.object_exists(camera):
        raise RuntimeError('Camera does not exists!'.format(camera))

    width = width or tp.Dcc.get_default_render_resolution_width()
    height = height or tp.Dcc.get_default_render_resolution_height()
    if maintain_aspect_ratio:
        ratio = tp.Dcc.get_default_render_resolution_aspect_ratio()
        height = round(width / ratio)

    if start_frame is None:
        start_frame = tp.Dcc.get_start_frame()
    if end_frame is None:
        end_frame = tp.Dcc.get_end_frame()

    if raw_frame_numbers and frame is None:
        frame = range(int(start_frame), int(end_frame) + 1)

    playblast_kwargs = dict()
    if complete_filename:
        playblast_kwargs['completeFilename'] = complete_filename
    if frame is not None:
        playblast_kwargs['frame'] = frame
    if sound is not None:
        playblast_kwargs['sound'] = sound

    if frame and raw_frame_numbers:
        check = frame if isinstance(frame, (list, tuple)) else [frame]
        if any(f < 0 for f in check):
            raise RuntimeError('Negative frames are not supported with raw frame numbers and explicit frame numbers')

    tp.Dcc.set_current_frame(tp.Dcc.get_current_frame())

    padding = 10
    with gui.create_independent_panel(width=width + padding, height=height + padding, off_screen=off_screen) as panel:
        tp.Dcc.focus(panel)
        with contextlib.nested(
                viewport.applied_viewport_options(viewport_options, panel),
                cameras.applied_camera_options(camera_options, panel),
                displayoptions.applied_display_options(display_options),
                viewport.applied_viewport2_options(viewport2_options),
                gui.disable_inview_messages(),
                gui.maintain_camera_on_panel(panel=panel, camera=camera),
                gui.isolated_nodes(nodes=isolate, panel=panel),
                gui.reset_time()
        ):
            # Only image format supports raw frame numbers
            # so we ignore the state when calling it with a movie
            # format
            if format != "image" and raw_frame_numbers:
                artellapipe.logger.warning("Capturing to image format with raw frame numbers is not supported. Ignoring raw frame numbers...")
                raw_frame_numbers = False

            output = maya.cmds.playblast(
                compression=compression,
                format=format,
                percent=100,
                quality=quality,
                viewer=viewer,
                startTime=start_frame,
                endTime=end_frame,
                offScreen=off_screen,
                showOrnaments=show_ornaments,
                forceOverwrite=overwrite,
                filename=filename,
                widthHeight=[width, height],
                rawFrameNumbers=raw_frame_numbers,
                framePadding=frame_padding,
                **playblast_kwargs
            )

        return output


class PlayblastTemplateConfigurationDialog(dialog.ArtellaDialog, object):

    def __init__(self, parent=None, **kwargs):

        self.playblast_config_widgets = list()

        super(PlayblastTemplateConfigurationDialog, self).__init__(
            name='PlayblastTemplateConfigurationDialog',
            title='Artella - Playblast Template Configuration',
            parent=parent,
            **kwargs
        )

    def custom_ui(self):
        super(PlayblastTemplateConfigurationDialog, self).custom_ui()

        self.set_logo('solstice_playblast_logo')

        self.resize(400, 810)

        self.setMinimumHeight(810)
        self.setMaximumWidth(400)

        self.options_widget = accordion.AccordionWidget(parent=self)
        self.options_widget.rollout_style = accordion.AccordionStyle.MAYA
        self.main_layout.addWidget(self.options_widget)

        self.codec = codec.CodecWidget(project=self._project)
        self.renderer = renderer.RendererWidget(project=self._project)
        self.display = displayoptions.DisplayOptionsWidget(project=self._project)
        self.viewport = viewport.ViewportOptionsWidget(project=self._project)
        self.options = options.PlayblastOptionsWidget(project=self._project)
        self.panzoom = panzoom.PanZoomWidget(project=self._project)

        for widget in [self.codec, self.renderer, self.display, self.viewport, self.options, self.panzoom]:
            widget.initialize()
            # widget.optionsChanged.connect(self._on_update_settings)
            # self.playblastFinished.connect(widget.on_playblast_finished)
            item = self.options_widget.add_item(widget.id, widget)
            self.playblast_config_widgets.append(widget)
            if item is not None:
                widget.labelChanged.connect(item.setTitle)


def run(project):
    win = PlayblastManager(project=project)
    win.show()

    return win
