#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains publisher creator implementation for Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

from artellapipe.gui import window


class ArtellaPublisherCreator(window.ArtellaWindow, object):

    LOGO_NAME = 'publisher_logo'

    def __init__(self, project):

        self._pyblish_window = None
        self._registered_plugin_paths = list()
        self._registered_tag_types = list()

        super(ArtellaPublisherCreator, self).__init__(
            project=project,
            name='ArtellaPublisherCreatorWindow',
            title='Publisher Creator',
            size=(220, 250)
        )

        self.refresh()

    def ui(self):
        super(ArtellaPublisherCreator, self).ui()

        body = QWidget()
        lists = QWidget()
        footer = QWidget()

        container = QWidget()

        self._listing = QListWidget()
        self._name = QLineEdit()

        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Tag Types"))
        layout.addWidget(self._listing)
        layout.addWidget(QLabel("Name"))
        layout.addWidget(self._name)
        layout.setContentsMargins(0, 0, 0, 0)

        options = QWidget()

        autoclose_chk = QCheckBox("Close after creation")
        autoclose_chk.setCheckState(Qt.Checked)

        layout = QGridLayout(options)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(autoclose_chk, 1, 0)

        layout = QHBoxLayout(lists)
        layout.addWidget(container)
        layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(body)
        layout.addWidget(lists)
        layout.addWidget(options, 0, Qt.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)

        self._create_btn = QPushButton("Create")
        error_msg = QLabel()
        error_msg.hide()

        layout = QVBoxLayout(footer)
        layout.addWidget(self._create_btn)
        layout.addWidget(error_msg)
        layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addWidget(body)
        self.main_layout.addWidget(footer)

        names = {
            self._create_btn: "Create Button",
            self._listing: "Listing",
            # useselection_chk: "Use Selection Checkbox",
            autoclose_chk: "Autoclose Checkbox",
            self._name: "Name",
            error_msg: "Error Message",
        }

        for widget, name_ in names.items():
            widget.setObjectName(name_)

        self._name.setFocus()
        self._create_btn.setEnabled(False)

    # def setup_signals(self):
    #     self._create_btn.clicked.connect(self.on_create)
    #     self._name.returnPressed.connect(self.on_create)
    #     self._name.textChanged.connect(self.on_data_changed)
    #     self._listing.currentItemChanged.connect(self.on_data_changed)

    def refresh(self):
        has_tag_types = False

        tag_types = self._project.tag_types
        for tag_type in tag_types:
            item = QListWidgetItem(tag_type)
            item.setData(Qt.ItemIsEnabled, True)
            self._listing.addItem(item)
            has_tag_types = True

        if not has_tag_types:
            item = QListWidgetItem('No registered tag types')
            item.setData(Qt.ItemIsEnabled, False)
            self._listing.addItem(item)

        self._listing.setCurrentItem(self._listing.item(0))


def run(project):
    win = ArtellaPublisherCreator(project=project)
    win.show()

    return win
