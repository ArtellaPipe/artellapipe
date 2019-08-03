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
import shutil
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import base
from tpQtLib.widgets import stack, breadcrumb, treewidgets

import artellapipe
from artellapipe.core import defines, artellalib, artellaclasses
from artellapipe.gui import waiter
from artellapipe.utils import worker


class ArtellaSyncWaiter(waiter.ArtellaWaiter, object):
    def __init__(self, parent=None):
        super(ArtellaSyncWaiter, self).__init__(parent=parent)

    def get_path(self):
        return None


class ArtellaSyncWidget(base.BaseWidget, object):

    workerFailed = Signal(str, str)

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

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._back_btn.clicked.connect(self._on_back)
        self._next_btn.clicked.connect(self._on_next)

    def add_item_to_queue_list(self, item):
        """
        Adds given item to queue list
        :param item: ArtellaSyncItem
        """

        return self._queue_widget.add_item(item)

    def _init(self):
        """
        Internal function that initializes tree
        """

        assets_path = self._project.get_assets_path()
        self._add_tree(assets_path)

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

    def _add_tree(self, path):
        """
        Internal callback function that adds a new tree into the stack
        :param path: str
        """

        current_tree = self._stack.currentWidget()
        parent_path = current_tree.get_path()

        self._stack.slide_in_index(0)

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
        self._stack.slide_in_index(index)

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
                self._stack.slide_in_index(index_to_move)
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

        self._stack.slide_in_index(parent_index)

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
        self._stack.slide_in_index(parent_index)

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
            self._stack.slide_in_index(next_index)

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


class ArtellaSyncTree(treewidgets.TreeWidget, object):

    updateBreadcrumb = Signal(str)
    addToSyncQueue = Signal(object)

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

    def refresh(self):
        """
        Refreshes the items in the tree
        """

        self.clear()

        self.addTopLevelItems(self._items)

    def update_data(self, data):
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
                new_item = ArtellaSyncItem(ref_name, artella_data, is_file, file_icon)
            except Exception:
                new_item = ArtellaSyncItem(ref_name, artella_data, False)
        else:
            split_name = ref_name.split('/')
            if len(split_name) > 1:
                ref_name = split_name[-1]
            new_item = ArtellaSyncItem(ref_name, artella_data, is_file)

        return new_item

    def _create_context_menu(self, item=None):
        """
        Internal function that creates the context menu of the tree
        :return: QMenu
        """

        context_menu = QMenu(self)
        if not item:
            return context_menu

        artella_icon = artellapipe.resource.icon('artella')
        queue_icon = artellapipe.resource.icon('queue')

        open_in_artella_action = QAction(artella_icon, 'Open in Artella', context_menu, statusTip='Open Item in Artella')
        add_to_sync_queue_action = QAction(queue_icon, 'Add to Sync Queue', context_menu, statusTip='Add item to Artella Syncer queue')

        open_in_artella_action.triggered.connect(partial(self._on_open_item_in_artella, item))
        add_to_sync_queue_action.triggered.connect(partial(self._on_add_item_to_sync_queue, item))

        context_menu.addAction(add_to_sync_queue_action)

        return context_menu

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return
            # context_menu = self._context_menu
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

    def _on_add_item_to_sync_queue(self, item):
        """
        Internal callback function that is called when an ArtellaSyncItem is added to render sync queue
        :param item: ArtellaSyncItem
        """

        self.addToSyncQueue.emit(item)


class ArtellaSyncItem(QTreeWidgetItem, object):

    ICON_UNKNOWN = artellapipe.resource.icon('question')
    ICON_FOLDER = artellapipe.resource.icon('folder')
    ICON_ASSET = artellapipe.resource.icon('teapot')

    def __init__(self, name, artella_data, is_file=False, file_icon=None, parent=None):
        super(ArtellaSyncItem, self).__init__(parent)

        self._name = name
        self._artella_data = artella_data
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

        return None

    def get_icon(self):
        """
        Returns item icon depending of the wrapped Artella object
        """

        if not self._artella_data:
            self.setDisabled(True)
            return self.ICON_UNKNOWN

        if not self._is_file:
            if isinstance(self._artella_data, artellaclasses.ArtellaDirectoryMetaData):
                return self.ICON_FOLDER
            elif isinstance(self._artella_data, artellaclasses.ArtellaAssetMetaData):
                return self.ICON_ASSET
        else:
            return self._file_icon

        self.setDisabled(True)
        return self.ICON_UNKNOWN

    def is_file(self):
        """
        Returns whether current item is a file or not
        :return: bool
        """

        return self._is_file

    def open_in_artella(self):
        """
        Opens current item in Artella web
        :return:
        """

        pass


class ArtellaSyncQueueTree(QTreeWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaSyncQueueTree, self).__init__(parent)

        self.header().setVisible(False)
        self.setSortingEnabled(False)

    def add_item(self, item):
        """
        Adds a new item to the list
        :param item: ArtellaSyncItem
        :return: bool
        """

        new_item = QTreeWidgetItem(self)
        new_item.setText(0, item.get_name())
        new_item.setIcon(0, item.get_icon())

        self.addTopLevelItem(new_item)

        return True


class ArtellaSyncQueueWidget(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(ArtellaSyncQueueWidget, self).__init__()

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
        self._sync_btn = QPushButton('Sync')
        queue_layout.addWidget(self._queue_list)
        queue_layout.addWidget(self._sync_btn)

        self._stack.addWidget(no_items_widget)
        self._stack.addWidget(queue_widget)

    def add_item(self, item):
        """
        Adds a new item to the sync queue
        :param item: ArtellaSyncItem
        :return: bool
        """

        valid_add = self._queue_list.add_item(item)
        self._show_queue_list()

        return valid_add

    def _show_queue_list(self):
        """
        Internal function that shows or hides queue list
        """

        if self._queue_list.topLevelItemCount() > 0:
            self._stack.slide_in_index(1)
        else:
            self._stack.slide_in_index(0)
