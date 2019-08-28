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

import os
import datetime
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import osplatform

import tpDccLib as tp

from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.tools.playblastmanager.core import plugin


class RecentPlayblastAction(QAction, object):
    def __init__(self, parent, file_path):
        super(RecentPlayblastAction, self).__init__(parent)

        action_lbl = os.path.basename(file_path)

        self.setText(action_lbl)
        self.setData(file_path)

        self.setEnabled(os.path.isfile(file_path))

        info = QFileInfo(file_path)
        icon_provider = QFileIconProvider()
        self.setIcon(icon_provider.icon(info))

        self.triggered.connect(self._on_open_object_data)

    def _on_open_object_data(self):
        """
        Internal callback function that is called when Save buttons is clicked
        """

        osplatform.open_file(self.data())


class SaveWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to set playblast display settings
    """

    id = 'Save'
    max_recent_playblasts = 5

    def __init__(self, project, parent=None):

        self._recent_playblasts = list()

        super(SaveWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(SaveWidget, self).ui()

        self.save_file = QCheckBox('Save')
        self.open_viewer = QCheckBox('Open Viewer when finished')
        self.raw_frame_numbers = QCheckBox('Raw Frame Numbers')

        cbx_layout = QHBoxLayout()
        cbx_layout.setContentsMargins(5, 0, 5, 0)
        cbx_layout.addWidget(self.save_file)
        cbx_layout.addWidget(splitters.get_horizontal_separator_widget())
        cbx_layout.addWidget(self.open_viewer)
        cbx_layout.addWidget(splitters.get_horizontal_separator_widget())
        cbx_layout.addWidget(self.raw_frame_numbers)
        cbx_layout.addStretch(True)

        self.play_recent_widget = QWidget()
        play_recent_layout = QVBoxLayout()
        self.play_recent_widget.setLayout(play_recent_layout)
        self.play_recent = QPushButton('Play recent playblast')
        self.recent_menu = QMenu()
        self.play_recent.setMenu(self.recent_menu)
        play_recent_layout.addWidget(self.play_recent)
        cbx_layout.addWidget(self.play_recent_widget)

        self.path_widget = QWidget()
        self.path_widget.setEnabled(False)
        path_layout = QVBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(0)
        path_base_layout = QHBoxLayout()
        path_base_layout.setContentsMargins(0, 0, 0, 0)
        path_base_layout.setSpacing(0)
        path_layout.addLayout(path_base_layout)
        self.path_widget.setLayout(path_layout)
        path_lbl = QLabel('Path: ')
        path_lbl.setFixedWidth(30)
        self.file_path = QLineEdit()
        tip = 'Right click in the text filed to insert tokens'
        self.file_path.setToolTip(tip)
        self.file_path.setStatusTip(tip)
        self.file_path.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_path.customContextMenuRequested.connect(self._on_show_token_menu)
        browse_icon = artellapipe.resource.icon('open')
        self.browse = QPushButton()
        self.browse.setIcon(browse_icon)
        self.browse.setFixedWidth(30)
        self.browse.setToolTip('Playblast Save Path')
        self.browse.setStatusTip('Playblast Save Path')
        path_base_layout.addWidget(path_lbl)
        path_base_layout.addWidget(self.file_path)
        path_base_layout.addWidget(self.browse)

        self.main_layout.addLayout(cbx_layout)
        self.main_layout.addWidget(self.path_widget)
        self.main_layout.addWidget(self.play_recent_widget)

        self.browse.clicked.connect(self._on_show_browse)
        self.file_path.textChanged.connect(self.optionsChanged)
        self.save_file.stateChanged.connect(self.optionsChanged)
        self.raw_frame_numbers.stateChanged.connect(self.optionsChanged)
        self.save_file.stateChanged.connect(self._on_save_changed)

        self._on_save_changed()

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        inputs = {
            'name': self.file_path.text(),
            'save_file': self.save_file.isChecked(),
            'open_finished': self.open_viewer.isChecked(),
            'recent_playblasts': self._recent_playblasts,
            'raw_frame_numbers': self.raw_frame_numbers.isChecked()
        }

        if as_preset:
            inputs['recent_playblasts'] = list()

        return inputs

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        output = {'filename': None,
                  'raw_frame_numbers': self.raw_frame_numbers.isChecked(),
                  'viewer': self.open_viewer.isChecked()}

        save = self.save_file.isChecked()
        if not save:
            return output

        save_path = self.file_path.text()
        if not save_path:
            scene = tp.Dcc.scene_name()
            time_stamp = datetime.datetime.today()
            str_time_stamp = time_stamp.strftime("%d-%m-%Y_%H-%M-%S")
            save_path = '{}_{}'.format(scene, str_time_stamp)

        output['filename'] = save_path

        return output

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        directory = attrs_dict.get('name', None)
        save_file = attrs_dict.get('save_file', True)
        open_finished = attrs_dict.get('open_finished', True)
        raw_frame_numbers = attrs_dict.get('raw_frame_numbers', False)
        prev_playblasts = attrs_dict.get('recent_playblasts', list())

        self.save_file.setChecked(bool(save_file))
        self.open_viewer.setChecked(bool(open_finished))
        self.raw_frame_numbers.setChecked(bool(raw_frame_numbers))

        for playblast in reversed(prev_playblasts):
            self.add_playblast(playblast)

        self.file_path.setText(directory)

    def add_playblast(self, item):
        """
        Adds an item into the playblast menu
        :param item: str, full path to a playblast file
        """

        if item in self._recent_playblasts:
            self._recent_playblasts.remove(item)

        self._recent_playblasts.insert(0, item)

        if len(self._recent_playblasts) > self.max_recent_playblasts:
            del self._recent_playblasts[self.max_recent_playblasts:]

        self.recent_menu.clear()
        for playblast in self._recent_playblasts:
            action = RecentPlayblastAction(parent=self, file_path=playblast)
            self.recent_menu.addAction(action)

    def on_playblast_finished(self, options):
        """
        Takes action after the play blast is completed
        :param options:
        """

        artellapipe.logger.debug('Generating Playblast with options: {}'.format(options))

        playblast_file = options['filename']
        if not playblast_file:
            return

        self.add_playblast(playblast_file)

    def _token_menu(self):
        """
        Internal function that builds the token menu based on the registered tokens
        :return: QMenu
        """

        from artellapipe.tools.playblastmanager.core import playblastmanager

        menu = QMenu(self)
        registered_tokens = playblastmanager.list_tokens()
        for token, value in registered_tokens.items():
            lbl = '{} \t{}'.format(token, value['label'])
            action = QAction(lbl, menu)
            action.triggered.connect(partial(self.file_path.insert, token))
            menu.addAction(action)

        return menu

    def _on_show_browse(self, path=None):
        """
        Internal function used to set the path of the playblast file
        :param path: str
        """

        if path is None:
            scene_path = tp.Dcc.scene_name()
            default_filename = os.path.splitext(os.path.basename(scene_path))[0]
            if not default_filename:
                default_filename = 'playblast'

            # default_root = os.path.normpath(utils.get_project_rule('images'))
            # default_path = os.path.join(default_root, default_filename)
            default_path = self._project.get_path()
            path = tp.Dcc.select_folder_dialog(title='Select Folder', start_directory=default_path)

        if not path:
            return

        if isinstance(path, (tuple, list)):
            path = path[0]

        if path.endswith('.*'):
            path = path[:-2]

        # Fix for playblasts that result in nesting of the extension (eg. '.mov.mov.mov') which happens if the format
        # is defined in the filename used for saving.
        ext = os.path.splitext(path)[-1]
        if ext:
            path = path[:-len(ext)]

        path = os.path.normpath(path)

        self.file_path.setText(path)
        self.file_path.setCursorPosition(0)

    def _on_save_changed(self):
        """
        Internal function used to update the visibility of the path field
        """

        if self.save_file.isChecked():
            self.path_widget.setEnabled(True)
        else:
            self.path_widget.setEnabled(False)

    def _on_show_token_menu(self, pos):
        """
        Internal function that shows a custom menu
        """

        menu = self._token_menu()
        global_pos = QPoint(self.file_path.mapToGlobal(pos))
        menu.exec_(global_pos)
