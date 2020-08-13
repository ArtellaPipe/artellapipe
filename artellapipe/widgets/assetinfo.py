#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget that shows asset information
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

import artellapipe
from artellapipe.core import defines
from artellapipe.libs.artella.core import artellalib


class AssetInfoWidget(base.BaseWidget, object):
    def __init__(self, asset_widget, parent=None):

        self._asset_widget = asset_widget

        super(AssetInfoWidget, self).__init__(parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(AssetInfoWidget, self).ui()

        self._title_breadcrumb = breadcrumb.BreadcrumbFrame()
        self._asset_icon_frame = QFrame()
        self._asset_icon_frame.setFrameShape(QFrame.StyledPanel)
        self._asset_icon_frame.setFrameShadow(QFrame.Sunken)
        self._asset_icon_frame.setLineWidth(3)
        self._asset_icon_frame.setStyleSheet('background-color: rgba(60, 60, 60, 100); border-radius:5px;')
        asset_icon_layout = QHBoxLayout()
        asset_icon_layout.setContentsMargins(0, 0, 0, 0)
        asset_icon_layout.setSpacing(0)
        self._asset_icon_frame.setLayout(asset_icon_layout)
        self._asset_icon_lbl = QLabel()
        self._asset_icon_lbl.setAlignment(Qt.AlignCenter)
        self._asset_icon_lbl.setPixmap(tpDcc.ResourcesMgr().pixmap('default'))
        self._asset_toolbar_layout = QVBoxLayout()
        self._asset_toolbar_layout.setContentsMargins(2, 2, 2, 2)
        self._asset_toolbar_layout.setSpacing(5)

        asset_icon_layout.addLayout(self._asset_toolbar_layout)
        asset_icon_layout.addWidget(self._asset_icon_lbl)

        self.main_layout.addWidget(self._title_breadcrumb)
        self.main_layout.addWidget(self._asset_icon_frame)
        # self.main_layout.addLayout(dividers.DividerLayout())

    def reset(self):
        """
        Restores initial values of the AssetInfoWidget
        """

        pass

    def _init(self):
        """
        Internal function that initializes asset info widget
        """

        if not self._asset_widget:
            return

        self._title_breadcrumb.set_items([{'text': self._asset_widget.asset.get_name()}])
        thumb_icon = self._asset_widget.get_thumbnail_icon()
        thumb_size = artellapipe.AssetsMgr().config.get('thumb_size')
        self._asset_icon_lbl.setPixmap(
            thumb_icon.pixmap(thumb_icon.availableSizes()[-1]).scaled(thumb_size[0], thumb_size[1], Qt.KeepAspectRatio))

        self._asset_toolbar = self._create_asset_toolbar()
        self._status_stack = StatusStack(asset_widget=self._asset_widget)
        self._status_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._asset_toolbar_layout.addWidget(self._asset_toolbar)
        self.main_layout.addWidget(self._status_stack)

    def _create_asset_toolbar(self):
        """
        Creates toolbar widget for the asset
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
        Internal callback function that is called when the user presses asset Artella button
        """

        if not self._asset_widget:
            return

        self._asset_widget.asset.open_in_artella()

    def _on_view_locally(self):
        """
        Internal callback function that is called when the user presses asset View Locally button
        """

        if not self._asset_widget:
            return

        self._asset_widget.asset.view_locally()


class StatusStack(base.BaseWidget, object):
    def __init__(self, asset_widget, parent=None):

        self._asset_widget = asset_widget

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
        self._working_status_widget = WorkingAssetInfo(asset_widget=self._asset_widget)
        self._working_status_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._published_status_widget = PublishedAssetInfo(asset_widget=self._asset_widget)
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


class AssetFileButton(base.BaseWidget, object):

    checkVersions = Signal(str, object)

    def __init__(self, asset_widget, status, asset_file_type, asset_file_type_name, asset_file_icon, parent=None):

        self._asset_file_icon = asset_file_icon
        self._status = status
        self._asset_file_type = asset_file_type
        self._asset_file_type_name = asset_file_type_name or asset_file_type
        self._asset_widget = asset_widget

        super(AssetFileButton, self).__init__(parent=parent)

        self._check_availability()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(AssetFileButton, self).ui()

        folder_icon = tpDcc.ResourcesMgr().icon('artella')

        self._file_btn = QPushButton()
        self._file_btn.setText(self._asset_file_type_name)
        self._file_btn.setIcon(self._asset_file_icon)
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
        self._file_btn.clicked.connect(partial(self._on_open_asset_file, self._asset_file_type))
        self._versions_btn.clicked.connect(partial(self._on_check_working_versions, self._asset_file_type))

    def _check_availability(self):
        """
        Internal function that updates enabled status of the buttons depending of the asset file availability
        """

        if not self._asset_widget:
            return

        file_path = self._get_file_path()
        if not file_path or not os.path.exists(file_path):
            self._disable_state()
            return

        self._enable_state()

    def _enable_state(self):
        """
        Internal function that enables the functionality of asset file buttons
        """

        self._file_btn.setEnabled(True)
        self._versions_btn.setEnabled(True)

    def _disable_state(self):
        """
        Internal function that disables the functionality of asset file buttons
        """

        self._file_btn.setEnabled(False)
        self._versions_btn.setEnabled(False)

    def _get_file_path(self):
        """
        Internal function that returns asset file path linked to the button
        :return: str
        """

        file_path = self._asset_widget.asset.get_file(file_type=self._asset_file_type, status=self._status)

        return file_path

    def _on_open_asset_file(self, file_type):
        """
        Internal callback function that is called when the user clicks on open file button
        """

        if not self._asset_widget:
            return

        if not file_type or file_type not in self._asset_widget.asset.FILES:
            return

        return self._asset_widget.asset.open_file(file_type=self._asset_file_type, status=self._status)

    def _on_check_working_versions(self, file_type):
        """
        Internal callback function that is called when the user clicks on a check version button
        """

        if not self._asset_widget:
            return

        if not file_type or file_type not in self._asset_widget.asset.FILES:
            return

        file_path = self._get_file_path()
        asset_history = artellalib.get_file_history(file_path)
        asset_versions = asset_history.versions
        if not asset_versions:
            return

        self.checkVersions.emit(file_path, asset_versions)


class AssetVersionsTree(QTreeWidget, object):
    def __init__(self, parent=None):
        super(AssetVersionsTree, self).__init__(parent)

        self.header().hide()


class WorkingAssetInfo(base.BaseWidget, object):

    STATUS = defines.ArtellaFileStatus.WORKING

    def __init__(self, asset_widget, parent=None):

        self._asset_widget = asset_widget
        self._file_buttons = dict()

        super(WorkingAssetInfo, self).__init__(parent=parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(WorkingAssetInfo, self).ui()

    def _init(self):
        if not self._asset_widget:
            return

        self._buttons_widget = self._create_asset_files_buttons()

        self.main_layout.addLayout(dividers.DividerLayout())
        self.main_layout.addWidget(self._buttons_widget)
        self.main_layout.addLayout(dividers.DividerLayout())

        self._stack = stack.SlidingStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self._stack)

        no_items_widget = QFrame()
        no_items_widget.setFrameShape(QFrame.StyledPanel)
        no_items_widget.setFrameShadow(QFrame.Sunken)
        no_items_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        no_items_layout = QVBoxLayout()
        no_items_layout.setContentsMargins(0, 0, 0, 0)
        no_items_layout.setSpacing(0)
        no_items_widget.setLayout(no_items_layout)
        no_items_lbl = QLabel()
        no_items_pixmap = tpDcc.ResourcesMgr().pixmap('no_asset_selected')
        no_items_lbl.setPixmap(no_items_pixmap)
        no_items_lbl.setAlignment(Qt.AlignCenter)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        no_items_layout.addWidget(no_items_lbl)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        version_widget = QWidget()
        version_layout = QHBoxLayout()
        version_layout.setContentsMargins(2, 2, 2, 2)
        version_layout.setSpacing(2)
        version_widget.setLayout(version_layout)

        version_splitter = QSplitter(Qt.Horizontal)
        version_layout.addWidget(version_splitter)

        self._versions_tree = AssetVersionsTree()
        version_splitter.addWidget(self._versions_tree)

        version_splitter.addWidget(QPushButton('Test'))

        self._stack.addWidget(no_items_widget)
        self._stack.addWidget(version_splitter)

        self._versions_tree.itemClicked.connect(self._on_version_item_clicked)

    def _create_asset_files_buttons(self):
        """
        Internal function that creates file buttons for the asset
        """

        if not self._asset_widget:
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
        must_file_types = artellapipe.AssetsMgr().must_file_types
        for file_type in self._asset_widget.asset.FILES:
            if must_file_types:
                if file_type not in must_file_types:
                    continue
            file_type_name = artellapipe.FilesMgr().get_file_type_name(file_type)
            file_btn = AssetFileButton(
                self._asset_widget, self.STATUS,
                file_type, file_type_name, tpDcc.ResourcesMgr().icon(file_type))
            files_btn.append(file_btn)
            file_btn.checkVersions.connect(self._on_check_versions)
            self._file_buttons[file_type] = file_btn
            row, col = file_buttons_widget.first_empty_cell()
            file_buttons_widget.addWidget(row, col, file_btn)
            file_buttons_widget.resizeRowsToContents()

        if files_btn:
            file_buttons_widget.setFixedHeight(file_buttons_widget.rowCount() * files_btn[0].height() + 10)

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


class PublishedAssetInfo(WorkingAssetInfo, object):

    STATUS = defines.ArtellaFileStatus.PUBLISHED

    def __init__(self, asset_widget, parent=None):
        super(PublishedAssetInfo, self).__init__(asset_widget=asset_widget, parent=parent)
