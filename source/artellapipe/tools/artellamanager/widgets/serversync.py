#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to easily sync files from Artella server
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import webbrowser
import traceback
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import python

from tpQtLib.core import base
from tpQtLib.widgets import stack, breadcrumb, treewidgets

import artellapipe
from artellapipe.utils import worker
from artellapipe.core import defines, artellalib, artellaclasses
from artellapipe.gui import waiter, progressbar
from artellapipe.tools.bugtracker import bugtracker


class ArtellaSyncWaiter(waiter.ArtellaWaiter, object):
    def __init__(self, parent=None):
        super(ArtellaSyncWaiter, self).__init__(parent=parent)

    def get_path(self):
        return None


class ArtellaSyncWidget(base.BaseWidget, object):

    workerFailed = Signal(str, str)
    syncOk = Signal(str)
    syncFailed = Signal(str)
    syncWarning = Signal(str)
    createAsset = Signal(object)

    def __init__(self, project, parent=None):

        self._project = project
        self._artella_worker = worker.Worker(app=QApplication.instance())
        self._artella_worker.workCompleted.connect(self._on_artella_worker_completed)
        self._artella_worker.workFailure.connect(self._on_artella_worker_failed)
        self._artella_worker.start()

        self._trees = dict()
        self._last_add = None

        super(ArtellaSyncWidget, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaSyncWidget, self).ui()

        self._toolbar = QToolBar()
        self.main_layout.addWidget(self._toolbar)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._stack = stack.SlidingStackedWidget()
        self._waiter = ArtellaSyncWaiter()
        self._breadcrumb = breadcrumb.BreadcrumbFrame()
        self._queue_widget = ArtellaSyncQueueWidget(project=self._project)

        back_icon = artellapipe.resource.icon('back')
        self._back_btn = QPushButton()
        self._back_btn.setIcon(back_icon)

        next_icon = artellapipe.resource.icon('forward')
        self._next_btn = QPushButton()
        self._next_btn.setIcon(next_icon)

        self._add_all_to_queue_btn = QPushButton('Add all to sync queue')

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(2)
        top_layout.addWidget(self._back_btn)
        top_layout.addWidget(self._breadcrumb)
        top_layout.addWidget(self._next_btn)

        stack_widget = QWidget()
        stack_layout = QVBoxLayout()
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(2)
        stack_widget.setLayout(stack_layout)
        stack_layout.addLayout(top_layout)
        stack_layout.addWidget(self._stack)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(2, 2, 2, 2)
        bottom_layout.setSpacing(2)
        bottom_layout.addWidget(self._add_all_to_queue_btn)

        splitter.addWidget(stack_widget)
        splitter.addWidget(self._queue_widget)

        self.main_layout.addWidget(splitter)

        self._stack.addWidget(self._waiter)

        self._reset_title()

        self._init()
        
        self._setup_toolbar()

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._back_btn.clicked.connect(self._on_back)
        self._next_btn.clicked.connect(self._on_next)
        self._queue_widget.syncOk.connect(self.syncOk.emit)
        self._queue_widget.syncWarning.connect(self.syncWarning.emit)
        self._queue_widget.syncFailed.connect(self.syncFailed.emit)

    def add_item_to_queue_list(self, item):
        """
        Adds given item to queue list
        :param item: ArtellaSyncItem
        """

        return self._queue_widget.add_items(item)

    def worker_is_running(self):
        """
        Returns whether Artella worker is running or not
        """

        return self._artella_worker.isRunning()

    def stop_artella_worker(self):
        """
        Forces the stop of the Artella worker if running
        """

        if self.worker_is_running():
            self._artella_worker.requestInterruption()

    def _init(self):
        """
        Internal function that initializes tree
        """

        assets_path = self._project.get_assets_path()
        self._add_tree(assets_path)

    def _setup_toolbar(self):
        """
        Internal function that setup menu bar
        """

        refresh_icon = artellapipe.resource.icon('refresh')
        queue_icon = artellapipe.resource.icon('queue')
        delete_icon = artellapipe.resource.icon('delete')

        refresh_btn = QToolButton()
        refresh_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        refresh_action = QAction(refresh_icon, 'Refresh', refresh_btn)
        refresh_btn.setDefaultAction(refresh_action)
        queue_btn = QToolButton()
        queue_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        queue_action = QAction(queue_icon, 'Add All Items to Sync Queue', queue_btn)
        queue_btn.setDefaultAction(queue_action)
        remove_queue_btn = QToolButton()
        remove_queue_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        remove_queue_action = QAction(delete_icon, 'Clear Sync Queue', remove_queue_btn)
        remove_queue_btn.setDefaultAction(remove_queue_action)

        refresh_btn.clicked.connect(self._on_refresh)
        queue_btn.clicked.connect(self._on_add_all_items_to_sync_queue)
        remove_queue_btn.clicked.connect(self._on_clear_sync_queue)

        self._toolbar.addWidget(refresh_btn)
        self._toolbar.addWidget(queue_btn)
        self._toolbar.addWidget(remove_queue_btn)

    def _update_title(self):
        """
        Sets the title of the breadcrumb
        """

        def _get_tree_selected_items(tree, tree_paths):
            current_path = tree.get_path()
            if current_path not in self._trees:
                return
            selected_items = tree.selectedItems()
            if selected_items:
                selected_item = selected_items[0]
                tree_paths.append(selected_item.get_name())
            parent_path = self._trees[current_path]['parent']
            if parent_path:
                parent_tree = self._trees[parent_path]['tree']
                _get_tree_selected_items(parent_tree, tree_paths)

        tree_paths = list()
        current_tree = self._stack.currentWidget()
        _get_tree_selected_items(current_tree, tree_paths)
        tree_paths.reverse()

        if not tree_paths:
            return False

        self._breadcrumb.set(tree_paths)

        return True

    def _reset_title(self):
        """
        Internal function that resets the title of the breadcrumb
        """

        self._breadcrumb.set(['Retrieving data from Artella ...'])

    def _show_loading_widget(self):
        """
        Internal function that shows the loading widget
        """

        self._back_btn.setVisible(False)
        self._next_btn.setVisible(False)
        self._toolbar.setVisible(False)
        self._stack.slide_in_index(0)

    def _slide_in_index(self, index):
        """
        Internal function that slides index and also shows hided UI during Artella work
        :param index: int
        """

        self._back_btn.setVisible(True)
        self._next_btn.setVisible(True)
        self._toolbar.setVisible(True)
        self._stack.slide_in_index(index)

    def _add_tree(self, path):
        """
        Internal callback function that adds a new tree into the stack
        :param path: str
        """

        current_tree = self._stack.currentWidget()
        parent_path = current_tree.get_path()

        self._show_loading_widget()

        if path in self._trees:
            sync_tree = self._trees[path]['tree']
            index = self._trees[path]['index']
        else:
            sync_tree = self._create_tree(path)
            self._stack.addWidget(sync_tree)
            index = self._stack.indexOf(sync_tree)
            self._trees[path] = {'tree': sync_tree, 'index': index, 'parent': parent_path}
            self._artella_worker.queue_work(sync_tree.update_data, {'index': index})
            self._last_add = path

            self._trees[path]['parent'] = current_tree.get_path()

        return sync_tree, index

    def _create_tree(self, path):
        """
        Creates a new empty ArtellaSyncTree
        :param path: str
        :return: ArtellaSyncTree
        """

        sync_tree = ArtellaSyncTree(project=self._project, path=path)
        sync_tree.itemClicked.connect(self._on_item_clicked)
        sync_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        sync_tree.updateBreadcrumb.connect(self._on_update_breadcrumb)
        sync_tree.addToSyncQueue.connect(self._on_add_item_to_sync_queue)
        sync_tree.forceRefresh.connect(self._on_refresh)
        sync_tree.addAllItemsToSyncQueue.connect(self._on_add_all_items_to_sync_queue)
        sync_tree.createAsset.connect(self._on_create_new_asset)

        return sync_tree

    def _remove_tree(self, path):
        """
        Internal function that removes tree with given path
        :param path: str
        :return:
        """

        if path not in self._trees:
            return

        self._stack.removeWidget(self._trees[path]['tree'])
        self._trees[path]['tree'].deleteLater()
        self._trees.pop(path)

    def _on_artella_worker_completed(self, uid, data):
        """
        Internal callback function that is called when worker finishes its job
        """

        index = data.get('index', 1)
        self._slide_in_index(index)

    def _on_item_clicked(self, item):
        """
        Internal callback function that is called when the user clicks an item in a tree
        :param item: QTreeWidgetItem
        """

        self._update_title()

    def _on_item_double_clicked(self, item):
        """
        Internal callback function that is called when the user double clicks on an item
        :param index: int
        :return:
        """

        if not item or item.isDisabled():
            return

        if item.is_disabled():
            return

        if item.is_file():
            self.add_item_to_queue_list(item)
        else:
            current_widget = self._stack.currentWidget()
            current_path = current_widget.get_path()
            if not current_path or current_path not in self._trees:
                return

            path_to_add = item.get_path()
            if path_to_add in self._trees:
                index_to_move = self._trees[path_to_add]['index']
                self._slide_in_index(index_to_move)
            else:
                self._add_tree(path_to_add)

    def _on_artella_worker_failed(self, uid, msg, trace):
        """
        Internal callback function that is called when the Artella worker fails
        :param uid: str
        :param msg: str
        :param trace: str
        """

        artellapipe.logger.error(msg)
        self.workerFailed.emit(msg, trace)

        parent_index = 1
        if self._last_add and self._last_add in self._trees:
            parent_tree = self._trees[self._last_add]['parent']
            if parent_tree and parent_tree in self._trees:
                parent_index = self._trees[parent_tree]['index']

            self._remove_tree(self._last_add)
            self._last_add = None

        self._slide_in_index(parent_index)

    def _on_back(self):
        """
        Internal callback function that is called when the user presses the Back button
        """

        current_tree = self._stack.currentWidget()
        current_path = current_tree.get_path()
        if not current_path:
            return

        parent_path = self._trees[current_path]['parent']
        if not parent_path:
            return

        parent_index = self._trees[parent_path]['index']
        self._slide_in_index(parent_index)

    def _on_next(self):
        """
        Internal callback function that is called when the user presses the forward button
        """

        current_tree = self._stack.currentWidget()
        current_path = current_tree.get_path()
        if not current_path:
            return

        current_index = self._trees[current_path]['index']
        next_index = current_index + 1

        widget_in_index = self._stack.widget(next_index)
        if widget_in_index:
            self._slide_in_index(next_index)

        self._update_title()

    def _on_stack_anim_finished(self, index):
        """
        Internal callback function that is called when stack slide animation finishes
        :param index: int, new stack widget index
        """

        if index == 0:
            self._breadcrumb.set(['Retrieving data from Artella ...'])
        else:
            valid_update = self._update_title()
            if not valid_update:
                self._breadcrumb.set([''])

    def _on_update_breadcrumb(self, msg):
        """
        Internal callback function that is called during Artella syncing operations to update breadcrumb with info
        :param msg: str
        """

        self._breadcrumb.set([msg])

    def _on_add_item_to_sync_queue(self, item):
        """
        Internal callback that is called when the user adds a new item to queue list through item contextual menu
        :param item: ArtellaSyncItem
        """

        self.add_item_to_queue_list(item)

    def _on_refresh(self, tree_to_refresh=None):
        """
        Internal callback function that refresh current tree data
        """

        if tree_to_refresh:
            current_tree = tree_to_refresh
        else:
            current_tree = self._stack.currentWidget()
        if not current_tree:
            return

        current_path = current_tree.get_path()
        if current_path not in self._trees:
            return

        self._show_loading_widget()

        current_index = self._trees[current_path]['index']
        self._artella_worker.queue_work(current_tree.update_data, {'index': current_index})

    def _on_add_all_items_to_sync_queue(self, source_tree=None):
        """
        Internal callback function that is called when the user selects Add All Items toolbar button
        :param source_tree: variant, ArtellaSyncTree or None
        """

        if source_tree:
            current_tree = source_tree
        else:
            current_tree = self._stack.currentWidget()

        all_items = current_tree.get_items()
        for item in all_items:
            self.add_item_to_queue_list(item)

    def _on_clear_sync_queue(self):
        """
        Internal callback function that is callded when the user selects Clear Sync Queue toolbar button
        :param tree_to_clear: variant, ArtellaSyncTree or None
        """

        self._queue_widget.clear()

    def _on_create_new_asset(self, item):
        """
        Internal callback function that is called when a new asset should be created
        :param item: ArtellaSyncItem
        """

        self.createAsset.emit(item)


