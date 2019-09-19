#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export shot files to be used in the shot builder tool
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import sys
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.core import qtutils
from tpQtLib.widgets import splitters, stack

from artellapipe.gui import window


class ShotExporter(window.ArtellaWindow, object):

    VERSION = '0.0.1'
    LOGO_NAME = 'shotexporter_logo'

    def __init__(self, project):
        super(ShotExporter, self).__init__(
            project=project,
            name='ShotExporter',
            title='Shot Exporter',
            size=(550, 650)
        )

        self._init()

    def ui(self):
        super(ShotExporter, self).ui()

        self._exporters_menu_layout = QHBoxLayout()
        self._exporters_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._exporters_menu_layout.setSpacing(5)
        self._exporters_menu_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self._exporters_menu_layout)

        self._exporters_btn_grp = QButtonGroup(self)
        self._exporters_btn_grp.setExclusive(True)

        self._main_stack = stack.SlidingStackedWidget()

        self.main_layout.addLayout(self._exporters_menu_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._main_stack)

    def setup_signals(self):
        self._main_stack.animFinished.connect(self._on_stack_anim_finished)

    def _init(self):
        """
        Internal function that initializes Short Exporter widgets
        :return:
        """
        self._update_registered_exporters()

    def _update_registered_exporters(self):
        """
        Internal function that updates current categories with the given ones
        """

        for btn in self._exporters_btn_grp.buttons():
            self._exporters_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._exporters_menu_layout)

        self._exporters_menu_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        i = 0
        registered_exporters = self.get_registered_exporters()
        for exporter_name, exporter in reversed(registered_exporters.items()):
            if exporter.EXPORTER_FILE in self._project.shot_file_types:
                new_btn = QPushButton(exporter_name)
                new_btn.setIcon(exporter.EXPORTER_ICON)
                new_btn.setMinimumWidth(80)
                new_btn.setCheckable(True)
                self._exporters_menu_layout.addWidget(new_btn)
                self._exporters_btn_grp.addButton(new_btn)
                exporter_widget = exporter(project=self._project)
                new_btn.clicked.connect(partial(self._on_change_exporter, exporter_widget))
                self._main_stack.addWidget(exporter_widget)
                if i == 0:
                    new_btn.setChecked(True)
                i += 1

        self._exporters_menu_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

    def get_registered_exporters(self):
        """
        Returns a list with all registered exporters
        :return: list(cls)
        """

        if 'exporters' not in sys.modules[__name__].__dict__:
            return dict()

        return sys.modules[__name__].__dict__['exporters']

    def _on_change_exporter(self, exporter):
        """
        Internal callback function that is called when an exporter needs to be showed
        :param exporter:
        """

        if exporter == self._main_stack.currentWidget():
            return

        for btn in self._exporters_btn_grp.buttons():
            btn.setEnabled(False)

        index = self._main_stack.indexOf(exporter)
        if not index:
            self._main_stack.slide_in_index(0)
        else:
            self._main_stack.slide_in_index(index)

    def _on_stack_anim_finished(self):
        """
        Internal callback function that is called when stack anim finishes
        """

        for btn in self._exporters_btn_grp.buttons():
            btn.setEnabled(True)


def register_exporter(cls):
    """
    This function registers given exporter class
    :param cls: class, Alembic importer class we want to register
    """

    if 'exporters' not in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__['exporters'] = dict()

    sys.modules[__name__].__dict__['exporters'][cls.EXPORTER_NAME] = cls


def run(project):
    win = ShotExporter(project=project)
    win.show()

    return win
