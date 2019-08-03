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

        self._stack = stack.SlidingStackedWidget()
        self._waiter = ArtellaSyncWaiter()
        self._breadcrumb = breadcrumb.BreadcrumbFrame()

        back_icon = artellapipe.resource.icon('back')
        self._back_btn = QPushButton()
        self._back_btn.setIcon(back_icon)

        next_icon = artellapipe.resource.icon('forward')
        self._next_btn = QPushButton()
        self._next_btn.setIcon(next_icon)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(2)
        top_layout.addWidget(self._back_btn)
        top_layout.addWidget(self._breadcrumb)
        top_layout.addWidget(self._next_btn)

        self.main_layout.addLayout(top_layout)
        self.main_layout.addWidget(self._stack)

        self._stack.addWidget(self._waiter)

        self._reset_title()

        self._init()

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._back_btn.clicked.connect(self._on_back)
        self._next_btn.clicked.connect(self._on_next)

    def _on_stack_anim_finished(self, index):
        if index == 0:
            self._breadcrumb.set(['Retrieving data from Artella ...'])
        else:
            valid_update = self._update_title()
            if not valid_update:
                self._breadcrumb.set([''])

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
            sync_tree = ArtellaSyncTree(path=path)
            sync_tree.itemClicked.connect(self._on_item_clicked)
            sync_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
            self._stack.addWidget(sync_tree)
            index = self._stack.indexOf(sync_tree)
            self._trees[path] = {'tree': sync_tree, 'index': index, 'parent': parent_path}
            self._artella_worker.queue_work(sync_tree.update_data, {'index': index})
            self._last_add = path

            self._trees[path]['parent'] = current_tree.get_path()

        return sync_tree, index

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

        if not item:
            return

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

    def _on_artella_worker_failed(self, uid, msg):
        """
        Internal callback function that is called when the Artella worker fails
        :param uid: str
        :param msg: str
        """

        artellapipe.logger.error(msg)

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


class ArtellaSyncTree(treewidgets.TreeWidget, object):

    def __init__(self, path, parent=None):
        super(ArtellaSyncTree, self).__init__(parent)

        self._path = path
        self._items = list()

        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setTabKeyNavigation(True)
        self.setHeaderHidden(True)
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self._context_menu = self._create_context_menu()

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
            for ref_name, ref_data in status.references.items():
                artella_data = artellalib.get_status(ref_data.path)
                item = ArtellaSyncItem(ref_name, artella_data)
                self._items.append(item)
        elif isinstance(status, artellaclasses.ArtellaAssetMetaData):
            working_path = os.path.join(status.path, defines.ARTELLA_WORKING_FOLDER)
            artella_data = artellalib.get_status(working_path)
            if isinstance(artella_data, artellaclasses.ArtellaDirectoryMetaData):
                for ref_name, ref_data in artella_data.references.items():
                    artella_data = artellalib.get_status(ref_data.path)
                    item = ArtellaSyncItem(ref_name, artella_data)
                    self._items.append(item)

        self.refresh()

        return data

    def _create_context_menu(self):
        """
        Internal function that creates the context menu of the tree
        :return: QMenu
        """

        context_menu = QMenu(self)

        context_menu.addAction('Hello Tree!')

        return context_menu

    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            context_menu = self._context_menu
        else:
            context_menu = item.get_context_menu()

        if not context_menu:
            return

        context_menu.exec_(self.mapToGlobal(pos))


class ArtellaSyncItem(QTreeWidgetItem, object):

    ICON_UNKNOWN = artellapipe.resource.icon('question')
    ICON_FOLDER = artellapipe.resource.icon('folder')

    def __init__(self, name, artella_data, parent=None):
        super(ArtellaSyncItem, self).__init__(parent)

        self._name = name
        self._artella_data = artella_data

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
            return self.ICON_UNKNOWN

        if isinstance(self._artella_data, artellaclasses.ArtellaDirectoryMetaData):
            return self.ICON_FOLDER

        return self.ICON_UNKNOWN

    def get_context_menu(self):
        """
        Returns context menu linked to this item
        :return: QMenu
        """

        context_menu = QMenu()

        context_menu.addAction('Hello World!')

        return context_menu