class ArtellaSyncTree(treewidgets.TreeWidget, object):

    updateBreadcrumb = Signal(str)
    addToSyncQueue = Signal(object)
    forceRefresh = Signal(object)
    addAllItemsToSyncQueue = Signal(object)
    clearSyncQueue = Signal()
    createAsset = Signal(object)

    def __init__(self, project, path, parent=None):
        super(ArtellaSyncTree, self).__init__(parent)

        self._project = project
        self._path = path
        self._items = list()

        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setTabKeyNavigation(True)
        self.setHeaderHidden(True)
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self._on_context_menu)

    def drawBranches(self, painter, rect, index):
        """
        Overrides base treewidgets.FileTreeWidget drawBranches function
        Draw custom icons for tree items
        :param painter: QPainter
        :param rect: QRect
        :param index: QModelIndex
        """

        item = self.itemFromIndex(index)
        item.get_icon().paint(painter, rect)

    def get_path(self):
        """
        Returns path linked to this tree
        :return: str
        """

        return self._path

    def get_items(self, include_disabled_items=True):
        """
        Returns all items added to the tree
        :return: list(ArtellaSyncItem)
        """

        if include_disabled_items:
            return [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        else:
            return [self.topLevelItem(i) for i in range(self.topLevelItemCount()) if not self.topLevelItem(i).is_disabled()]

    def refresh(self):
        """
        Refreshes the items in the tree
        """

        self.clear()
        self.addTopLevelItems(self._items)

    def update_data(self, data=None):
        """
        Function that updates tree with current project info
        """

        self._items = list()

        if not self._path:
            return

        status = artellalib.get_status(self._path)
        if isinstance(status, artellaclasses.ArtellaDirectoryMetaData):
            total_refs = len(status.references.keys())
            current_ref = 1
            for ref_name, ref_data in status.references.items():
                self.updateBreadcrumb.emit('({}/{}) Retrieving info: {}'.format(current_ref, total_refs, ref_name))
                artella_data = artellalib.get_status(ref_data.path)
                if ref_data.is_directory:
                    item = self._create_item(ref_name, ref_data.path, artella_data)
                else:
                    item = self._create_item(ref_name, ref_data.path, artella_data, True)
                self._items.append(item)
                current_ref += 1
        elif isinstance(status, artellaclasses.ArtellaAssetMetaData):
            working_path = os.path.join(status.path, defines.ARTELLA_WORKING_FOLDER)
            artella_data = artellalib.get_status(working_path)
            if isinstance(artella_data, artellaclasses.ArtellaDirectoryMetaData):
                for ref_name, ref_data in artella_data.references.items():
                    artella_data = artellalib.get_status(ref_data.path)
                    item = self._create_item(ref_name, ref_data.path, artella_data)
                    self._items.append(item)

        self.refresh()

        return data

    def _create_item(self, ref_name, ref_path, artella_data, is_file=False):
        """
        Internal function that creates an return new ArtellaSyncItem
        :return: ArtellaSyncItem
        """

        path_ext = os.path.splitext(ref_path)[-1]
        if not path_ext:
            is_file = False

        if is_file:
            try:
                ref_name = ref_name.split('/')[-1]
                cache_folder = os.path.join(self._project.get_data_path(), 'server_sync_cache')
                if not os.path.exists(cache_folder):
                    os.makedirs(cache_folder)
                cache_path = os.path.join(cache_folder, os.path.basename(ref_path))
                if not os.path.isfile(cache_path):
                    open(cache_path, 'a').close()
                file_info = QFileInfo(cache_path)
                icon_provider = QFileIconProvider()
                file_icon = icon_provider.icon(file_info)
                new_item = ArtellaSyncItem(self._project, ref_name, ref_path, artella_data, is_file, file_icon)
            except Exception:
                new_item = ArtellaSyncItem(self._project, ref_name, ref_path, artella_data, False)
        else:
            split_name = ref_name.split('/')
            if len(split_name) > 1:
                ref_name = split_name[-1]
            new_item = ArtellaSyncItem(self._project, ref_name, ref_path, artella_data, is_file)

        return new_item

    def _create_tree_context_menu(self):
        """
        Internal function that creates the context menu of the tree
        :return:
        """

        context_menu = QMenu(self)

        refresh_icon = artellapipe.resource.icon('refresh')
        queue_icon = artellapipe.resource.icon('queue')
        delete_icon = artellapipe.resource.icon('delete')

        refresh_action = QAction(refresh_icon, 'Refresh', context_menu, statusTip='Refresh Tree Data')
        add_all_items_action = QAction(queue_icon, 'Add all Items to Sync Queue', context_menu, statusTip='Add all items into Sync queue')
        clear_queue_action = QAction(delete_icon, 'Clear Sync Queue', context_menu, statusTip='Clear All items from Sync Queue')

        refresh_action.triggered.connect(self._on_refresh)
        add_all_items_action.triggered.connect(self._on_add_all_items_to_sync_queue)
        clear_queue_action.triggered.connect(self.clearSyncQueue.emit)

        context_menu.addAction(refresh_action)
        context_menu.addAction(add_all_items_action)
        context_menu.addAction(clear_queue_action)

        return context_menu

    def _create_tree_item_context_menu(self, item):
        """
        Internal function that creates the context menu of the tree items
        :param item: ArtellaSyncItem
        """

        context_menu = QMenu(self)
        if not item:
            return context_menu

        artella_icon = artellapipe.resource.icon('artella')
        queue_icon = artellapipe.resource.icon('queue')
        teapot_icon = artellapipe.resource.icon('teapot')
        eye_icon = artellapipe.resource.icon('eye')

        open_in_artella_action = QAction(artella_icon, 'Open in Artella', context_menu, statusTip='Open Item in Artella')
        add_to_sync_queue_action = QAction(queue_icon, 'Add to Sync Queue', context_menu, statusTip='Add item to Artella Syncer queue')
        create_asset_action = QAction(teapot_icon, 'Create New Asset', context_menu, statusTip='Create New Asset')
        view_locally_action = QAction(eye_icon, 'View Locally', context_menu, statusTip='View File Locally')

        open_in_artella_action.triggered.connect(partial(self._on_open_item_in_artella, item))
        add_to_sync_queue_action.triggered.connect(partial(self._on_add_item_to_sync_queue, item))
        create_asset_action.triggered.connect(partial(self._on_create_new_asset, item))
        view_locally_action.triggered.connect(partial(self._on_view_locally, item))

        context_menu.addAction(open_in_artella_action)
        context_menu.addAction(add_to_sync_queue_action)
        context_menu.addAction(view_locally_action)

        if not item.is_asset():
            context_menu.addSeparator()
            context_menu.addAction(create_asset_action)

        return context_menu

    def _create_context_menu(self, item=None):
        """
        Internal function that creates the context menu to show
        :return: QMenu
        """

        if item:
            context_menu = self._create_tree_item_context_menu(item)
        else:
            context_menu = self._create_tree_context_menu()

        return context_menu

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            context_menu = self._create_context_menu()
        else:
            context_menu = self._create_context_menu(item)

        if not context_menu:
            return

        context_menu.exec_(self.mapToGlobal(pos))

    def _on_open_item_in_artella(self, item):
        """
        Internal callback function that opens item in Artella web
        :param item: ArtellaSyncItem
        """

        item.open_in_artella()

    def _on_create_new_asset(self, item):
        """
        Internal callback function that opens Create New Assset dialog
        :param item: ArtellaSyncItem
        """

        self.createAsset.emit(item)

    def _on_view_locally(self, item):
        """
        Internal callback function that opens file locally
        :param item: ArtellaSyncItem
        """

        item.view_locally()

    def _on_add_item_to_sync_queue(self, item):
        """
        Internal callback function that is called when an ArtellaSyncItem is added to render sync queue
        :param item: ArtellaSyncItem
        """

        self.addToSyncQueue.emit(item)

    def _on_refresh(self):
        """
        Internal callback function that is called when the user wants to refresh tree data
        """

        self.forceRefresh.emit(self)

    def _on_add_all_items_to_sync_queue(self):
        """
        Internal callback function that is called when the user wants to add all items to sync queue
        """

        self.addAllItemsToSyncQueue.emit(self)


class ArtellaSyncItem(QTreeWidgetItem, object):

    ICON_UNKNOWN = artellapipe.resource.icon('question')
    ICON_FOLDER = artellapipe.resource.icon('folder')
    ICON_ASSET = artellapipe.resource.icon('teapot')

    def __init__(self, project, name, path, artella_data, is_file=False, file_icon=None, parent=None):
        super(ArtellaSyncItem, self).__init__(parent)

        self._project = project
        self._name = name
        self._path = path
        self._artella_data = artella_data
        self._is_disabled = False if artella_data else True
        self._is_file = is_file
        self._file_icon = file_icon if file_icon else self.ICON_UNKNOWN

        self._parent = None
        self.set_parent(parent)

        self.setFlags(self.flags() | Qt.ItemIsSelectable)

        self.setText(0, name)

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

    def get_project(self):
        """
        Returns Artella project linked to this item
        :return: ArtellaProject
        """

        return self._project

    def get_name(self):
        """
        Returns name of the item
        :return: str
        """

        return self._name

    def get_path(self):
        """
        Returns path of the current item in Artella project
        :return: str
        """

        if not self._artella_data:
            return None

        if isinstance(self._artella_data, (artellaclasses.ArtellaDirectoryMetaData, artellaclasses.ArtellaAssetMetaData)):
            return self._artella_data.path
        elif isinstance(self._artella_data, artellaclasses.ArtellaHeaderMetaData):
            return self._path

        return None

    def get_relative_path(self):
        """
        Returns poath of the item relative to the Artella project
        :return: str
        """

        return os.path.relpath(self.get_path(), self._project.get_assets_path())

    def is_asset(self):
        """
        Returns whether current item is an asset or not
        :return: bool
        """

        if not self._artella_data:
            return False

        return isinstance(self._artella_data, artellaclasses.ArtellaAssetMetaData)

    def get_icon(self):
        """
        Returns item icon depending of the wrapped Artella object
        """

        if not self._artella_data:
            self._is_disabled = True
            return self.ICON_UNKNOWN

        if not self._is_file:
            if isinstance(self._artella_data, artellaclasses.ArtellaDirectoryMetaData):
                return self.ICON_FOLDER
            elif isinstance(self._artella_data, artellaclasses.ArtellaAssetMetaData):
                return self.ICON_ASSET
        else:
            return self._file_icon

        self._is_disabled = True
        return self.ICON_UNKNOWN

    def get_artella_url(self):
        """
        Returns Artella URL of the item
        :return: str
        """

        relative_path = self.get_relative_path()
        assets_url = self._project.get_artella_assets_url()
        artella_url = '{}{}'.format(assets_url, relative_path)

        return artella_url

    def is_file(self):
        """
        Returns whether current item is a file or not
        :return: bool
        """

        return self._is_file

    def is_disabled(self):
        """
        Returns whether the item is disabled or not
        :return: bool
        """

        return self._is_disabled

    def open_in_artella(self):
        """
        Opens current item in Artella web
        :return:
        """

        artella_url = self.get_artella_url()
        webbrowser.open(artella_url)

    def view_locally(self):
        """
        Opens item locally
        """

        artellalib.explore_file(self.get_path())


class ArtellaSyncQueueItemStatus(object):
    WAIT = 'wait'
    RUN = 'run'
    OK = 'ok'
    ERROR = 'error'


class ArtellaSyncQueueItem(QTreeWidgetItem, object):

    WAIT_ICON = artellapipe.resource.icon('clock')
    RUN_ICON = artellapipe.resource.icon('clock_start')
    OK_ICON = artellapipe.resource.icon('ok')
    ERROR_ICON = artellapipe.resource.icon('error')

    def __init__(self, project, name, path, icon, is_file, is_asset, parent=None):
        super(ArtellaSyncQueueItem, self).__init__(parent)

        self._project = project
        self._path = path
        self._icon = icon
        self._is_file = is_file
        self._is_asset = is_asset
        self._sync_status = ArtellaSyncQueueItemStatus.WAIT

        self.setText(0, name)
        self.setIcon(0, icon)

    def get_project(self):
        """
        Returns Artella project linked to this item
        :return: ArtellaProject
        """

        return self._project

    def get_name(self):
        """
        Returns the name of the item
        :return: str
        """

        return self.text(0)

    def get_path(self):
        """
        Returns the path of the item
        :return: str
        """

        return self._path

    def get_icon(self):
        """
        Returns the icon of the item
        :return: QIcon
        """

        return self.icon(0)

    def is_file(self):
        """
        Returns whether the item is a file or not
        :return: bool
        """

        return self._is_file

    def is_asset(self):
        """
        Returns whether current item is an asset or not
        :return: bool
        """

        return self._is_asset

    def get_relative_path(self):
        """
        Returns poath of the item relative to the Artella project
        :return: str
        """

        return os.path.relpath(self.get_path(), self._project.get_assets_path())

    def get_artella_url(self):
        """
        Returns Artella URL of the item
        :return: str
        """

        relative_path = self.get_relative_path()
        assets_url = self._project.get_artella_assets_url()
        artella_url = '{}{}'.format(assets_url, relative_path)

        return artella_url

    def open_in_artella(self):
        """
        Opens current item in Artella web
        :return:
        """

        artella_url = self.get_artella_url()
        webbrowser.open(artella_url)

    def set_sync_status(self, sync_status):
        """
        Sets the sync status of the item
        :param sync_status: ArtellaSyncItemStatus
        """

        self._sync_status = sync_status

        if self._sync_status == ArtellaSyncQueueItemStatus.WAIT:
            self.setIcon(0, self.WAIT_ICON)
        elif self._sync_status == ArtellaSyncQueueItemStatus.RUN:
            self.setIcon(0, self.RUN_ICON)
        elif self._sync_status == ArtellaSyncQueueItemStatus.OK:
            self.setIcon(0, self.OK_ICON)
        else:
            self.setIcon(0, self.ERROR_ICON)


class ArtellaSyncQueueTree(QTreeWidget, object):

    queueCleared = Signal()

    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaSyncQueueTree, self).__init__(parent)

        self.header().setVisible(False)
        self.setSortingEnabled(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def get_items(self):
        """
        Returns the items added to the list
        :return: list(ArtellaSyncQueuItem)
        """

        return [self.topLevelItem(i) for i in range(self.topLevelItemCount())]

    def item_in_queue(self, item):
        """
        Returns whether given item is already in queue or not by comparing paths
        :param item: ArtellaSyncItem
        :return: bool
        """

        for i in range(self.topLevelItemCount()):
            queue_item = self.topLevelItem(i)
            if queue_item.get_path() == item.get_path():
                return queue_item

        return None

    def add_item(self, item):
        """
        Adds a new item to the list
        :param item: ArtellaSyncItem
        :return: QTreeWidgetItem
        """

        queue_item = self.item_in_queue(item)

        if not queue_item:
            queue_item = ArtellaSyncQueueItem(item.get_project(), item.get_name(), item.get_path(), item.get_icon(), item.is_file(), item.is_asset(), self)
            self.addTopLevelItem(queue_item)

        return queue_item

    def add_items(self, items):
        """
        Adds given items into the list
        :param items: list(ArtellaSyncItem)
        :return: list(QTreeWidgetItem)
        """

        return [self.add_item(item) for item in items]

    def remove_item(self, item):
        """
        Removes given item from list
        :param item: ArtellaSyncQueueItem
        """

        for i in range(self.topLevelItemCount()):
            queue_item = self.topLevelItem(i)
            if queue_item.get_path() == item.get_path():
                self.takeTopLevelItem(i)
                break

        if self.topLevelItemCount() == 0:
            self.queueCleared.emit()

    def clear_all_items(self):
        """
        Clears all the items in the list
        """

        self.clear()
        self.queueCleared.emit()

    def _create_tree_item_context_menu(self, item):
        """
        Internal function that creates menu for tree items
        :return: QMenu
        """

        context_menu = QMenu(self)

        artella_icon = artellapipe.resource.icon('artella')
        delete_icon = artellapipe.resource.icon('delete')

        open_in_artella_action = QAction(artella_icon, 'Open in Artella', context_menu, statusTip='Open Item in Artella')
        delete_action = QAction(delete_icon, 'Remove from Sync Queue', context_menu, statusTip='Remove item from Sync Queue')

        open_in_artella_action.triggered.connect(partial(self._on_open_item_in_artella, item))
        delete_action.triggered.connect(partial(self._on_remove_item, item))

        context_menu.addAction(open_in_artella_action)
        context_menu.addAction(delete_action)

        return context_menu

    def _create_tree_context_menu(self):
        """
        Internal function that creates menu for tree items
        :return: QMenu
        """

        context_menu = QMenu(self)

        delete_icon = artellapipe.resource.icon('delete')

        remove_queue_action = QAction(delete_icon, 'Clear Sync Queue', context_menu, statusTip='Remove All Items from Sync Queue')

        remove_queue_action.triggered.connect(self._on_clear)

        context_menu.addAction(remove_queue_action)

        return context_menu

    def _on_context_menu(self, pos):
        """
        Internal callback function that is called when the user opens contextual menu
        :param pos: QPos
        """

        item = self.itemAt(pos)
        if item:
            context_menu = self._create_tree_item_context_menu(item)
        else:
            context_menu = self._create_tree_context_menu()

        if not context_menu:
            return

        context_menu.exec_(self.mapToGlobal(pos))

    def _on_item_double_clicked(self, item):
        """
        Internal callback function that is called when the user double clicks an item
        :param item: ArtellaSyncQueueItem
        """

        self.remove_item(item)

    def _on_open_item_in_artella(self, item):
        """
        Internal callback function that opens item in Artella web
        :param item: ArtellaSyncQueueItem
        """

        item.open_in_artella()

    def _on_remove_item(self, item):
        """
        Internal callback function that is called when the user wants to remove an item using context menu
        :param itme: ArtellaSyncQueueItem
        """

        self.remove_item(item)

    def _on_clear(self):
        """
        Internal callback function that is called when the user wants to clear sync queue
        """

        self.clear_all_items()


class ArtellaSyncQueueWidget(base.BaseWidget, object):

    syncOk = Signal(str)
    syncFailed = Signal(str)
    syncWarning = Signal(str)

    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaSyncQueueWidget, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaSyncQueueWidget, self).ui()

        self.setMinimumWidth(150)

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        no_items_widget = QFrame()
        no_items_widget.setFrameShape(QFrame.StyledPanel)
        no_items_widget.setFrameShadow(QFrame.Sunken)
        no_items_layout = QVBoxLayout()
        no_items_layout.setContentsMargins(0, 0, 0, 0)
        no_items_layout.setSpacing(0)
        no_items_widget.setLayout(no_items_layout)
        no_items_lbl = QLabel()
        no_items_pixmap = artellapipe.resource.pixmap('sync_no_items')
        no_items_lbl.setPixmap(no_items_pixmap)
        no_items_lbl.setAlignment(Qt.AlignCenter)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        no_items_layout.addWidget(no_items_lbl)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        queue_widget = QWidget()
        queue_layout = QVBoxLayout()
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(2)
        queue_widget.setLayout(queue_layout)
        self._queue_list = ArtellaSyncQueueTree(project=self._project)
        self._queue_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._progress = progressbar.ArtellaProgressBar(project=self._project)
        self._progress.setVisible(False)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        self._sync_subfolders_cbx = QCheckBox('Sync Subfolders?')
        self._sync_subfolders_cbx.setMaximumWidth(110)
        self._sync_btn = QPushButton('Sync')
        buttons_layout.addWidget(self._sync_subfolders_cbx)
        buttons_layout.addWidget(self._sync_btn)

        queue_layout.addWidget(self._queue_list)
        queue_layout.addWidget(self._progress)
        queue_layout.addLayout(buttons_layout)

        self._stack.addWidget(no_items_widget)
        self._stack.addWidget(queue_widget)

    def setup_signals(self):
        self._queue_list.queueCleared.connect(self._on_queue_cleared)
        self._sync_btn.clicked.connect(self._on_sync)

    def add_items(self, items):
        """
        Adds a new item to the sync queue
        :param item: list(ArtellaSyncItem)
        :return: list(QTreeWidgetItem)
        """

        items = python.force_list(items)

        added_items = self._queue_list.add_items(items)
        if added_items:
            self._show_queue_list()

        return added_items

    def clear(self):
        """
        Clears queue list items
        """

        self._queue_list.clear_all_items()

    def _show_queue_list(self):
        """
        Internal function that shows or hides queue list
        """

        if self._queue_list.topLevelItemCount() > 0:
            self._stack.slide_in_index(1)
        else:
            self._stack.slide_in_index(0)

    def _on_queue_cleared(self):
        """
        Internal callback function that is called when queue list is cleared
        """

        self._stack.slide_in_index(0)

    def _on_sync(self):
        """
        Internal callback function that is called when the user presses Sync button
        """

        items_to_sync = self._queue_list.get_items()
        if not items_to_sync:
            msg = 'Select files and folers to sync before syncing!'
            artellapipe.logger.warning(msg)
            self.syncWarning.emit(msg)
            return

        self._progress.set_minimum(0)
        self._progress.set_maximum(len(items_to_sync))
        self._progress.setVisible(True)
        for item in items_to_sync:
            item.set_sync_status(ArtellaSyncQueueItemStatus.WAIT)
        self._queue_list.repaint()

        for i, item in enumerate(items_to_sync):
            item_path = item.get_path()
            item_name = os.path.basename(item_path)
            item.set_sync_status(ArtellaSyncQueueItemStatus.RUN)
            self._progress.set_value(i + 1)
            self._progress.set_text('Syncing file: {}. Please wait ...'.format(item_name))
            self._queue_list.repaint()
            try:
                if item.is_file():
                    valid_sync = artellalib.synchronize_file(item_path)
                else:
                    if self._sync_subfolders_cbx.isChecked() or item.is_asset():
                        valid_sync = artellalib.synchronize_path_with_folders(item_path, True)
                        if not valid_sync:
                            item_path = os.path.join(item_path, defines.ARTELLA_WORKING_FOLDER)
                            valid_sync = artellalib.synchronize_path_with_folders(item_path, True)
                    else:
                        valid_sync = artellalib.synchronize_path(item_path)
                        if not valid_sync:
                            item_path = os.path.join(item_path, defines.ARTELLA_WORKING_FOLDER)
                            valid_sync = artellalib.synchronize_path(item_path)
                if valid_sync:
                    item.set_sync_status(ArtellaSyncQueueItemStatus.OK)
                    self._queue_list.repaint()
                    self.syncOk.emit('File {} synced successfully!'.format(item_name))
                else:
                    item.set_sync_status(ArtellaSyncQueueItemStatus.ERROR)
                    self._queue_list.repaint()
                    self.syncFailed.emit('Error while syncing file {} from Artella server!'.format(item_name))
            except Exception as e:
                item.set_sync_status(ArtellaSyncQueueItemStatus.ERROR)
                self._queue_list.repaint()
                if item.is_file():
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
