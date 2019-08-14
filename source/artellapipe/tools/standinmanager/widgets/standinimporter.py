#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Standin Importer
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base

import artellapipe
from artellapipe.tools.standinmanager import standinmanager

if tp.is_maya():
    import tpMayaLib as maya


class StandinImporter(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(StandinImporter, self).__init__(parent=parent)

    def ui(self):
        super(StandinImporter, self).ui()

        buttons_layout = QGridLayout()
        self.main_layout.addLayout(buttons_layout)

        folder_icon = artellapipe.resource.icon('folder')
        standin_path_layout = QHBoxLayout()
        standin_path_layout.setContentsMargins(2, 2, 2, 2)
        standin_path_layout.setSpacing(2)
        standin_path_widget = QWidget()
        standin_path_widget.setLayout(standin_path_layout)
        standin_path_lbl = QLabel('Standin File: ')
        self.standin_path_line = QLineEdit()
        self.standin_path_line.setReadOnly(True)
        self.standin_path_btn = QPushButton()
        self.standin_path_btn.setIcon(folder_icon)
        self.standin_path_btn.setIconSize(QSize(18, 18))
        self.standin_path_btn.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0); border: 0px solid rgba(255,255,255,0);")
        standin_path_layout.addWidget(self.standin_path_line)
        standin_path_layout.addWidget(self.standin_path_btn)
        buttons_layout.addWidget(standin_path_lbl, 1, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(standin_path_widget, 1, 1)

        self.import_btn = QPushButton('Import')
        self.import_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.reference_btn = QPushButton('Reference')
        buttons_layout.addWidget(self.import_btn, 2, 0, 2, 2)
        self.import_btn.setEnabled(False)

        self.standin_path_btn.clicked.connect(self._on_browse_standin)
        self.standin_path_line.textChanged.connect(self.refresh)
        self.import_btn.clicked.connect(self._on_import)

    @staticmethod
    def import_standin(project, standin_path, standin_name=None, fix_path=False):
        if not standin_path or not os.path.isfile(standin_path):
            artellapipe.logger.warning('Standin file {} does not exits!'.format(standin_path))
            return None

        if standin_name is None:
            standin_name = os.path.basename(standin_path).split('.')[0]

        standin_node = maya.cmds.createNode('aiStandIn', name='{}_standin'.format(standin_name))
        xform = maya.cmds.listRelatives(standin_node, parent=True)[0]
        maya.cmds.rename(xform, standin_name)

        if fix_path:
            ass_path = project.fix_path(standin_path)
        else:
            ass_path = standin_path
        maya.cmds.setAttr('{}.dso'.format(standin_node), ass_path, type='string')

    def refresh(self):
        if self.standin_path_line.text() and os.path.isfile(self.standin_path_line.text()):
            self.import_btn.setEnabled(True)
        else:
            self.import_btn.setEnabled(False)

    def _on_browse_standin(self):
        standin_folder = self._project.get_path()

        res = maya.cmds.fileDialog2(fm=1, dir=standin_folder, cap='Select Standin to Import', ff='Standin Files (*.ass)')
        if res:
            standin_file = res[0]
        else:
            standin_file = ''

        self.standin_path_line.setText(standin_file)

        self.refresh()

    def _on_import(self):
        standin_file = self.standin_path_line.text()
        if not standin_file or not os.path.isfile(standin_file):
            maya.cmds.confirmDialog(t='Error', m='No Standin File is selected or file is not currently available on disk')
            return None

        standin_name = os.path.basename(standin_file).split('.')[0]

        self.import_standin(self._project, standin_file, standin_name)


standinmanager.register_importer(StandinImporter)
