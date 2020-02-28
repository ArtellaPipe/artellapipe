#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for sequence files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.qt.core import base, menu, qtutils

import artellapipe
from artellapipe.core import defines


class SequenceCategoryButton(QPushButton, object):
    def __init__(self, text, sequence):
        super(SequenceCategoryButton, self).__init__(text)

        self._sequence = sequence

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _create_context_menu(self, context_menu):
        """
        Internal function that generates contextual menu for asset widget
        Reimplement for custom functionality
        :param context_menu: Menu
        """

        sync_icon = tpDcc.ResourcesMgr().icon('sync')
        artella_icon = tpDcc.ResourcesMgr().icon('artella')
        eye_icon = tpDcc.ResourcesMgr().icon('eye')

        artella_action = QAction(artella_icon, 'Open in Artella', context_menu)
        view_locally_action = QAction(eye_icon, 'View Locally', context_menu)
        sync_action = QAction(sync_icon, 'Synchronize', context_menu)

        sync_menu = menu.Menu(self)
        actions_added = self._fill_sync_action_menu(sync_menu)
        artella_action.triggered.connect(self._on_open_in_artella)
        view_locally_action.triggered.connect(self._on_view_locally)

        context_menu.addAction(artella_action)
        context_menu.addAction(view_locally_action)
        context_menu.addSeparator()
        if actions_added:
            sync_action.setMenu(sync_menu)
            context_menu.addAction(sync_action)

    def _fill_sync_action_menu(self, sync_menu):
        """
        Internal function that fills sync menu with proper actions depending of the asset files supported
        :param sync_menu: Menu
        """

        if not sync_menu:
            return

        actions_to_add = list()

        for sequence_type_name in self._sequence.FILES:
            asset_type_icon = resource.ResourceManager().icon(sequence_type_name)
            asset_type_action = QAction(asset_type_icon, sequence_type_name.title(), sync_menu)
            asset_type_action.triggered.connect(
                partial(self._on_sync, sequence_type_name, defines.ArtellaFileStatus.ALL))
            actions_to_add.append(asset_type_action)

        if actions_to_add:
            download_icon = resource.ResourceManager().icon('download')
            all_action = QAction(download_icon, 'All', sync_menu)
            all_action.triggered.connect(
                partial(self._on_sync, defines.ArtellaFileStatus.ALL, defines.ArtellaFileStatus.ALL))
            actions_to_add.insert(0, all_action)

            for action in actions_to_add:
                sync_menu.addAction(action)

        return actions_to_add

    def _on_context_menu(self, pos):
        """
        Internal callback function that is called when the user wants to show asset widget contextual menu
        :param pos: QPoint
        """

        context_menu = menu.Menu(self)
        self._create_context_menu(context_menu)
        context_menu.exec_(self.mapToGlobal(pos))

    def _on_open_in_artella(self):
        """
        Internal callback function that is called when the user presses Open in Artella contextual menu action
        """

        self._sequence.open_in_artella()

    def _on_view_locally(self):
        """
        Internal callback function that is called when the user presses View Locally contextual menu action
        """

        self._sequence.view_locally()

    def _on_sync(self, file_type, sync_type, ask=False):
        """
        Internal callback function that is called when the user presses Sync contextual menu action
        :param file_type: str
        :param sync_type: str
        :param ask: bool
        """

        if ask:
            res = qtutils.show_question(
                None,
                'Synchronize "{}" file: {}'.format(self.asset.get_name(), file_type.title()),
                'Are you sure you want to sync this asset? This can take some time!'
            )
            if res != QMessageBox.Yes:
                return

        self._sequence.sync(file_type, sync_type)


class ArtellaSequenceWidget(base.BaseWidget, object):

    clicked = Signal(object)

    def __init__(self, sequence, text=None, parent=None):
        self._sequence = sequence
        self._text = text or artellapipe.SequencesMgr().get_default_sequence_name()

        super(ArtellaSequenceWidget, self).__init__(parent=parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(ArtellaSequenceWidget, self).ui()

        self.setFixedWidth(160)
        self.setFixedHeight(160)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(2, 2, 2, 2)
        widget_layout.setSpacing(0)
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        self._sequence_btn = QPushButton('', self)
        self._sequence_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._sequence_btn.setIcon(artellapipe.project.thumb_icon)
        self._sequence_btn.setIconSize(QSize(150, 150))
        self._sequence_lbl = QLabel(self._text)
        self._sequence_lbl.setAlignment(Qt.AlignCenter)

        widget_layout.addWidget(self._sequence_btn)
        widget_layout.addWidget(self._sequence_lbl)

    def setup_signals(self):
        self._sequence_btn.clicked.connect(partial(self.clicked.emit, self))

    @property
    def sequence(self):
        """
        Returns shot data
        :return: ArtellaSequence
        """

        return self._sequence

    def _init(self):
        """
        Internal function that initializes sequence widget
        Can be extended to add custom initialization functionality to sequence widgets
        """

        if not self._sequence:
            return

        self._sequence_lbl.setText(self._sequence.get_name())


artellapipe.register.register_class('SequenceWidget', ArtellaSequenceWidget)
