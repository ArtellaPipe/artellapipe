#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to upload new working versions of files to Artella in a batch mode
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import traceback

from Qt.QtWidgets import *
from Qt.QtCore import *

import tpDccLib as tp

from tpQtLib.core import qtutils
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.core import artellalib
from artellapipe.gui import window


class ArtellaUploader(window.ArtellaWindow, object):

    LOGO_NAME = 'artella_uploader'

    def __init__(self, project):
        super(ArtellaUploader, self).__init__(
            project=project,
            name='ArtellaUploaderWindow',
            title='Artella Uploader',
            size=(450, 650)
        )

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ArtellaUploader, self).ui()

        self._path_widget = QWidget()
        path_layout = QVBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(0)
        path_base_layout = QHBoxLayout()
        path_base_layout.setContentsMargins(0, 0, 0, 0)
        path_base_layout.setSpacing(0)
        path_layout.addLayout(path_base_layout)
        self._path_widget.setLayout(path_layout)
        path_lbl = QLabel('Path: ')
        path_lbl.setFixedWidth(30)
        self._folder_path = QLineEdit()
        tip = 'Select folder where files to batch are located'
        self._folder_path.setToolTip(tip)
        self._folder_path.setStatusTip(tip)
        self._folder_path.setContextMenuPolicy(Qt.CustomContextMenu)
        browse_icon = artellapipe.resource.icon('open')
        self._browse_btn = QPushButton()
        self._browse_btn.setFlat(True)
        self._browse_btn.setIcon(browse_icon)
        self._browse_btn.setFixedWidth(30)
        self._browse_btn.setToolTip('Browse Root Folder')
        self._browse_btn.setStatusTip('Browse Root Folder')
        sync_icon = artellapipe.resource.icon('sync')
        self._sync_btn = QPushButton()
        self._sync_btn.setFlat(True)
        self._sync_btn.setIcon(sync_icon)
        path_base_layout.addWidget(path_lbl)
        path_base_layout.addWidget(self._folder_path)
        path_base_layout.addWidget(self._browse_btn)
        path_base_layout.addWidget(splitters.get_horizontal_separator_widget())
        path_base_layout.addWidget(self._sync_btn)

        self._all_cbx = QCheckBox()
        self._all_cbx.setChecked(True)
        cbx_lyt = QHBoxLayout()
        cbx_lyt.setContentsMargins(0, 0, 0, 0)
        cbx_lyt.setSpacing(0)
        cbx_lyt.addWidget(self._all_cbx)
        cbx_lyt.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self._total_items_lbl = QLabel('')
        cbx_lyt.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        cbx_lyt.addWidget(self._total_items_lbl)

        self._files_list = QTreeWidget()
        self._files_list.setColumnCount(4)
        self._files_list.setAlternatingRowColors(True)
        self._files_list.setHeaderLabels(['', 'Path', 'Current Version', 'New Version'])
        for i in range(4):
            self._files_list.resizeColumnToContents(i)

        self._progress = self._project.get_progress_bar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress_lbl = QLabel('')
        self._progress_lbl.setAlignment(Qt.AlignCenter)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        lock_icon = artellapipe.resource.icon('lock')
        unlock_icon = artellapipe.resource.icon('unlock')
        upload_icon = artellapipe.resource.icon('upload')
        self._lock_btn = QPushButton('Lock')
        self._lock_btn.setIcon(lock_icon)
        self._unlock_btn = QPushButton('Unlock')
        self._unlock_btn.setIcon(unlock_icon)
        self._upload_btn = QPushButton('Upload')
        self._upload_btn.setIcon(upload_icon)
        buttons_layout.addWidget(self._lock_btn)
        buttons_layout.addWidget(self._unlock_btn)
        buttons_layout.addWidget(self._upload_btn)

        self.main_layout.addWidget(self._path_widget)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addLayout(cbx_lyt)
        self.main_layout.addWidget(self._files_list)
        self.main_layout.addWidget(self._progress)
        self.main_layout.addWidget(self._progress_lbl)
        self.main_layout.addLayout(buttons_layout)

        self._files_list.model().dataChanged.connect(self._on_data_changed)
        self._browse_btn.clicked.connect(self._on_browse)
        self._sync_btn.clicked.connect(self._on_sync)
        self._all_cbx.toggled.connect(self._on_toggle_all)
        self._lock_btn.clicked.connect(self._on_lock)
        self._upload_btn.clicked.connect(self._on_upload)
        self._unlock_btn.clicked.connect(self._on_unlock)

    def _on_data_changed(self):
        checked_items = self._checked_items()
        total_checked_items = len(list(checked_items))
        self._total_items_lbl.setText('Total Checked Items: {}'.format(total_checked_items))

    def _refresh_files(self):
        root_path = self._folder_path.text()
        if not root_path:
            return

        self._files_list.clear()

        for root, dirs, files in os.walk(root_path):
            for f in files:
                file_path = '{}{}{}'.format(root, os.sep, f)
                list_item = QTreeWidgetItem(self._files_list, [None, os.path.relpath(file_path, root_path), self._files_list])
                list_item.path = file_path
                list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                list_item.setTextAlignment(2, Qt.AlignCenter)
                list_item.setTextAlignment(3, Qt.AlignCenter)
                if self._all_cbx.isChecked():
                    list_item.setCheckState(0, Qt.Checked)
                else:
                    list_item.setCheckState(0, Qt.Unchecked)

        for i in range(4):
            self._files_list.resizeColumnToContents(i)

    def _on_browse(self):
        stored_path = self.settings().get('upload_path')
        if stored_path and os.path.isdir(stored_path):
            start_directory = stored_path
        else:
            start_directory = self._project.get_path()

        export_path = tp.Dcc.select_folder_dialog(
            title='Select Root Path',
            start_directory=start_directory
        )
        if not export_path:
            return

        self.settings().set('upload_path', str(export_path))

        self._folder_path.setText(export_path)

        self._refresh_files()
        self._refresh_versions()

    def _on_sync(self):
        current_path = self._folder_path.text()
        if not current_path or not os.path.isdir(current_path):
            artellapipe.logger.warning('Selected a folder to sync first!')
            return

        result = qtutils.show_question(None, 'Synchronizing folder: {}'.format(current_path), 'Are you sure you want to synchronize this folder? This can take quite a lot of time!')
        if result == QMessageBox.No:
            return

        try:
            self._progress.setVisible(True)
            self._progress_lbl.setText('Synchronizing files ... Please wait!')
            self.repaint()
            artellalib.synchronize_path_with_folders(current_path, recursive=True)
        except Exception as e:
            artellapipe.logger.error(str(e))
            artellapipe.logger.error(traceback.format_exc())
        finally:
            self._progress.setVisible(False)
            self._progress_lbl.setText('')
            self._refresh_files()
            self._refresh_versions()

    def _on_toggle_all(self, flag):
        it = QTreeWidgetItemIterator(self._files_list)
        while it.value():
            item = it.value()
            if flag:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)
            it += 1

    def _checked_items(self):
        """
        Internal function that returns all checked items in the list
        :return: generator
        """

        it = QTreeWidgetItemIterator(self._files_list)
        while it.value():
            item = it.value()
            if item.checkState(0) == Qt.Checked:
                yield item
            it += 1

    def _all_items(self):
        """
        Internal function that updates the versions of all items
        :return: generator
        """

        it = QTreeWidgetItemIterator(self._files_list)
        while it.value():
            item = it.value()
            yield item
            it += 1

    def _refresh_versions(self):
        """
        Internal funciton that updates working version of selected items
        :return:
        """

        try:
            all_items = list(self._all_items())
            self._progress.setVisible(True)
            self._progress.setMinimum(0)
            self._progress.setMaximum(len(all_items)-1)
            self._progress_lbl.setText('Checking file versions ... Please wait!')
            for i, item in enumerate(all_items):
                self._progress.setValue(i)
                self._progress_lbl.setText('Checking version for: {}'.format(item.text(1)))
                current_version = artellalib.get_file_current_working_version(item.path)
                if current_version == 0:
                    item.setText(2, '0 (Local Only)')
                else:
                    item.setText(2, str(current_version))
                item.setText(3, str(current_version + 1))
        except Exception as e:
            artellapipe.logger.error(str(e))
            artellapipe.logger.error(traceback.format_exc())
        finally:
            self._progress.setValue(0)
            self._progress_lbl.setText('')
            self._progress.setVisible(False)

    def _on_lock(self):
        items_to_lock = list()
        checked_items = self._checked_items()
        for item in checked_items:
            if not os.path.isfile(item.path):
                continue
            items_to_lock.append(item)

        if not items_to_lock:
            return

        self._progress.setVisible(True)
        self._progress.setMinimum(0)
        self._progress.setMaximum(len(items_to_lock)-1)
        self._progress_lbl.setText('Locking files ...')
        for i, item in enumerate(items_to_lock):
            self._progress.setValue(i)
            self._progress_lbl.setText('Locking: {}'.format(item.text(1)))
            self._project.lock_file(item.path, notify=False)
        self._progress.setValue(0)
        self._progress_lbl.setText('')
        self._progress.setVisible(False)
        self._project.tray.show_message(title='Lock Files', msg='Files locked successfully!')

    def _on_unlock(self):
        items_to_unlock = list()
        checked_items = self._checked_items()
        for item in checked_items:
            if not os.path.isfile(item.path):
                continue
            items_to_unlock.append(item)

        if not items_to_unlock:
            return

        msg = 'If changes in files are not submitted to Artella yet, submit them before unlocking the file please. \n\n Do you want to continue?'
        res = tp.Dcc.confirm_dialog(title='Unlock File', message=msg, button=['Yes', 'No'], cancel_button='No', dismiss_string='No')
        if tp.is_houdini():
            if res != QMessageBox.StandardButton.Yes:
                return
        else:
            if res != 'Yes':
                return False

        self._progress.setVisible(True)
        self._progress.setMinimum(0)
        self._progress.setMaximum(len(items_to_unlock) - 1)
        self._progress_lbl.setText('Unlocking files ...')
        for i, item in enumerate(items_to_unlock):
            self._progress.setValue(i)
            self._progress_lbl.setText('Unlocking: {}'.format(item.text(1)))
            self._project.unlock_file(item.path, notify=False, warn_user=False)
        self._progress.setValue(0)
        self._progress_lbl.setText('')
        self._progress.setVisible(False)
        self._project.tray.show_message(title='Unlock Files', msg='Files unlocked successfully!')

    def _on_upload(self):
        items_to_upload = list()
        checked_items = self._checked_items()
        for item in checked_items:
            if not os.path.isfile(item.path):
                continue
            items_to_upload.append(item)

        if not items_to_upload:
            return

        try:
            comment, res = QInputDialog.getMultiLineText(tp.Dcc.get_main_window(), 'Make New Versions', 'Comment')
        except Exception:
            comment, res = QInputDialog.getText(tp.Dcc.get_main_window(), 'Make New Versions', 'Comment')

        if res and comment:
            self._progress.setVisible(True)
            self._progress.setMinimum(0)
            self._progress.setMaximum(len(items_to_upload)-1)
            self._progress_lbl.setText('Uploading new working versions to Artella server ...')
            for i, item in enumerate(items_to_upload):
                self._progress.setValue(i)
                self._progress_lbl.setText('New version for: {} ({})'.format(item.text(1), item.text(3)))
                self._project.upload_working_version(item.path, skip_saving=True, notify=False, comment=comment)
            self._progress.setValue(0)
            self._progress_lbl.setText('')
            self._progress.setVisible(False)
            self._project.tray.show_message(title='New Working Versions', msg='New versions uploaded to Artella server successfully!')


def run(project):
    win = ArtellaUploader(project=project)
    win.show()

    return win
