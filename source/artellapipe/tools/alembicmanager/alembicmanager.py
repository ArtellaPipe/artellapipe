#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export/import Alembic (.abc) files in Solstice
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtWidgets import *

from tpQtLib.widgets import stack, splitters

import artellapipe
from artellapipe.gui import window

from artellapipe.tools.alembicmanager.widgets import alembicgroup, alembicexporter, alembicimporter


class AlembicManager(window.ArtellaWindow, object):

    LOGO_NAME = 'alembicmanager_logo'

    def __init__(self, project):
        super(AlembicManager, self).__init__(
            project=project,
            name='SolsticeAlembicManager',
            title='Alembic Manager',
            size=(550, 650)
        )

    def ui(self):
        super(AlembicManager, self).ui()

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())

        self._abc_btn = QPushButton('ABC Group')
        self._abc_btn.setMinimumWidth(80)
        self._abc_btn.setCheckable(True)
        self._exporter_btn = QPushButton('Exporter')
        self._exporter_btn.setMinimumWidth(80)
        self._exporter_btn.setCheckable(True)
        self._importer_btn = QPushButton('Importer')
        self._importer_btn.setMinimumWidth(80)
        self._importer_btn.setCheckable(True)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        buttons_layout.addWidget(self._abc_btn)
        buttons_layout.addWidget(self._exporter_btn)
        buttons_layout.addWidget(self._importer_btn)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self._buttons_grp = QButtonGroup(self)
        self._buttons_grp.setExclusive(True)
        self._buttons_grp.addButton(self._abc_btn)
        self._buttons_grp.addButton(self._exporter_btn)
        self._buttons_grp.addButton(self._exporter_btn)
        self._buttons_grp.addButton(self._importer_btn)
        self._abc_btn.setChecked(True)

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        self._alembic_group_widget = alembicgroup.AlembicGroup()
        self._alembic_exporter = alembicexporter.AlembicExporter(project=self._project)
        self._alembic_importer = alembicimporter.AlembicImporter(project=self._project)

        self._stack.addWidget(self._alembic_group_widget)
        self._stack.addWidget(self._alembic_exporter)
        self._stack.addWidget(self._alembic_importer)

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._abc_btn.clicked.connect(partial(self._on_slide_stack, 0))
        self._exporter_btn.clicked.connect(partial(self._on_slide_stack, 1))
        self._importer_btn.clicked.connect(partial(self._on_slide_stack, 2))

    def _on_slide_stack(self, index):
        """
        Internal callback function that is called when stack needs to change current widget
        :param index: int
        """

        for btn in self._buttons_grp.buttons():
            btn.setEnabled(False)

        self._stack.slide_in_index(index)

    def _on_stack_anim_finished(self):
        """
        Internal callback function that is called when stack anim finish
        """

        for btn in self._buttons_grp.buttons():
            btn.setEnabled(True)


def run():
    win = AlembicManager(artellapipe.solstice)
    win.show()

    return win
