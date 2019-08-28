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

import re
import sys

from Qt.QtWidgets import *

import tpDccLib as tp

from artellapipe.tools.playblastmanager.core import plugin


class TimeRanges(object):
    RANGE_TIME_SLIDER = 'Time Slider'
    RANGE_START_END = 'Start/End'
    CURRENT_FRAME = 'Current Frame'
    CUSTOM_FRAMES = 'Custom Frames'


class TimeRangeWidget(plugin.PlayblastPlugin, object):

    id = 'Time Range'
    label = 'Time Range'

    def __init__(self, project, parent=None):

        self._event_callbacks = list()

        super(TimeRangeWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 0, 5, 0)

        return main_layout

    def ui(self):
        super(TimeRangeWidget, self).ui()

        self.mode = QComboBox()
        self.mode.addItems([TimeRanges.RANGE_TIME_SLIDER, TimeRanges.RANGE_START_END, TimeRanges.CURRENT_FRAME, TimeRanges.CUSTOM_FRAMES])

        self.start = QSpinBox()
        self.start.setRange(-sys.maxint, sys.maxint)
        self.start.setFixedHeight(20)
        self.end = QSpinBox()
        self.end.setRange(-sys.maxint, sys.maxint)
        self.end.setFixedHeight(20)

        self.custom_frames = QLineEdit()
        self.custom_frames.setFixedHeight(20)
        self.custom_frames.setPlaceholderText('Example: 1-20,25,50,75,100-150')
        self.custom_frames.setVisible(True)
        self.custom_frames.setVisible(False)

        for widget in [self.mode, self.start, self.end, self.custom_frames]:
            self.main_layout.addWidget(widget)

    def setup_signals(self):
        self.start.valueChanged.connect(self._ensure_end)
        self.start.valueChanged.connect(self._on_mode_changed)
        self.end.valueChanged.connect(self._ensure_start)
        self.end.valueChanged.connect(self._on_mode_changed)
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        self.custom_frames.textChanged.connect(self._on_mode_changed)

    def validate(self):
        """
        Overrides base ArtellaPlayblastPlugin validate function
        Will ensure that widget outputs are valid and will raise proper errors if necessary
        :return: list<str>
        """

        errors = list()
        if self.mode.currentText() == TimeRanges.CUSTOM_FRAMES:
            self.custom_frames.setStyleSheet('')
            try:
                self.parse_frames(self.custom_frames.text())
            except ValueError as e:
                errors.append('{0} : Invalid frame description: "{1}"'.format(self.id, e))
                self.custom_frames.setStyleSheet('border 1px solid red;')
            except Exception:
                pass

        return errors

    def initialize(self):
        """
        Overrides base ArtellaPlayblastPlugin initialize function
        Method used to initialize callbacks on widget
        """

        pass

        # self._register_callbacks()

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        return {
            'time': self.mode.currentText(),
            'start_frame': self.start.value(),
            'end_frame': self.end.value(),
            'frame': self.custom_frames.text()
        }

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        mode = self.mode.currentText()
        frames = None
        if mode == TimeRanges.RANGE_TIME_SLIDER:
            start, end = tp.Dcc.get_time_slider_range()
        elif mode == TimeRanges.RANGE_START_END:
            start = self.start.value()
            end = self.end.value()
        elif mode == TimeRanges.CURRENT_FRAME:
            frame = tp.Dcc.get_current_frame()
            start = frame
            end = frame
        elif mode == TimeRanges.CUSTOM_FRAMES:
            frames = self.parse_frames(self.custom_frames.text())
            start = None
            end = None
        else:
            raise NotImplementedError('Unsupported time range mode: "{}"'.format(mode))

        return {
            'start_frame': start,
            'end_frame': end,
            'frame': frames
        }

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        mode = self.mode.findText(attrs_dict.get('time', TimeRanges.RANGE_TIME_SLIDER))
        start_frame = attrs_dict.get('start_frame', 1)
        end_frame = attrs_dict.get('end_frame', 120)
        custom_frames = attrs_dict.get('frame', None)

        self.mode.setCurrentIndex(mode)
        self.start.setValue(int(start_frame))
        self.end.setValue(int(end_frame))
        if custom_frames is not None:
            self.custom_frames.setText(custom_frames)

    def _ensure_start(self, value):
        """
        Internal function that initializes the value of the start frame
        :param value: int
        """

        self.start.setValue(min(self.start.value(), value))

    def _ensure_end(self, value):
        """
        Internal function that initializes the value of the end frame
        :param value: int
        """

        self.end.setValue(max(self.end.value(), value))

    def _on_mode_changed(self, emit=True):
        """
        Internal callback function that is called when Time Slider Mode changes
        :param emit: bool
        """

        mode = self.mode.currentText()
        if mode == TimeRanges.RANGE_TIME_SLIDER:
            start, end = tp.Dcc.get_time_slider_range()
            self.start.setEnabled(False)
            self.end.setEnabled(False)
            self.start.setVisible(True)
            self.end.setVisible(True)
            self.custom_frames.setVisible(False)
            mode_values = int(start), int(end)
        elif mode == TimeRanges.RANGE_START_END:
            self.start.setEnabled(True)
            self.end.setEnabled(True)
            self.start.setVisible(True)
            self.end.setVisible(True)
            self.custom_frames.setVisible(False)
            mode_values = self.start.value(), self.end.value()
        elif mode == TimeRanges.CUSTOM_FRAMES:
            self.start.setVisible(False)
            self.end.setVisible(False)
            self.custom_frames.setVisible(True)
            mode_values = '({})'.format(self.custom_frames.text())
            self.validate()
        else:
            self.start.setEnabled(False)
            self.end.setEnabled(False)
            self.start.setVisible(True)
            self.end.setVisible(True)
            self.custom_frames.setVisible(False)
            current_frame = int(tp.Dcc.get_current_frame())
            mode_values = '({})'.format(current_frame)

        self.label = 'Time Range {}'.format(mode_values)
        self.labelChanged.emit(self.label)

    @staticmethod
    def parse_frames(frames_str):
        """
        Parses the given frames from a frame list string
        :param frames_str: parse_frames("0-3;30") --> [0, 1, 2, 3, 30]
        :return: list<str>
        """

        result = list()
        if not frames_str.strip():
            raise ValueError('Cannot parse an empty frame string')
        if not re.match("^[-0-9,; ]*$", frames_str):
            raise ValueError('Invalid symbols in frame string: {}'.format(frames_str))

        for raw in re.split(';|,', frames_str):
            value = raw.strip().replace(' ', '')
            if not value:
                continue

            # Check for sequences (1-20) including negatives (-10--8)
            sequence = re.search("(-?[0-9]+)-(-?[0-9]+)", value)
            if sequence:
                start, end = sequence.groups()
                frames = range(int(start), int(end) + 1)
                result.extend(frames)
            else:
                try:
                    frame = int(value)
                except ValueError:
                    raise ValueError('Invalid frame description: "{}"'.format(value))
                result.append(frame)

        if not result:
            raise ValueError('Unable to parse any frame from string: {}'.format(frames_str))

        return result

    # def closeEvent(self, event):
    #     self.uninitialize()
    #     event.accept()
    #
    # def uninitialize(self):
    #     self._remove_callbacks()

    # def _register_callbacks(self):
    #     """
    #     Register Maya time and playback range change callbacks
    #     """
    #
    #     callback = lambda x: self._on_mode_changed(emit=False)
    #     current_frame = OpenMayaV1.MEventMessage.addEventCallback('timeChanged', callback)
    #     time_range = OpenMayaV1.MEventMessage.addEventCallback('playbackRangeChanged', callback)
    #     self._event_callbacks.append(current_frame)
    #     self._event_callbacks.append(time_range)
    #
    # def _remove_callbacks(self):
    #     for callback in self._event_callbacks:
    #         try:
    #             OpenMayaV1.MEventMessage.removeCallback(callback)
    #         except RuntimeError as e:
    #             sys.solstice.logger.error('Encounter error: {}'.format(e))