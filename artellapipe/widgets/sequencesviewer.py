#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for sequences viewer
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.python import python

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import grid

import artellapipe

LOGGER = logging.getLogger()


class SequencesViewer(base.BaseWidget, object):

    sequenceAdded = Signal(object)

    def __init__(self, project, column_count=4, update=False, parent=None):

        self._project = project
        self._column_count = column_count

        super(SequencesViewer, self).__init__(parent=parent)

        if update:
            self._sequences_grid.update_sequences()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(SequencesViewer, self).ui()

        self._sequences_grid = SequencesGrid(
            project=self._project,
            column_count=self._column_count,
            parent=self
        )
        self._sequences_grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout.addWidget(self._sequences_grid)

    def setup_signals(self):
        self._sequences_grid.sequenceAdded.connect(self.sequenceAdded.emit)

    def update_sequences(self, force=False):
        self._sequences_grid.update_sequences(force=force)


class SequencesGrid(grid.GridWidget, object):

    sequenceAdded = Signal(object)

    def __init__(self, project, column_count=4, parent=None):
        super(SequencesGrid, self).__init__(parent=parent)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setColumnCount(column_count)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setSelectionMode(QAbstractItemView.NoSelection)

        self._sequences = list()
        self._cache = list()

        self._project = project

    def get_sequences(self, update_cache=True, force=False):
        """
        Returns a list with all the sequences of the project
       :param update_cache: bool, Updates the internal cache
        :param force: bool, If True, cache and shots will be updated
        :return: list
        """

        if update_cache:
            self.update_cache(force=force)

        if self._sequences and not force:
            return self._sequences

        self.update_sequences()

        return self._sequences

    def update_cache(self, force=False):
        """
        Updates internal cache with the current sequences located in Artella server
        """

        if self._cache and not force:
            return self._cache

        python.clear_list(self._sequences)
        return artellapipe.SequencesMgr().find_all_sequences(force_update=force)

    def update_sequences(self, force=False):
        """
        Updates the list of sequences in the sequences viewer
        :param force:
        :return:
        """

        if not self._project:
            LOGGER.warning('Project not defined!')
            return

        self.clear_sequences()

        all_sequences = self.update_cache(force=force)
        if not all_sequences:
            return

        for sequence in all_sequences:
            if not sequence:
                continue
            sequence_widget = artellapipe.SequenceWidget(sequence)
            self.add_sequence(sequence_widget)

    def clear_sequences(self):
        """
        Clear all the sequences of the sequences viewer
        """

        python.clear_list(self._sequences)
        self.clear()

    def add_sequence(self, sequence_widget):
        """
        Adds given sequence widget to viewer
        :param sequence_widget: ArtellaSequenceWidget
        """

        if not sequence_widget:
            return

        self._add_widget(sequence_widget)
        self._sequences.append(sequence_widget)
        self.sequenceAdded.emit(sequence_widget)

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


artellapipe.register.register_class('SequencesViewer', SequencesViewer)
