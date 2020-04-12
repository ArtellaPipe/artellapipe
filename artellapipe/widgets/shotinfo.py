#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget that shows shot information
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import breadcrumb, stack, dividers, grid

import artellapipe.register
from artellapipe.core import defines
from artellapipe.libs.artella.core import artellalib


class ShotInfoWidget(base.BaseWidget, object):
    def __init__(self, show_widget, parent=None):
        self._shot_widget = show_widget
        super(ShotInfoWidget, self).__init__(parent=parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ShotInfoWidget, self).ui()

        self._shot_title_breadcrumb = breadcrumb.BreadcrumbFrame()
        self._shot_icon_frame = QFrame()
        self._shot_icon_frame.setFrameShape(QFrame.StyledPanel)
        self._shot_icon_frame.setFrameShadow(QFrame.Sunken)
        self._shot_icon_frame.setLineWidth(3)
        self._shot_icon_frame.setStyleSheet('background-color: rgba(60, 60, 60, 100); border-radius:5px;')
        shot_icon_layout = QHBoxLayout()
        shot_icon_layout.setContentsMargins(0, 0, 0, 0)
        shot_icon_layout.setSpacing(0)
        self._shot_icon_frame.setLayout(shot_icon_layout)
        self._shot_icon_lbl = QLabel()
        self._shot_icon_lbl.setAlignment(Qt.AlignCenter)
        self._shot_icon_lbl.setPixmap(tpDcc.ResourcesMgr().pixmap('default'))
        self._shot_toolbar_layout = QVBoxLayout()
        self._shot_toolbar_layout.setContentsMargins(2, 2, 2, 2)
        self._shot_toolbar_layout.setSpacing(5)

        shot_icon_layout.addLayout(self._shot_toolbar_layout)
        shot_icon_layout.addWidget(self._shot_icon_lbl)

        self.main_layout.addWidget(self._shot_title_breadcrumb)
        self.main_layout.addWidget(self._shot_icon_frame)

    def _init(self):
        """
        Internal function that initializes sequence info widget
        """

        if not self._shot_widget:
            return

        self._shot_title_breadcrumb.set_items([{'text': self._shot_widget.shot.get_name()}])
        thumb_icon = self._shot_widget.get_thumbnail_icon()
        thumb_size = artellapipe.ShotsMgr().config.get('thumb_size')
        self._shot_icon_lbl.setPixmap(
            thumb_icon.pixmap(thumb_icon.availableSizes()[-1]).scaled(thumb_size[0], thumb_size[1], Qt.KeepAspectRatio))

        self._shot_toolbar = self._create_sequence_toolbar()
        self._status_stack = StatusStack(shot_widget=self._shot_widget)
        self._status_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._shot_toolbar_layout.addWidget(self._shot_toolbar)
        self.main_layout.addWidget(self._status_stack)

    def _create_sequence_toolbar(self):
        """
        Creates toolbar widget for the sequence
        """

        toolbar_widget = QWidget()
        toolbar_widget.setMaximumWidth(40)
        toolbar_layout = QVBoxLayout()
        toolbar_layout.setContentsMargins(2, 2, 2, 2)
        toolbar_layout.setSpacing(5)
        toolbar_widget.setLayout(toolbar_layout)

        artella_btn = QToolButton()
        artella_btn.setText('Artella')
        artella_btn.setIcon(tpDcc.ResourcesMgr().icon('artella'))
        artella_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        view_locally_btn = QToolButton()
        view_locally_btn.setText('Folder')
        view_locally_btn.setIcon(tpDcc.ResourcesMgr().icon('folder'))
        view_locally_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        toolbar_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        toolbar_layout.addWidget(artella_btn)
        toolbar_layout.addWidget(view_locally_btn)
        toolbar_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        artella_btn.clicked.connect(self._on_open_artella)
        view_locally_btn.clicked.connect(self._on_view_locally)

        return toolbar_widget

    def _on_open_artella(self):
        """
        Internal callback function that is called when the user presses shot Artella button
        """

        if not self._shot_widget:
            return

        self._shot_widget.shot.open_in_artella()

    def _on_view_locally(self):
        """
        Internal callback function that is called when the user presses shot View Locally button
        """

        if not self._shot_widget:
            return

        self._shot_widget.shot.view_locally()


