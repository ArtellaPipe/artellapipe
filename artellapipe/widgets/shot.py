#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with Artella shots
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import traceback
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs.qt.core import base, menu

import artellapipe.register
from artellapipe.utils import worker
from artellapipe.widgets import shotinfo, sequenceinfo

LOGGER = logging.getLogger('artellapipe')


class ArtellaShotWidget(base.BaseWidget, object):

    ThreadPool = QThreadPool()

    clicked = Signal(object)
    startSync = Signal(object, str, str)

    def __init__(self, shot, text=None, parent=None):
        self._shot = shot
        self._text = text or artellapipe.ShotsMgr().get_default_shot_name()
        self._thumbnail_icon = None

        super(ArtellaShotWidget, self).__init__(parent=parent)

        self._worker = worker.ThumbDownloaderWorker()
        self._worker.setAutoDelete(False)
        self._worker.signals.triggered.connect(self._on_thumbnail_from_image)
        self._worker_started = False

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(ArtellaShotWidget, self).ui()

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

        self._shot_btn = QPushButton('', self)
        self._shot_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._shot_btn.setIconSize(QSize(150, 150))
        self._shot_lbl = QLabel(self._text)
        self._shot_lbl.setAlignment(Qt.AlignCenter)

        widget_layout.addWidget(self._shot_btn)
        widget_layout.addWidget(self._shot_lbl)

    def setup_signals(self):
        self._shot_btn.clicked.connect(partial(self.clicked.emit, self))
        self.customContextMenuRequested.connect(self._on_context_menu)

    @property
    def shot(self):
        """
        Returns shot data
        :return: ArtellaShot
        """

        return self._shot

    def get_shot_info(self):
        """
        Returns widget associated to this shot
        :return: ShotInfoWidget
        """

        return ShotSequenceInfo(self)

    def get_thumbnail_path(self):
        """
        Returns path where sequence thumbnail is located
        :return: str
        """

        data_path = self._shot.project.get_data_path()
        thumbnails_cache_folder = os.path.join(data_path, 'shot_thumbs_cache')
        if not os.path.isdir(thumbnails_cache_folder):
            os.makedirs(thumbnails_cache_folder)

        return os.path.join(thumbnails_cache_folder, self._shot.get_name() + '.png')

    def get_thumbnail_icon(self):
        """
        Returns the icon of the asset
        :return: QIcon
        """

        return self._thumbnail_icon

    def update_thumbnail_icon(self, force=False):
        """
        Function that updates the thumbnail icon
        :return:
        """

        try:
            thumbnail_path = self.get_thumbnail_path()
            if thumbnail_path and os.path.isfile(thumbnail_path) and not force:
                thumb_icon = QIcon(thumbnail_path)
                self._shot_btn.setIcon(thumb_icon)
                self._thumbnail_icon = thumb_icon
                return thumb_icon
            else:
                self._thumbnail_icon = tpDcc.ResourcesMgr().icon(
                    artellapipe.ShotsMgr().get_default_shot_thumb())
                self._shot_btn.setIcon(self._thumbnail_icon)
                shot_thumbnail_path = self._shot.get_thumbnail_path()
                if not shot_thumbnail_path:
                    return self._thumbnail_icon
                self._worker_started = True
                self._worker.set_path(thumbnail_path)
                self._worker.set_force(force)
                self._worker.set_preview_id(shot_thumbnail_path)
                self.ThreadPool.start(self._worker)
                return self._thumbnail_icon
        except Exception as exc:
            LOGGER.error('Impossible to update thumbnail icon: {} | {}'.format(exc, traceback.format_exc()))

    def _init(self):
        """
        Internal function that initializes sequence widget
        Can be extended to add custom initialization functionality to sequence widgets
        """

        if not self._shot:
            return

        self._shot_lbl.setText(self._shot.get_name())

        self.update_thumbnail_icon()

    def _create_context_menu(self, context_menu):
        """
        Internal function that generates contextual menu for asset widget
        Reimplement for custom functionality
        :param context_menu: Menu
        """

        sync_icon = tpDcc.ResourcesMgr().icon('sync')
        artella_icon = tpDcc.ResourcesMgr().icon('artella')
        eye_icon = tpDcc.ResourcesMgr().icon('eye')
        thumb_icon = tpDcc.ResourcesMgr().icon('picture')

        artella_action = QAction(artella_icon, 'Open in Artella', context_menu)
        view_locally_action = QAction(eye_icon, 'View Locally', context_menu)
        sync_action = QAction(sync_icon, 'Synchronize', context_menu)
        thumb_action = QAction(thumb_icon, 'Update Thumbnail', context_menu)

        sync_menu = menu.Menu(self)
        # actions_added = self._fill_sync_action_menu(sync_menu)
        artella_action.triggered.connect(self._on_open_in_artella)
        view_locally_action.triggered.connect(self._on_view_locally)
        thumb_action.triggered.connect(partial(self.update_thumbnail_icon, True))

        context_menu.addAction(artella_action)
        context_menu.addAction(view_locally_action)
        context_menu.addSeparator()
        context_menu.addAction(thumb_action)

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

        self._shot.open_in_artella()

    def _on_view_locally(self):
        """
        Internal callback function that is called when the user presses View Locally contextual menu action
        """

        self._shot.view_locally()

    def _on_thumbnail_from_image(self, shot_icon):
        """
        Internal callback function that is called when an image object has finished loading
        """

        if shot_icon and not shot_icon.isNull():
            self._thumbnail_icon = shot_icon
            self._shot_btn.setIcon(shot_icon)


class ShotSequenceInfo(base.BaseWidget, object):
    def __init__(self, shot_widget, parent=None):
        self._shot_widget = shot_widget
        super(ShotSequenceInfo, self).__init__(parent=parent)

    def ui(self):
        super(ShotSequenceInfo, self).ui()

        tab = QTabWidget()
        self.main_layout.addWidget(tab)

        sequence_name = self._shot_widget.shot.get_sequence()
        sequence = artellapipe.SequencesMgr().find_sequence(sequence_name)

        self._sequence_info = sequenceinfo.SequenceInfoWidget(sequence)
        self._shot_info = shotinfo.ShotInfoWidget(self._shot_widget)

        tab.addTab(self._shot_info, 'Shot')
        tab.addTab(self._sequence_info, 'Sequence')
