#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget that allows to sync user local folders
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import weakref
import traceback
from copy import deepcopy

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDccLib as tp
from tpQtLib.core import base
from tpQtLib.widgets import search

import artellapipe
from artellapipe.core import artellalib
from artellapipe.gui import progressbar
from artellapipe.tools.bugtracker import bugtracker


class ArtellaLocalTreeModel(QFileSystemModel, object):
    def __init__(self):
        super(ArtellaLocalTreeModel, self).__init__()

        self.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.setNameFilterDisables(False)
        self.setReadOnly(True)


class HideFileTypesProxy(QSortFilterProxyModel, object):
    def __init__(self, excludes, *args, **kwargs):
        super(HideFileTypesProxy, self).__init__(*args, **kwargs)

        self._excludes = excludes[:]

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        name = index.data()

        for exc in self._excludes:
            if name.endswith(exc):
                return False

        return True

    def get_excludes(self):
        return self._excludes


class ArtellaLocalTreeView(QTreeView, object):

    selectedItems = Signal(list)

    def __init__(self, project, parent=None):
        super(ArtellaLocalTreeView, self).__init__(parent=parent)

        self._project = project
        self._model = None

        self._init()

        for i in range(1, 4):
            self.hideColumn(i)

    def get_selected_names(self):
        """
        Returns a list of selected item names
        :return: list(str)
        """

        selected = self.selectionModel().selectedIndexes()
        return [self._model.data(index, self._model.FileNameRole) for index in selected if index.column() == 0]

    def get_selected_paths(self):
        """
        Returns a list of selected item paths
        :return: list(str)
        """

        selected = self.selectionModel().selectedIndexes()
        return [self._model.data(index, self._model.FilePathRole) for index in selected if index.column() == 0]

    def get_selected_items_data(self):
        """
        Returns a list of selected items
        :return: list(dict)
        """

        selected = self.selectionModel().selectedIndexes()

        selected_data = list()
        for index in selected:
            if index.column() == 0:
                data = dict()
                data['name'] = self.model().data(index, self._model.FileNameRole)
                data['path'] = self.model().data(index, self._model.FilePathRole)
                data['icon'] = self.model().data(index, self._model.FileIconRole)
                selected_data.append(data)

        return selected_data

    def set_excludes_extensions(self, excluded_extensions):
        """
        Sets the extensions that should be excluded by the view
        :param excluded_extensions: list(str)
        """

        root_path = ''
        if self._project:
            root_path = self._project.get_path()

        self.selectionModel().selectionChanged.disconnect()
        self._proxy = HideFileTypesProxy(excludes=excluded_extensions, parent=self)
        self._proxy.setDynamicSortFilter(True)
        self._proxy.setSourceModel(self._model)
        self.setModel(self._proxy)
        index = self._model.setRootPath(root_path)
        self.setRootIndex(self._proxy.mapFromSource(index))
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._on_data_loaded()

    def _init(self):
        """
        Internal function that initializes tree data
        """

        root_path = ''
        if self._project:
            root_path = self._project.get_path()

        self._model = ArtellaLocalTreeModel()
        self._proxy = HideFileTypesProxy(excludes=[], parent=self)
        self._proxy.setDynamicSortFilter(True)
        self._proxy.setSourceModel(self._model)
        self.header().setFixedHeight(30)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setModel(self._proxy)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        index = self._model.setRootPath(root_path)
        self.setRootIndex(self._proxy.mapFromSource(index))
        self.setItemsExpandable(True)

        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._model.directoryLoaded.connect(self._on_data_loaded)

    def _on_data_loaded(self):
        self.expandAll()
        self.resizeColumnToContents(0)

    def _on_selection_changed(self):

        selected_items = self.get_selected_items_data()
        self.selectedItems.emit(selected_items)


