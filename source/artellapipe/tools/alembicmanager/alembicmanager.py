#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export/import Alembic (.abc) files
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

from artellapipe.tools.alembicmanager.widgets import alembicgroup


class AlembicManager(window.ArtellaWindow, object):

    LOGO_NAME = 'alembicmanager_logo'

    def __init__(self, project):
        super(AlembicManager, self).__init__(
            project=project,
            name='ArtellaAlembicManager',
            title='Alembic Manager',
            size=(550, 650)
        )

    def ui(self):
        super(AlembicManager, self).ui()

        alembic_icon = artellapipe.resource.icon('alembic_white')
        export_icon = artellapipe.resource.icon('export')
        import_icon = artellapipe.resource.icon('import')

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())

        self._abc_btn = QPushButton('ABC Group')
        self._abc_btn.setIcon(alembic_icon)
        self._abc_btn.setMinimumWidth(80)
        self._abc_btn.setCheckable(True)
        self._exporter_btn = QPushButton('Exporter')
        self._exporter_btn.setIcon(export_icon)
        self._exporter_btn.setMinimumWidth(80)
        self._exporter_btn.setCheckable(True)
        self._importer_btn = QPushButton('Importer')
        self._importer_btn.setIcon(import_icon)
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
        self._alembic_exporter = getattr(sys.modules[__name__], 'exporter')(project=self._project)
        self._alembic_importer = getattr(sys.modules[__name__], 'importer')(project=self._project)

        self._stack.addWidget(self._alembic_group_widget)
        self._stack.addWidget(self._alembic_exporter)
        self._stack.addWidget(self._alembic_importer)

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._abc_btn.clicked.connect(partial(self._on_slide_stack, 0))
        self._exporter_btn.clicked.connect(partial(self._on_slide_stack, 1))
        self._importer_btn.clicked.connect(partial(self._on_slide_stack, 2))
        self._alembic_exporter.showWarning.connect(self._on_show_warning)
        self._alembic_exporter.showOk.connect(self._on_show_ok)
        self._alembic_importer.showOk.connect(self._on_show_ok)

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

        if self._stack.currentWidget() == self._alembic_exporter:
            self._alembic_exporter.refresh()

    def _on_show_ok(self, warning_msg):
        """
        Internal callback function that is called when an ok message should be showed
        :param warning_msg: str
        """

        artellapipe.logger.debug(warning_msg)
        self.show_ok_message(warning_msg)

    def _on_show_warning(self, warning_msg):
        """
        Internal callback function that is called when a warning message should be showed
        :param warning_msg: str
        """

        artellapipe.logger.warning(warning_msg)
        self.show_warning_message(warning_msg)


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
    win = AlembicManager(project=project)
    win.show()

    return win