class StatusStack(base.BaseWidget, object):
    def __init__(self, shot_widget, parent=None):

        self._shot_widget = shot_widget

        super(StatusStack, self).__init__(parent=parent)

    def ui(self):
        super(StatusStack, self).ui()

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        buttons_group = QButtonGroup(self)
        buttons_group.setExclusive(True)

        working_icon = tpDcc.ResourcesMgr().icon('working')
        published_icon = tpDcc.ResourcesMgr().icon('box')

        self._working_btn = QPushButton('Working')
        self._working_btn.setIcon(working_icon)
        self._working_btn.setMinimumWidth(80)
        self._working_btn.setCheckable(True)
        self._published_btn = QPushButton('Published')
        self._published_btn.setIcon(published_icon)
        self._published_btn.setMinimumWidth(80)
        self._published_btn.setCheckable(True)

        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        buttons_layout.addWidget(self._working_btn)
        buttons_layout.addWidget(self._published_btn)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        buttons_group.addButton(self._working_btn)
        buttons_group.addButton(self._published_btn)
        self._working_btn.setChecked(True)

        self._status_stack = stack.SlidingStackedWidget()
        self._working_status_widget = WorkingShotInfo(shot_widget=self._shot_widget)
        self._working_status_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._published_status_widget = PublishedShotInfo(shot_widget=self._shot_widget)
        self._published_status_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._status_stack.addWidget(self._working_status_widget)
        self._status_stack.addWidget(self._published_status_widget)

        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addWidget(self._status_stack)

    def setup_signals(self):
        self._status_stack.animFinished.connect(self._on_stack_anim_finished)
        self._working_btn.clicked.connect(self._on_working_button_clicked)
        self._published_btn.clicked.connect(self._on_published_button_clicked)

    def _on_stack_anim_finished(self):
        """
        Internal callback function that is called when stack animation finish
        """

        self._working_btn.setEnabled(True)
        self._published_btn.setEnabled(True)

    def _on_working_button_clicked(self):
        if self._status_stack.currentWidget() == self._working_status_widget:
            return

        self._working_btn.setEnabled(False)
        self._published_btn.setEnabled(False)
        self._status_stack.slide_in_index(0)

    def _on_published_button_clicked(self):
        if self._status_stack.currentWidget() == self._published_status_widget:
            return

        self._working_btn.setEnabled(False)
        self._published_btn.setEnabled(False)
        self._status_stack.slide_in_index(1)


class ShotFileButton(base.BaseWidget, object):

    checkVersions = Signal(str, object)

    def __init__(self, shot_widget, status, shot_file_type, shot_file_type_name, shot_file_icon, parent=None):

        self._shot_file_icon = shot_file_icon
        self._status = status
        self._shot_file_type = shot_file_type
        self._shot_file_type_name = shot_file_type_name or shot_file_type
        self._shot_widget = shot_widget

        super(ShotFileButton, self).__init__(parent=parent)

        self._check_availability()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(ShotFileButton, self).ui()

        folder_icon = tpDcc.ResourcesMgr().icon('artella')

        self._file_btn = QPushButton()
        self._file_btn.setText(self._shot_file_type_name)
        self._file_btn.setIcon(self._shot_file_icon)
        self._versions_btn = QPushButton()
        self._versions_btn.setFixedWidth(25)
        self._versions_btn.setIcon(folder_icon)

        frame = QFrame()
        frame.setFixedWidth(1)
        frame.setStyleSheet('background-color: rgb(60, 60, 60);')

        self.main_layout.addWidget(self._file_btn)
        self.main_layout.addWidget(frame)
        self.main_layout.addWidget(self._versions_btn)

    def setup_signals(self):
        self._file_btn.clicked.connect(partial(self._on_open_shot_file, self._shot_file_type))
        self._versions_btn.clicked.connect(partial(self._on_check_working_versions, self._shot_file_type))

    def _check_availability(self):
        """
        Internal function that updates enabled status of the buttons depending of the asset file availability
        """

        if not self._shot_widget:
            return

        file_path = self._get_file_path()
        if not file_path or not os.path.exists(file_path):
            self._file_btn.setEnabled(False)
            self._versions_btn.setEnabled(False)

    def _get_file_path(self):
        """
        Internal function that returns asset file path linked to the button
        :return: str
        """

        file_path = self._shot_widget.shot.get_file(file_type=self._shot_file_type, status=self._status)

        return file_path

    def _on_open_shot_file(self, file_type):
        """
        Internal callback function that is called when the user clicks on open file button
        """

        if not self._shot_widget:
            return

        if not file_type or file_type not in self._shot_widget.shot.FILES:
            return

        self._shot_widget.shot.open_file(file_type=self._shot_file_type, status=self._status)

    def _on_check_working_versions(self, file_type):
        """
        Internal callback function that is called when the user clicks on a check version button
        """

        if not self._shot_widget:
            return

        if not file_type or file_type not in self._shot_widget.shot.FILES:
            return

        file_path = self._get_file_path()
        asset_history = artellalib.get_file_history(file_path)
        asset_versions = asset_history.versions
        if not asset_versions:
            return

        self.checkVersions.emit(file_path, asset_versions)


class ShotVersionsTree(QTreeWidget, object):
    def __init__(self, parent=None):
        super(ShotVersionsTree, self).__init__(parent)

        self.header().hide()


