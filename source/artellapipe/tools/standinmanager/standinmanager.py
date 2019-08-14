#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export/import Standin (.ass) files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import sys
from functools import partial

from Qt.QtWidgets import *

from tpQtLib.widgets import stack, splitters

import artellapipe
from artellapipe.gui import window


class StandinManager(window.ArtellaWindow, object):

    LOGO_NAME = 'standinmanager_logo'

    def __init__(self, project):
        super(StandinManager, self).__init__(
            project=project,
            name='SolsticeStandinManager',
            title='Standin Manager',
            size=(400, 600)
        )

    def ui(self):
        super(StandinManager, self).ui()

        export_icon = artellapipe.resource.icon('export')
        import_icon = artellapipe.resource.icon('import')

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())

        self._exporter_btn = QPushButton('Exporter')
        self._exporter_btn.setIcon(export_icon)
        self._exporter_btn.setMinimumWidth(80)
        self._exporter_btn.setCheckable(True)
        self._importer_btn = QPushButton('Importer')
        self._importer_btn.setIcon(import_icon)
        self._importer_btn.setMinimumWidth(80)
        self._importer_btn.setCheckable(True)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        buttons_layout.addWidget(self._exporter_btn)
        buttons_layout.addWidget(self._importer_btn)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self._buttons_grp = QButtonGroup(self)
        self._buttons_grp.setExclusive(True)
        self._buttons_grp.addButton(self._exporter_btn)
        self._buttons_grp.addButton(self._exporter_btn)
        self._buttons_grp.addButton(self._importer_btn)
        self._exporter_btn.setChecked(True)

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        self._standin_exporter = getattr(sys.modules[__name__], 'exporter')(project=self._project)
        self._standin_importer = getattr(sys.modules[__name__], 'importer')(project=self._project)

        self._stack.addWidget(self._standin_exporter)
        self._stack.addWidget(self._standin_importer)

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._exporter_btn.clicked.connect(partial(self._on_slide_stack, 0))
        self._importer_btn.clicked.connect(partial(self._on_slide_stack, 1))

    def _on_slide_stack(self, index):
        """
        Internal callback function that is called when stack needs to change current widget
        :param index: int
        """

        if index == self._stack.currentIndex():
            return

        for btn in self._buttons_grp.buttons():
            btn.setEnabled(False)

        self._stack.slide_in_index(index)

    def _on_stack_anim_finished(self):
        """
        Internal callback function that is called when stack anim finish
        """

        for btn in self._buttons_grp.buttons():
            btn.setEnabled(True)


def register_importer(cls):
    """
    This function registers given class
    :param cls: class, Alembic importer class we want to register
    """

    sys.modules[__name__].__dict__['importer'] = cls


def register_exporter(cls):
    """
    This function registers given class
    :param cls: class, Alembic importer class we want to register
    """

    sys.modules[__name__].__dict__['exporter'] = cls


def run(project):
    win = StandinManager(project=project)
    win.show()

    return win