class ArtellaLocalListViewDelegateRowPainter(object):

    ICON_PADDING = tp.Dcc.get_dpi_scale(10.0)
    ICON_WIDTH = tp.Dcc.get_dpi_scale(20)
    ICON_WIDTH_NO_DPI = tp.Dcc.get_dpi_scale(29)
    ICON_TOP_OFFSET = tp.Dcc.get_dpi_scale(4)

    def __init__(self, painter, option, item, parent):
        self._parent = weakref.ref(parent)
        self._painter = painter
        self._item = item
        self._rect = deepcopy(option.rect)
        self._is_higlighted = option.showDecorationSelected and option.state & QStyle.State_Selected
        self._higlight_color = option.palette.color(QPalette.Highlight)

    def paint_row(self):
        """
        Function that paints row with delegate properties
        :return:
        """
        self._draw_background()
        self._draw_sync_status()
        text_rect = self._draw_text()
        self._draw_icon(text_rect)

    def _draw_background(self):
        """
        Internal function that draws the background of the row
        """

        color = self._higlight_color if self._is_higlighted else self._item.get_background_color()
        self._painter.fillRect(self._rect, color)

    def _draw_sync_status(self):
        """
        Internal function that draws the status icon of the row
        """

        rect2 = deepcopy(self._rect)
        new_rect = QRect()
        new_rect.setRight(rect2.left())
        new_rect.setLeft(new_rect.right() - self.ICON_WIDTH_NO_DPI + 9)
        new_rect.setBottom(rect2.top() - self.ICON_WIDTH + tp.Dcc.get_dpi_scale(6))
        new_rect.setTop(new_rect.bottom() + self.ICON_WIDTH - 2)
        sync_pixmap = self._item.get_sync_pixmap()
        if sync_pixmap:
            self._painter.drawPixmap(new_rect, sync_pixmap.scaled(self.ICON_WIDTH, self.ICON_WIDTH, Qt.KeepAspectRatio))

    def _draw_text(self):
        """
        Internal function that draws the texst of the row
        :return: QRect
        """

        old_pen = self._painter.pen()
        text_rect = deepcopy(self._rect)
        text_rect.setBottom(text_rect.bottom() + tp.Dcc.get_dpi_scale(2))
        text_rect.setLeft(text_rect.left() + tp.Dcc.get_dpi_scale(40) + 0)
        text_rect.setRight(text_rect.right() - tp.Dcc.get_dpi_scale(11))
        self._painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, os.path.basename(self._item.get_path()))
        self._painter.setPen(old_pen)

        return text_rect

    def _draw_icon(self, text_rect):
        """
        Internal function that draws the icon of the row
        :param text_rect: QRect
        """

        rect2 = deepcopy(text_rect)
        icon = self._item.get_icon()
        if icon:
            new_rect = QRect()
            new_rect.setRight(rect2.left() - tp.Dcc.get_dpi_scale(4))
            new_rect.setLeft(new_rect.right() - self.ICON_WIDTH_NO_DPI)
            new_rect.setBottom(rect2.top() - self.ICON_WIDTH + tp.Dcc.get_dpi_scale(6))
            new_rect.setTop(new_rect.bottom() + self.ICON_WIDTH - 7)
            self._painter.drawPixmap(new_rect, icon.pixmap(self.ICON_WIDTH, self.ICON_WIDTH))


class ArtellaLocalListViewDelegate(QItemDelegate, object):

    ROW_HEIGHT = 30

    def __init__(self, list_view):
        super(ArtellaLocalListViewDelegate, self).__init__()

        self._view = weakref.ref(list_view)

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        item = self._get_item(index)
        row_painter = ArtellaLocalListViewDelegateRowPainter(painter, option, item, self.view())
        row_painter.paint_row()

        check_rect = deepcopy(option.rect)
        check_rect.setRight(30)
        check_rect.setBottom(15)

    def sizeHint(self, option, index):
        hint = super(ArtellaLocalListViewDelegate, self).sizeHint(option, index)
        hint.setHeight(tp.Dcc.get_dpi_scale(self.ROW_HEIGHT))
        return hint

    def view(self):
        """
        Returns view linked to this delegate
        :return: QListView
        """

        return self._view()

    def _get_item(self, index):
        """
        Internal function that returns item from given index
        :param index: QModelIndex
        :return:
        """

        return self.view().itemFromIndex(index)


class ArtellaSyncItemStatus(object):
    WAIT = 'wait'
    RUN = 'run'
    OK = 'ok'
    ERROR = 'error'


class ArtellaSyncItem(QTreeWidgetItem, object):

    WAIT_PIXMAP = artellapipe.resource.pixmap('clock', category='icons', theme='color', extension='png')
    RUN_PIXMAP = artellapipe.resource.pixmap('clock_start', category='icons', theme='color', extension='png')
    OK_PIXMAP = artellapipe.resource.pixmap('ok', category='icons', theme='color', extension='png')
    ERROR_PIXMAP = artellapipe.resource.pixmap('error', category='icons', theme='color', extension='png')

    def __init__(self, name, path, icon, color=None, parent=None):
        super(ArtellaSyncItem, self).__init__()

        self._name = name
        self._path = path
        self._icon = icon
        self._color = color
        self._sync_status = ArtellaSyncItemStatus.WAIT
        if self._color is None:
            self._color = QColor(0, 0, 0)
            self._color.setNamedColor('#444444')

        self._parent = None
        self.set_parent(parent)

        self.setFlags(self.flags() | Qt.ItemIsSelectable)

    def parent(self):
        """
        Overrides base QTreeWidgetItem parent function to avoid deleted C++ object
        :return: QTreeWidgetItem
        """

        return self._parent

    def set_parent(self, parent):
        """
        Sets the parent of the current item
        :param parent: QTreeWidgetItem
        """

        self._parent = parent

    def get_name(self):
        """
        Returns name of the item
        :return: str
        """

        return self._name

    def get_path(self):
        """
        Returns the path of the item
        :return: str
        """

        return self._path

    def get_icon(self):
        """
        Returns icon of the item
        :return: QIcon
        """

        return self._icon

    def get_background_color(self):
        """
        Returns background color of the item
        :return: QColor
        """

        return self._color

    def get_sync_status(self):
        """
        Returns sync status of the item
        :return: str
        """

        return self._sync_status

    def set_sync_status(self, sync_status):
        """
        Sets the sync status of the item
        :param sync_status: ArtellaSyncItemStatus
        """

        self._sync_status = sync_status

    def get_sync_pixmap(self):
        """
        Returns the icon of the current sync status
        :return: QPixmap
        """

        if self._sync_status == ArtellaSyncItemStatus.WAIT:
            return None
        elif self._sync_status == ArtellaSyncItemStatus.RUN:
            return self.RUN_PIXMAP
        elif self._sync_status == ArtellaSyncItemStatus.OK:
            return self.OK_PIXMAP
        else:
            return self.ERROR_PIXMAP


