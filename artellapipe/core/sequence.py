#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class that defines Artella Sequence
"""

from __future__ import print_function, division, absolute_import

import os
import logging

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import decorators, path as path_utils

from tpQtLib.core import base
from tpQtLib.widgets import splitters

from artellapipe.utils import resource
from artellapipe.core import defines, artellalib, artellaclasses

LOGGER = logging.getLogger()


class ArtellaSequence(object):

    DEFAULT_FILES = ['master_layout']

    def __init__(self, project, sequence_name, sequence_id, sequence_data):
        super(ArtellaSequence, self).__init__()

        self._project = project
        self._name = sequence_name
        self._id = sequence_id
        self._sequence_data = sequence_data

        self._info = None
        self._files = dict()

        self.update_files()

    @property
    def name(self):
        """
        Returns the name of the sequence
        :return: str
        """

        return self._name

    @property
    def id(self):
        """
        Returns ID of the sequence
        :return: str
        """

        return self._id

    def get_complete_name(self):
        """
        Returns complete name of the sequence (name + ID)
        :return: str
        """

        return self._project.format_template('sequence_name', {'sequence_name': self._name, 'sequence_index': self._id})

    def get_path(self):
        """
        Returns path where sequence
        :return:
        """

        return path_utils.clean_path(os.path.join(
            self._project.get_production_path(),
            self._project.format_template('sequence', {'sequence_name': self._name, 'sequence_index': self._id}))
        )

    def get_info(self, force_update=False):
        """
        Returns info from Artella server
        :param force_update:
        :return: ArtellaHeaderMetaData
        """

        if not self._info or force_update:
            shot_info = artellalib.get_status(self.get_path())
            if not isinstance(shot_info, artellaclasses.ArtellaDirectoryMetaData):
                LOGGER.warning('Shot {} has has no info inside!'.format(self.get_complete_name()))
                return
            self._info = shot_info

        return self._info

    def get_files(self, force_update=False):
        """
        Returns files of the sequences
        :param force_update: bool
        :return: dict
        """

        if not self._files or force_update:
            return self.update_files()

        return self._files

    def get_shots(self, force_update=False):
        """
        Returns all shot files that are port of this sequence
        :param force_update: bool
        :return:
        """

        shots = self._project.get_shots_from_sequence(self.get_complete_name())
        return shots

    @decorators.timestamp
    def update_files(self, status=defines.ARTELLA_SYNC_WORKING_ASSET_STATUS, force_update=False):
        """
        Caches adn returns all the files that belongs to the current sequence
        :param status:
        :param force_update: bool
        :return:
        """

        if self._files and not force_update:
            return self._files

        self._files.clear()

        production_path = path_utils.clean_path(os.path.join(os.path.dirname(self._project.get_production_path())))
        for file_name in self.DEFAULT_FILES:
            file_folder = self._project.format_template(
                '{}_folder'.format(file_name), {'sequence_name': self._name, 'sequence_index': self._id})
            self._files[file_name] = dict()
            self._files[file_name]['path'] = file_folder

            if status == defines.ARTELLA_SYNC_WORKING_ASSET_STATUS:
                file_folder_working = self._project.format_template(
                    '{}_working_folder'.format(file_name), {'sequence_name': self._name, 'sequence_index': self._id})
                if not file_folder_working:
                    LOGGER.warning(
                        'Impossible to retrieve {} folder for Sequence {} File: "{}"'.format(
                            defines.ARTELLA_SYNC_WORKING_ASSET_STATUS, self._name, file_name))
                    return
                file_folder_working_full = path_utils.clean_path(os.path.join(production_path, file_folder_working))
                file_folder_working_info = artellalib.get_status(file_folder_working_full)
                if not file_folder_working_info:
                    LOGGER.warning(
                        'Working file for: {} | {} does not exists in Artella server!'.format(
                            file_name, file_folder_working))
                    return
                if not isinstance(file_folder_working_info, artellaclasses.ArtellaDirectoryMetaData):
                    LOGGER.warning(
                        'Artella information retrieve from Artella path: "{}" is not valid. Contact TD!'.format(
                            file_folder_working))
                    continue

                layout_files = list()
                if file_folder_working_info.references:
                    for ref_name, ref_data in file_folder_working_info.references.items():
                        layout_files.append(
                            path_utils.clean_path(os.path.join(file_folder_working, ref_name.split('/')[-1])))

                if len(layout_files) > 0:
                    self._files[file_name]['status'] = dict()
                    self._files[file_name]['status'][defines.ARTELLA_SYNC_WORKING_ASSET_STATUS] = dict()
                    self._files[file_name]['status'][defines.ARTELLA_SYNC_WORKING_ASSET_STATUS]['path'] = \
                        file_folder_working
                    self._files[file_name]['status'][defines.ARTELLA_SYNC_WORKING_ASSET_STATUS]['file'] = \
                        layout_files[0]
            else:
                raise NotImplementedError('Published Layout Files are not supported yet!')

        return self._files


class ArtellaSequenceWidget(base.BaseWidget, object):
    def __init__(self, sequence, parent=None):

        self._sequence = sequence

        super(ArtellaSequenceWidget, self).__init__(parent=parent)

    @property
    def sequence(self):
        """
        Returns sequence object wrapped by this widget
        :return: ArtellaSequence
        """

        return self._sequence

    def ui(self):
        super(ArtellaSequenceWidget, self).ui()

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(2, 2, 2, 2,)
        widget_layout.setSpacing(2)
        widget_layout.setAlignment(Qt.AlignLeft)
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        # Name and icon layout
        icon_name_layout = QHBoxLayout()
        icon_name_layout.setContentsMargins(2, 2, 2, 2)
        icon_name_layout.setSpacing(2)
        icon_name_layout.setAlignment(Qt.AlignLeft)
        widget_layout.addLayout(icon_name_layout)
        seq_lbl = splitters.Splitter(self._sequence.get_complete_name())
        icon_lbl = QLabel()
        icon_name_layout.addWidget(seq_lbl)
        icon_name_layout.addWidget(icon_lbl)
        icon_name_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        files_layout = QHBoxLayout()
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(2)
        widget_layout.addLayout(files_layout)
        files_widget = self._get_files()
        for f in files_widget:
            files_layout.addWidget(f)
        files_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        # self._open_btn = QPushButton()

    def get_shots(self):
        """
        Returns shots of the wrapped sequence
        :return:
        """

        if not self._sequence:
            return None

        return self._sequence.get_shots()

    def _get_files(self):
        """
        Retrieves files from wrapped sequence and proper widgets
        """

        files_found = list()

        sequence_files = self.sequence.get_files(force_update=True)
        if not sequence_files:
            return

        for file_name, file_data in sequence_files.items():
            if not file_data:
                continue
            file_status = file_data.get('status', None)
            if not file_status:
                continue
            file_statuses = list()
            if defines.ARTELLA_SYNC_WORKING_ASSET_STATUS in file_status:
                file_statuses.append(defines.ARTELLA_SYNC_WORKING_ASSET_STATUS)
            elif defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS in file_status:
                file_statuses.append(defines.ARTELLA_SYNC_PUBLISHED_ASSET_STATUS)
            for status in file_statuses:
                seq_file = ArtellaSequenceFileWidget(
                    status=status,
                    root_path=file_data.get('path', None),
                    base_path=file_data['status'][defines.ARTELLA_SYNC_WORKING_ASSET_STATUS].get('path', None),
                    file_path=file_data['status'][defines.ARTELLA_SYNC_WORKING_ASSET_STATUS].get('file', None)
                )
                files_found.append(seq_file)

        return files_found


class ArtellaSequenceFileWidget(base.BaseWidget, object):
    def __init__(self, status, root_path, base_path, file_path, parent=None):
        super(ArtellaSequenceFileWidget, self).__init__(parent=parent)

        self._status = status
        self._root = root_path
        self._path = base_path
        self._file = file_path

    def ui(self):
        super(ArtellaSequenceFileWidget, self).ui()

        self.setMinimumWidth(140)

        main_frame = QFrame()
        main_frame_layout = QVBoxLayout()
        main_frame.setLayout(main_frame_layout)
        main_frame.setStyleSheet(
            "#background {border-radius: 3px;border-style: solid;border-width: 1px;border-color: rgb(32,32,32);}")
        main_frame.setFrameShape(QFrame.StyledPanel)
        main_frame.setFrameShadow(QFrame.Raised)
        self.main_layout.addWidget(main_frame)

        self.lbl = QLabel('MASTER LAYOUT')
        self.lbl.setStyleSheet('background-color: rgb(32, 32, 32);')
        self.lbl.setAlignment(Qt.AlignCenter)
        main_frame_layout.addWidget(self.lbl)
        main_frame_layout.addLayout(splitters.SplitterLayout())

        self.main_layout.addItem(QSpacerItem(0, 5, QSizePolicy.Fixed, QSizePolicy.Expanding))

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(0)
        main_frame_layout.addLayout(buttons_layout)
        self._sync_btn = QToolButton()
        self._sync_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._sync_btn.setText('Sync')
        self._sync_btn.setStatusTip('Sync File')
        self._sync_btn.setToolTip('Sync File')
        self._sync_btn.setIcon(resource.ResourceManager().con('sync'))
        self._open_btn = QToolButton()
        self._open_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._open_btn.setText('Open')
        self._open_btn.setStatusTip('Open File')
        self._open_btn.setToolTip('Open File')
        self._open_btn.setIcon(resource.ResourceManager().icon('open'))
        self._import_btn = QToolButton()
        self._import_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._import_btn.setText('Import')
        self._import_btn.setStatusTip('Import File')
        self._import_btn.setToolTip('Import File')
        self._import_btn.setIcon(resource.ResourceManager().icon('import'))
        self._reference_btn = QToolButton()
        self._reference_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._reference_btn.setText('Reference')
        self._reference_btn.setStatusTip('Reference File')
        self._reference_btn.setToolTip('Reference File')
        self._reference_btn.setIcon(resource.ResourceManager().icon('reference'))
        self._new_version_btn = QToolButton()
        self._new_version_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._new_version_btn.setText('New Version')
        self._new_version_btn.setStatusTip('Reference File')
        self._new_version_btn.setStatusTip('New Version')
        self._new_version_btn.setToolTip('New Version')
        self._new_version_btn.setIcon(resource.ResourceManager().icon('upload'))

        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        buttons_layout.addWidget(self._sync_btn)
        buttons_layout.addWidget(splitters.get_horizontal_separator_widget())
        buttons_layout.addWidget(self._open_btn)
        buttons_layout.addWidget(self._import_btn)
        buttons_layout.addWidget(self._reference_btn)
        buttons_layout.addWidget(splitters.get_horizontal_separator_widget())
        buttons_layout.addWidget(self._new_version_btn)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        main_frame_layout.addItem(QSpacerItem(0, 5, QSizePolicy.Fixed, QSizePolicy.Expanding))

        # self._sync_btn.clicked.connect(self.sync)
        # self._open_btn.clicked.connect(self.open)