class WorkingShotInfo(base.BaseWidget, object):
    def __init__(self, shot_widget, parent=None):

        self._shot_widget = shot_widget
        self._file_buttons = dict()

        super(WorkingShotInfo, self).__init__(parent=parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(WorkingShotInfo, self).ui()

    def _init(self):
        if not self._shot_widget:
            return

        self._buttons_widget = self._create_asset_files_buttons()

        self.main_layout.addLayout(dividers.DividerLayout())
        self.main_layout.addWidget(self._buttons_widget)
        self.main_layout.addLayout(dividers.DividerLayout())

        self._stack = stack.SlidingStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self._stack)

        no_shots_widget = QFrame()
        no_shots_widget.setFrameShape(QFrame.StyledPanel)
        no_shots_widget.setFrameShadow(QFrame.Sunken)
        no_shots_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        no_shots_layout = QVBoxLayout()
        no_shots_layout.setContentsMargins(0, 0, 0, 0)
        no_shots_layout.setSpacing(0)
        no_shots_widget.setLayout(no_shots_layout)
        no_shots_lbl = QLabel()
        no_items_pixmap = tpDcc.ResourcesMgr().pixmap('no_shot_selected')
        no_shots_lbl.setPixmap(no_items_pixmap)
        no_shots_lbl.setAlignment(Qt.AlignCenter)
        no_shots_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        no_shots_layout.addWidget(no_shots_lbl)
        no_shots_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        version_widget = QWidget()
        version_layout = QHBoxLayout()
        version_layout.setContentsMargins(2, 2, 2, 2)
        version_layout.setSpacing(2)
        version_widget.setLayout(version_layout)

        version_splitter = QSplitter(Qt.Horizontal)
        version_layout.addWidget(version_splitter)

        self._versions_tree = ShotVersionsTree()
        version_splitter.addWidget(self._versions_tree)

        version_splitter.addWidget(QPushButton('Test'))

        self._stack.addWidget(no_shots_widget)
        self._stack.addWidget(version_splitter)

        self._versions_tree.itemClicked.connect(self._on_version_item_clicked)

    def _create_asset_files_buttons(self):
        """
        Internal function that creates file buttons for the asset
        """

        if not self._shot_widget:
            return

        file_buttons_widget = grid.GridWidget()
        file_buttons_widget.setStyleSheet('QTableWidget::item { margin-left: 6px; }')
        file_buttons_widget.setColumnCount(3)
        file_buttons_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        file_buttons_widget.setShowGrid(False)
        file_buttons_widget.setFocusPolicy(Qt.NoFocus)
        file_buttons_widget.horizontalHeader().hide()
        file_buttons_widget.verticalHeader().hide()
        file_buttons_widget.resizeRowsToContents()
        file_buttons_widget.resizeColumnsToContents()
        file_buttons_widget.setSelectionMode(QAbstractItemView.NoSelection)

        files_btn = list()
        for file_type in self._shot_widget.shot.FILES:
            file_type_name = artellapipe.FilesMgr().get_file_type_name(file_type)
            file_btn = ShotFileButton(
                self._shot_widget, defines.ArtellaFileStatus.WORKING,
                file_type, file_type_name, tpDcc.ResourcesMgr().icon(file_type))
            files_btn.append(file_btn)
            file_btn.checkVersions.connect(self._on_check_versions)
            self._file_buttons[file_type] = file_btn
            row, col = file_buttons_widget.first_empty_cell()
            file_buttons_widget.addWidget(row, col, file_btn)
            file_buttons_widget.resizeRowsToContents()

        if files_btn:
            file_buttons_widget.setFixedHeight(file_buttons_widget.rowCount() * files_btn[0].height() + 5)

        return file_buttons_widget

    def _on_check_versions(self, file_path, versions):
        """
        Internal callback function that is called when asset versions check are called
        :param versions: list(tuple(int, ArtellaFileVerionMetaData))
        """

        self._versions_tree.clear()
        if not versions:
            return

        root_item = QTreeWidgetItem(self._versions_tree, [os.path.basename(file_path)])
        root_item.setToolTip(0, file_path)
        self._versions_tree.addTopLevelItem(root_item)

        for version_number, version_info in versions:
            version_item = QTreeWidgetItem(root_item, [str(version_number)])
            version_item.version = version_number
            version_item.version_info = version_info
            root_item.addChild(version_item)

        self._versions_tree.expandAll()

        self._stack.slide_in_index(1)

    def _on_version_item_clicked(self, item):
        version_info = item.version_info
        print(version_info)


class PublishedShotInfo(base.BaseWidget, object):
    def __init__(self, shot_widget, parent=None):

        self._shot_widget = shot_widget

        super(PublishedShotInfo, self).__init__(parent=parent)

    def ui(self):
        super(PublishedShotInfo, self).ui()

        self.main_layout.addWidget(QPushButton('TEST'))


artellapipe.register.register_class('ShotInfo', ShotInfoWidget)
