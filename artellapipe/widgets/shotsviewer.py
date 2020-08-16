#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for shots viewer
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs.python import python
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import grid

import artellapipe
from artellapipe.widgets import shot as shot

LOGGER = logging.getLogger()


class ShotsViewer(base.BaseWidget, object):

    shotAdded = Signal(object)
    shotSynced = Signal()

    def __init__(self, project, column_count=4, show_context_menu=False, parent=None):

        self._project = project
        self._column_count = column_count
        self._show_context_menu = show_context_menu

        super(ShotsViewer, self).__init__(parent=parent)

        self._shots_grid.update_shots()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(ShotsViewer, self).ui()

        self._shots_grid = ShotsGrid(
            project=self._project,
            column_count=self._column_count,
            show_context_menu=self._show_context_menu,
            parent=self
        )
        self._shots_grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._sequences_menu_layout = QVBoxLayout()
        self._sequences_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._sequences_menu_layout.setSpacing(0)
        self._sequences_menu_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self._sequences_menu_layout)

        self._sequences_btn_grp = QButtonGroup(self)
        self._sequences_btn_grp.setExclusive(True)

        self.main_layout.addWidget(self._shots_grid)

        self.update_sequences_categories()

    def setup_signals(self):
        self._shots_grid.shotAdded.connect(self.shotAdded.emit)
        self._shots_grid.shotSynced.connect(self.shotSynced.emit)

    def first_empty_cell(self):
        """
        Creates ane empty cell in the shots grid
        """

        self._shots_grid.first_empty_cell()

    def update_shots(self, force=False):
        """
        Updates Shots viewer
        :param force: bool
        """

        self._shots_grid.update_shots(force=force)
        self.update_sequences_categories()

    def update_sequences_categories(self):
        """
        Updates current sequences categories
        """

        from artellapipe.widgets import sequence as sequence_widgets

        for btn in self._sequences_btn_grp.buttons():
            self._sequences_btn_grp.removeButton(btn)

        qtutils.clear_layout(self._sequences_menu_layout)

        all_sequences_categories = ['All']
        all_sequences = artellapipe.SequencesMgr().find_all_sequences()
        if all_sequences:
            sequence_names = [sequence.get_name() for sequence in all_sequences]
            all_sequences_categories.extend(sequence_names)

        for sequence_name in all_sequences_categories:
            sequence = artellapipe.SequencesMgr().find_sequence(sequence_name)
            new_btn = sequence_widgets.SequenceCategoryButton(sequence_name, sequence)
            new_btn.setMinimumWidth(QFontMetrics(new_btn.font()).width(sequence_name) + 10)
            new_btn.setCheckable(True)
            self._sequences_menu_layout.addWidget(new_btn)
            self._sequences_btn_grp.addButton(new_btn)
            if sequence_name == 'All':
                new_btn.setIcon(tpDcc.ResourcesMgr().icon('home'))
                new_btn.setChecked(True)
            new_btn.toggled.connect(partial(self._on_change_sequence, sequence_name))

    def _on_change_sequence(self, sequence_name, flag):
        """
        Internal callback function that is called when the user presses on Sequence category butotn
        :param sequence_name: str
        :param flag: bool
        """

        if flag:
            self._shots_grid.change_sequence(sequence_name)


class ShotsGrid(grid.GridWidget, object):

    shotAdded = Signal(object)
    shotSynced = Signal()

    def __init__(self, project, column_count=4, show_context_menu=False, parent=None):
        super(ShotsGrid, self).__init__(parent=parent)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setColumnCount(column_count)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setSelectionMode(QAbstractItemView.NoSelection)

        self._shots = list()
        self._cache = list()

        self._project = project
        self._show_context_menu = show_context_menu

        self._menu = self._create_contextual_menu()

    def contextMenuEvent(self, event):
        if not self._menu or not self._show_context_menu:
            return
        self._menu.exec_(event.globalPos())

    def get_shots(self, update_cache=True, force=False):
        """
        Returns a list with all the shots of the project
        :param update_cache: bool, Updates the internal cache
        :param force: bool, If True, cache and shots will be updated
        :return: list
        """

        if update_cache:
            self.update_cache(force=force)

        if self._shots and not force:
            return self._shots

        self.update_shots()

        return self._shots

    def update_cache(self, force=False):
        """
        Updates internal cache with the current shots located in Artella server
        """

        if self._cache and not force:
            return self._cache

        python.clear_list(self._cache)
        return artellapipe.ShotsMgr().find_all_shots(force_update=force)

    def update_shots(self, force=False):
        """
        Updates the list of shots in the shots viewer
        :param force: bool
        """

        if not self._project:
            LOGGER.warning('Project not defined!')
            return

        self.clear_shots()

        all_shots = self.update_cache(force=force)
        if not all_shots:
            return

        for found_shot in all_shots:
            if not found_shot:
                continue
            shot_widget = shot.ArtellaShotWidget(found_shot)
            self.add_shot(shot_widget)

    def clear_shots(self):
        """
        Clear all the shots of the shots viewer
        """

        python.clear_list(self._shots)
        self.clear()

    def change_sequence(self, sequence_name=None):
        """
        Changes the sequence of the shots that are being showed by the viewer
        :param sequence_name: str
        """

        if not sequence_name:
            sequence_name = 'All'

        all_sequences_names = artellapipe.SequencesMgr().get_sequence_names()
        if sequence_name != 'All' and sequence_name not in all_sequences_names:
            LOGGER.warning(
                'Sequence {} not found for current project {}'.format(sequence_name, self._project.name.title()))
            sequence_name = 'All'

        self.clear()

        new_shots = list()
        for new_shot in reversed(self._shots):
            if sequence_name == 'All':
                new_shot.setVisible(True)
                new_shots.insert(0, new_shot)
            else:
                if new_shot.shot.get_sequence() == sequence_name:
                    new_shot.setVisible(True)
                    new_shots.insert(0, new_shot)
                else:
                    new_shot.setVisible(False)
                    new_shots.append(new_shot)

        for new_shot in new_shots:
            self._add_widget(new_shot)

    def add_shot(self, shot_widget):
        """
        Adds given shot widget to viewer
        :param shot_widget:  ArtellaShotWidget
        """

        if not shot_widget:
            return

        self._add_widget(shot_widget)
        self._shots.append(shot_widget)
        self.shotAdded.emit(shot_widget)

    def _add_widget(self, widget):
        """
        Internal function that adds a new widget to the viewer
        :param widget: QWidget
        :return:
        """

        if widget is None:
            return

        row, col = self.first_empty_cell()
        self.addWidget(row, col, widget)
        self.resizeRowsToContents()

    def _create_contextual_menu(self):
        """
        Returns custom contextual menu
        :return: QMenu
        """

        new_menu = QMenu(self)

        return new_menu