class ArtellaLocalSyncTree(QTreeWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaLocalSyncTree, self).__init__(parent=parent)

        self.header().setVisible(False)
        self.setSortingEnabled(False)

        delegate = ArtellaLocalListViewDelegate(self)
        self.setItemDelegate(delegate)

    def get_items(self, skip_hidden=False):
        """
        Returns the items added to the list
        :return: list
        """

        if skip_hidden:
            return [self.topLevelItem(i) for i in range(self.topLevelItemCount()) if not self.topLevelItem(i).isHidden()]
        else:
            return [self.topLevelItem(i) for i in range(self.topLevelItemCount())]

    def set_items(self, items):
        """
        Sets paths that need to be showed in the view
        :param items: list
        """

        self.clear()

        for item in items:
            item_path = item.get('path')
            if not os.path.exists(item_path):
                continue
            if os.path.isdir(item_path):
                folder_item = self._make_item(item)
                self.addTopLevelItem(folder_item)
            elif os.path.isfile(item_path):
                file_data = self._get_file_data(item_path)
                file_item = self._make_item(file_data)
                self.addTopLevelItem(file_item)

    def _make_item(self, item_data):
        """
        Internal function that creates a folder item with given path
        :param folder_data: dict
        :return: FolderItemPath
        """

        folder_name = item_data.get('name')
        folder_path = item_data.get('path')
        folder_icon = item_data.get('icon')

        folder_item = ArtellaSyncItem(name=folder_name, path=folder_path, icon=folder_icon)

        return folder_item

    def _get_file_data(self, file_path):
        """
        Returns file data linked to given file path
        :param file_path: str
        :return: dict
        """

        file_name = os.path.basename(file_path)
        file_info = QFileInfo(file_path)
        icon_provider = QFileIconProvider()
        file_icon = icon_provider.icon(file_info)

        data = {
            'name': file_name,
            'path': file_path,
            'icon': file_icon
        }

        return data


