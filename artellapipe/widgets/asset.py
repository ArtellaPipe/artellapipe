#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with Artella assets
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
from tpDcc.libs.qt.core import base, qtutils, menu

import artellapipe
from artellapipe.utils import worker
from artellapipe.core import defines
from artellapipe.widgets import assetinfo

LOGGER = logging.getLogger('artellapipe')


class ArtellaAssetButton(QPushButton, object):
    def __init__(self, *args, **kwargs):
        super(ArtellaAssetButton, self).__init__(*args, **kwargs)

        # self.setMouseTracking(True)

        # self._tooltip = tooltips.ToolTipWidget(self)
        # self._tooltip_timer = QTimer(self)
        # self._tooltip_timer.setSingleShot(True)
        # self._tooltip_timer.setInterval(800)
        # self._tooltip_timer.timeout.connect(self._on_show_tooltip)
        # self._tooltip_pos = QPoint()

    # def enterEvent(self, event):
    #     self._tooltip_timer.start()
    #     super(ArtellaAssetButton, self).enterEvent(event)
    #
    # def mouseMoveEvent(self, event):
    #     self._tooltip_pos = event.pos()
    #     self._tooltip_timer.start()
    #     super(ArtellaAssetButton, self).mouseMoveEvent(event)
    #
    # def leaveEvent(self, event):
    #     self._tooltip_timer.stop()
    #     super(ArtellaAssetButton, self).leaveEvent(event)
    #
    # def _on_show_tooltip(self):
    #     self._tooltip.show_at(self.mapToGlobal(self._tooltip_pos), QLabel('HELLO WORLD'))


class ArtellaAssetWidget(base.BaseWidget, object):

    ThreadPool = QThreadPool()

    clicked = Signal(object)
    startSync = Signal(object, str, str)

    def __init__(self, asset, text=None, parent=None):

        self._asset = asset
        self._text = text or artellapipe.AssetsMgr().get_default_asset_name()
        self._thumbnail_icon = None

        super(ArtellaAssetWidget, self).__init__(parent=parent)

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
        super(ArtellaAssetWidget, self).ui()

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

        self._asset_btn = ArtellaAssetButton('', self)
        self._asset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._asset_btn.setIconSize(QSize(150, 150))
        self._asset_lbl = QLabel(self._text)
        self._asset_lbl.setAlignment(Qt.AlignCenter)

        widget_layout.addWidget(self._asset_btn)
        widget_layout.addWidget(self._asset_lbl)

    def setup_signals(self):
        self._asset_btn.clicked.connect(partial(self.clicked.emit, self))
        self.customContextMenuRequested.connect(self._on_context_menu)

    @property
    def asset(self):
        """
        Returns asset data
        :return: ArtellaAsset
        """

        return self._asset

    def get_asset_info(self):
        """
        Retruns AssetInfo widget associated to this asset
        :return: AssetInfoWidget
        """

        return assetinfo.AssetInfoWidget(self)

    def get_thumbnail_path(self):
        """
        Returns path where asset thumbnail is located
        :return: str
        """

        asset_name = self._asset.get_name()

        return artellapipe.AssetsMgr().get_asset_thumbnail_path(asset_name=asset_name, create_folder=True)

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
                thumb_icon = QIcon(QPixmap(thumbnail_path))
                self._asset_btn.setIcon(thumb_icon)
                self._thumbnail_icon = thumb_icon
                return thumb_icon
            else:
                self._thumbnail_icon = tpDcc.ResourcesMgr().icon(
                    artellapipe.AssetsMgr().get_default_asset_thumb())
                self._asset_btn.setIcon(self._thumbnail_icon)
                asset_thumbnail_path = self._asset.get_thumbnail_path()
                if not asset_thumbnail_path:
                    return self._thumbnail_icon
                self._worker_started = True
                self._worker.set_path(thumbnail_path)
                self._worker.set_force(force)
                self._worker.set_preview_id(asset_thumbnail_path)
                self.ThreadPool.start(self._worker)
                return self._thumbnail_icon
        except Exception as exc:
            LOGGER.error('Impossible to update thumbnail icon: {} | {}'.format(exc, traceback.format_exc()))

    def _init(self):
        """
        Internal function that initializes asset widget
        Can be extended to add custom initialization functionality to asset widgets
        """

        if not self._asset:
            return

        self._asset_lbl.setText(self._asset.get_name())

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
        actions_added = self._fill_sync_action_menu(sync_menu)
        artella_action.triggered.connect(self._on_open_in_artella)
        view_locally_action.triggered.connect(self._on_view_locally)
        thumb_action.triggered.connect(partial(self.update_thumbnail_icon, True))

        context_menu.addAction(artella_action)
        context_menu.addAction(view_locally_action)
        context_menu.addSeparator()

        if actions_added:
            sync_action.setMenu(sync_menu)
            context_menu.addAction(sync_action)

        context_menu.addSeparator()
        context_menu.addAction(thumb_action)

    def _fill_sync_action_menu(self, sync_menu):
        """
        Internal function that fills sync menu with proper actions depending of the asset files supported
        :param sync_menu: Menu
        """

        if not sync_menu:
            return

        actions_to_add = list()

        for asset_type_name in self.asset.FILES:
            asset_type_icon = tpDcc.ResourcesMgr().icon(asset_type_name)
            asset_type_action = QAction(asset_type_icon, asset_type_name.title(), sync_menu)
            asset_type_action.triggered.connect(
                partial(self._on_sync, asset_type_name, defines.ArtellaFileStatus.ALL))
            actions_to_add.append(asset_type_action)

        if actions_to_add:
            download_icon = tpDcc.ResourcesMgr().icon('download')
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

        self._asset.open_in_artella()

    def _on_view_locally(self):
        """
        Internal callback function that is called when the user presses View Locally contextual menu action
        """

        self._asset.view_locally()

    def _on_sync(self, file_type, sync_type, ask=False):
        """
        Internal callback function that is called when the user tries to Sync an asset through UI
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

        self.startSync.emit(self.asset, file_type, sync_type)

    def _on_thumbnail_from_image(self, asset_icon):
        """
        Internal callback function that is called when an image object has finished loading
        """

        if asset_icon and not asset_icon.isNull():
            self._thumbnail_icon = asset_icon
            self._asset_btn.setIcon(asset_icon)
