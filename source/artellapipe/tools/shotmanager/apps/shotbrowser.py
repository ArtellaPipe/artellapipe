#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to manage shots in Artella project
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpQtLib.widgets import stack, label

import artellapipe
from artellapipe.core import sequence
from artellapipe.gui import window, waiter


class ArtellaShotBrowser(window.ArtellaWindow, object):

    VERSION = '0.0.1'
    LOGO_NAME = 'shotbrowser_logo'

    refreshed = Signal()

    def __init__(self, project):

        self._selected_sequence = None
        self._selected_shot = None
        self._force_update = False
        self._is_blocked = False

        super(ArtellaShotBrowser, self).__init__(
            project=project,
            name='ShotManager',
            title='Shot Manager',
            size=(900, 850)
        )

        self._setup_toolbar()

    def ui(self):
        super(ArtellaShotBrowser, self).ui()

        self._main_stack = stack.SlidingStackedWidget(parnet=self)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._main_stack.addWidget(splitter)

        self.main_layout.addWidget(self._main_stack)

        sequences_widget = QWidget()
        self._sequences_layout = QVBoxLayout()
        self._sequences_layout.setContentsMargins(0, 0, 0, 0)
        self._sequences_layout.setSpacing(0)
        sequences_widget.setLayout(self._sequences_layout)
        self._sequences_stack = stack.SlidingStackedWidget(self)
        self._sequences_waiter = waiter.ArtellaWaiter()
        no_sequences_widget = QFrame()
        no_sequences_widget.setFrameShape(QFrame.StyledPanel)
        no_sequences_widget.setFrameShadow(QFrame.Sunken)
        no_items_layout = QVBoxLayout()
        no_items_layout.setContentsMargins(0, 0, 0, 0)
        no_items_layout.setSpacing(0)
        no_sequences_widget.setLayout(no_items_layout)
        no_items_lbl = QLabel()
        no_items_pixmap = artellapipe.resource.pixmap('refresh_sequences')
        no_items_lbl.setPixmap(no_items_pixmap)
        no_items_lbl.setAlignment(Qt.AlignCenter)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        no_items_layout.addWidget(no_items_lbl)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        self._sequences_list = QListWidget()
        accent_color = self.theme().accent_color()
        self._sequences_list.setStyleSheet("QListWidget::item:selected { border: 1px solid rgb(" + str(accent_color.red() * 255.0) + " +, " + str(accent_color.green() * 255.0) + ", " + str(accent_color.blue() * 255.0) + "); }")
        self._sequences_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._sequences_list.setMinimumWidth(100)
        self._sequences_stack.addWidget(no_sequences_widget)
        self._sequences_stack.addWidget(self._sequences_waiter)
        self._sequences_stack.addWidget(self._sequences_list)
        self._sequences_layout.addWidget(self._sequences_stack)

        shots_widget = QWidget()
        self._shots_layout = QVBoxLayout()
        self._shots_layout.setContentsMargins(0, 0, 0, 0)
        self._shots_layout.setSpacing(0)
        shots_widget.setLayout(self._shots_layout)
        self._shots_stack = stack.SlidingStackedWidget(self)
        self._shots_waiter = waiter.ArtellaWaiter()
        self._shots_list = QListWidget()
        shots_bg = QFrame()
        shots_bg_layout = QVBoxLayout()
        shots_bg_layout.setContentsMargins(0, 0, 0, 0)
        shots_bg_layout.setSpacing(0)
        shots_bg.setLayout(shots_bg_layout)
        shots_bg.setStyleSheet("#background {border-radius: 3px;border-style: solid;border-width: 1px;border-color: rgb(32,32,32);}")
        shots_bg.setFrameShape(QFrame.StyledPanel)
        shots_bg.setFrameShadow(QFrame.Raised)
        lbl_layout = QHBoxLayout()
        lbl_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))
        shot_thumb_lbl = label.ThumbnailLabel()
        shot_thumb_lbl.setMinimumSize(QSize(80, 55))
        shot_thumb_lbl.setMaximumSize(QSize(80, 55))
        shot_thumb_lbl.setStyleSheet('')
        shot_thumb_lbl.setPixmap(self._project.resource.pixmap(self._project.get_clean_name()))
        shot_thumb_lbl.setScaledContents(False)
        shot_thumb_lbl.setAlignment(Qt.AlignCenter)
        lbl_layout.addWidget(shot_thumb_lbl)
        lbl_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))
        shots_bg_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding))
        shots_bg_layout.addLayout(lbl_layout)
        shots_bg_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding))
        self._shots_stack.addWidget(shots_bg)
        self._shots_stack.addWidget(self._shots_waiter)
        self._shots_stack.addWidget(self._shots_list)
        self._shots_layout.addWidget(self._shots_stack)

        splitter.addWidget(sequences_widget)
        splitter.addWidget(shots_widget)

    def setup_signals(self):
        self._sequences_list.currentItemChanged.connect(self._on_sequence_item_changed)
        self._sequences_stack.animFinished.connect(self._on_sequences_stack_anim_finished)
        self._shots_stack.animFinished.connect(self._on_shots_stack_anim_finished)

    def refresh(self, force_update=False):
        """
        Refresh the data of loaded sequences and shots
        """

        self._shots_list.clear()
        self._sequences_list.clear()

        force_update = force_update or self._force_update

        sequences = self._get_sequences(force_update=force_update)
        self._force_update = False
        if not sequences:
            self.refreshed.emit()
            return

        for seq in sequences:
            seq_widget = sequence.ArtellaSequenceWidget(sequence=seq)
            seq_item = QListWidgetItem()
            seq_item.setSizeHint(seq_widget.sizeHint())
            seq_item.setFlags(seq_item.flags() | Qt.ItemIsTristate)
            self._sequences_list.addItem(seq_item)
            self._sequences_list.setItemWidget(seq_item, seq_widget)

    def _setup_toolbar(self):
        """
        Internal functoin that creates toolbar for ShotBrowser tool
        :return: QToolBar
        """
        refresh_icon = artellapipe.resource.icon('refresh')
        toolbar = self.add_toolbar('shotBrowserToolbar')
        refresh_button = QToolButton()
        refresh_button.setText('Refresh')
        refresh_button.setIcon(refresh_icon)
        refresh_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addWidget(refresh_button)
        toolbar.addSeparator()

        refresh_button.clicked.connect(self._on_refresh)

        return toolbar

    def _get_sequences(self, force_update=False):
        """
        Returns list of sequences in current project
        :return: list
        """

        if not self._project:
            artellapipe.logger.warning('Impossible to retrieve sequences because project is not setup!')
            return

        return self._project.get_sequences(force_update=force_update)

    def _get_shots_from_sequence(self, sequence=None):
        """
        Returns shots of the current selected sequence
        :return:
        """

        if not sequence:
            sequence = self._selected_sequence

        if not self._project:
            artellapipe.logger.warning('Impossible to retrieve shots because project is not setup!')
            return

        if not sequence:
            artellapipe.logger.warning('Impossible to retrieve shots because no sequence given!')
            return

        shots = sequence.get_shots()

        print('Shots: {}'.format(shots))

    def _on_refresh(self):
        """
        Internal callback function that is called when Refresh button is clicked
        """

        self._force_update = True
        self._sequences_stack.slide_in_index(1)

    def _on_sequences_stack_anim_finished(self, index):
        """
        Internal callback function that is called when shots stack anim finishes
        :param index: int
        """

        if index == 1:
            self._is_blocked = True
            self.refresh()
            if self._sequences_list.count() > 0:
                self._sequences_stack.slide_in_index(2)
            else:
                self._sequences_stack.slide_in_index(0)

    def _on_shots_stack_anim_finished(self, index):
        """
        Internal callback function that is called when shots stack anim finishes
        :param index: int
        """

        if index == 1 and self._selected_sequence:
            self._is_blocked = True
            self._get_shots_from_sequence()
            if self._shots_list.count() > 0:
                self._shots_stack.slide_in_index(2)
            else:
                self._shots_stack.slide_in_index(0)

    def _on_sequence_item_changed(self, selected_item):
        """
        Internal callback function that is called each time a sequence is selected
        """

        if selected_item:
            widget = self._sequences_list.itemWidget(selected_item)
            if widget:
                self._selected_sequence = widget
                self._shots_stack.slide_in_index(1)
                return

        self._shots_stack.slide_in_index(0)

def run(project):
    win = ArtellaShotBrowser(project=project)
    win.show()

    return win