class ArtellaPathSyncWidget(base.BaseWidget, object):

    syncOk = Signal(str)
    syncFailed = Signal(str)
    syncWarning = Signal(str)

    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaPathSyncWidget, self).__init__(parent=parent)

        self._init_filters()

    def ui(self):
        super(ArtellaPathSyncWidget, self).ui()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(splitter)

        tree_widget = QWidget()
        tree_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tree_layout = QVBoxLayout()
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(2)
        tree_widget.setLayout(tree_layout)

        filters_widget = QWidget()
        self._filters_layout = QHBoxLayout()
        self._filters_layout.setContentsMargins(2, 2, 2, 2)
        self._filters_layout.setSpacing(2)
        filters_widget.setLayout(self._filters_layout)
        self._filters_grp = QButtonGroup(self)
        self._filters_grp.setExclusive(False)

        self._tree = ArtellaLocalTreeView(project=self._project)
        tree_layout.addWidget(filters_widget)
        tree_layout.addWidget(self._tree)

        list_widget = QWidget()
        list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(2)
        list_widget.setLayout(list_layout)
        self._list_filter = search.SearchFindWidget(parent=self)
        self._list = ArtellaLocalSyncTree(project=self._project)
        self._list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_layout.addWidget(self._list_filter)
        list_layout.addWidget(self._list)

        self._progress = progressbar.ArtellaProgressBar(project=self._project)
        self._progress.setVisible(False)
        list_layout.addWidget(self._progress)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        self._sync_subfolders_cbx = QCheckBox('Sync Subfolders?')
        self._sync_subfolders_cbx.setMaximumWidth(110)
        self._sync_btn = QPushButton('Sync')
        buttons_layout.addWidget(self._sync_subfolders_cbx)
        buttons_layout.addWidget(self._sync_btn)
        list_layout.addLayout(buttons_layout)

        splitter.addWidget(tree_widget)
        splitter.addWidget(list_widget)

    def setup_signals(self):
        self._tree.selectedItems.connect(self._on_selected_items)
        self._sync_btn.clicked.connect(self._on_sync)
        self._list_filter.textChanged.connect(self._on_update_name)

    def _init_filters(self):
        """
        Internal function that is called when Tree View loads all the data
        """

        root_path = self._tree._model.rootPath()
        if not os.path.exists(root_path):
            return

        extensions_dict = dict()

        for d, _, files in os.walk(root_path):
            for f in files:
                file_path = os.path.join(d, f)
                ext = os.path.splitext(file_path)[-1]
                if ext not in extensions_dict:
                    file_info = QFileInfo(file_path)
                    icon_provider = QFileIconProvider()
                    file_icon = icon_provider.icon(file_info)
                    extensions_dict[ext] = file_icon

        for ext, ext_icon in extensions_dict.items():
            filter_btn = QPushButton(ext[1:])
            filter_btn.setMinimumWidth(45)
            filter_btn.setCheckable(True)
            filter_btn.setChecked(True)
            filter_btn.setIcon(ext_icon)
            filter_btn.toggled.connect(self._on_update_filters)
            self._filters_grp.addButton(filter_btn)
            self._filters_layout.addWidget(filter_btn)
        self._filters_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self._update_filters()

    def _update_filters(self):
        """
        Internal function that updates filters
        """

        extensions_to_hide = list()
        for btn in self._filters_grp.buttons():
            ext = '.{}'.format(btn.text())
            if btn.isChecked():
                continue
            extensions_to_hide.append(ext)

        self._tree.set_excludes_extensions(extensions_to_hide)

    def _update_name(self, name):
        """
        Internal function that updates name to show
        """

        for i in range(self._list.topLevelItemCount()):
            item = self._list.topLevelItem(i)
            item.setHidden(name not in item.get_name())

    def _on_selected_items(self, selected_items):
        """
        Internal callback function that is called when the user selects items in the tree widget
        :param selected_items: list(dict)
        """

        self._list.set_items(selected_items)

    def _on_sync(self):
        """
        Internal callback function that is called when the user presses Sync button
        """

        items_to_sync = self._list.get_items(skip_hidden=True)
        if not items_to_sync:
            msg = 'Select files and folers to sync before syncing!'
            artellapipe.logger.warning(msg)
            self.syncWarning.emit(msg)
            return

        self._progress.set_minimum(0)
        self._progress.set_maximum(len(items_to_sync))
        self._progress.setVisible(True)
        for item in items_to_sync:
            item.set_sync_status(ArtellaSyncItemStatus.WAIT)
        self._list.repaint()

        for i, item in enumerate(items_to_sync):
            item_path = item.get_path()
            item_name = os.path.basename(item_path)
            item.set_sync_status(ArtellaSyncItemStatus.RUN)
            self._progress.set_value(i + 1)
            self._progress.set_text('Syncing file: {}'.format(item_name))
            self._list.repaint()
            try:
                valid_sync = True
                if os.path.isfile(item_path):
                    valid_sync = artellalib.synchronize_file(item_path)
                elif os.path.isdir(item_path):
                    if self._sync_subfolders_cbx.isChecked():
                        valid_sync = artellalib.synchronize_path_with_folders(item_path, True)
                    else:
                        valid_sync = artellalib.synchronize_path(item_path)
                if valid_sync:
                    item.set_sync_status(ArtellaSyncItemStatus.OK)
                    self._list.repaint()
                    self.syncOk.emit('File {} synced successfully!'.format(item_name))
                else:
                    item.set_sync_status(ArtellaSyncItemStatus.ERROR)
                    self._list.repaint()
                    self.syncFailed.emit('Error while syncing file {} from Artella server!'.format(item_name))
            except Exception as e:
                item.set_sync_status(ArtellaSyncItemStatus.ERROR)
                self._list.repaint()
                if os.path.isfile(item_path):
                    msg = 'Error while syncing file: {}'.format(item_name)
                else:
                    msg = 'Error while syncing folder: {}'.format(item_name)
                artellapipe.logger.error(msg)
                artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))
                bugtracker.ArtellaBugTracker.run(self._project, traceback.format_exc())
                self._progress.set_value(0)
                self._progress.set_text('')
                self.syncFailed.emit(msg)
                break

        self._progress.set_value(0)
        self._progress.set_text('')
        self._progress.setVisible(False)

    def _on_update_filters(self):
        self._update_filters()

    def _on_update_name(self, text):
        self._update_name(text)
