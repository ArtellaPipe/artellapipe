#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base wrapper classes to create DCC windows
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import webbrowser

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpQtLib
from tpQtLib.widgets import statusbar

import artellapipe


class ArtellaWindowStatusBar(statusbar.StatusWidget, object):
    def __init__(self, parent=None):
        super(ArtellaWindowStatusBar, self).__init__(parent)

        self._info_url = None

        self.setFixedHeight(25)
        self._info_btn = QPushButton()
        self._info_btn.setIconSize(QSize(25, 25))
        self._info_btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._info_btn.setIcon(artellapipe.resource.icon('info1'))
        self._info_btn.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self.main_layout.insertWidget(0, self._info_btn)

        self._info_btn.clicked.connect(self._on_open_url)

    def set_info_url(self, url):
        """
        Sets the URL used to open tool info documentation web
        :param url: str
        """

        self._info_url = url

    def has_url(self):
        """
        Returns whether the URL documentation web is set or not
        :return: bool
        """

        if self._info_url:
            return True

        return False

    def show_info(self):
        """
        Shows the info button of the status bar
        """

        self._info_btn.setVisible(True)

    def hide_info(self):
        """
        Hides the info button of the status bar
        """

        self._info_btn.setVisible(False)

    def open_info_url(self):
        """
        Opens tool documentation URL in user web browser
        """

        if self._info_url:
            webbrowser.open_new_tab(self._info_url)

    def _on_open_url(self):
        """
        Internal callback function that is called when the user presses the info icon button
        :return:
        """

        self.open_info_url()


class ArtellaWindow(tpQtLib.MainWindow, object):

    STATUS_BAR_WIDGET = ArtellaWindowStatusBar

    def __init__(self, name='ArtellaWindow', title='Artella - Window', size=(800, 535), fixed_size=False, parent=None):
        super(ArtellaWindow, self).__init__(
            name=name,
            title=title,
            size=size,
            fixed_size=fixed_size,
            auto_run=True,
            frame_less=True,
            use_style=False,
            parent=parent
        )

        if self.parent():
            for widget in self.parent().findChildren(QMainWindow):
                if widget is not self:
                    if widget.objectName() == self.objectName():
                        widget.close()

    def ui(self):
        super(ArtellaWindow, self).ui()

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.main_layout.addLayout(title_layout)

        self._logo_view = QGraphicsView()
        self._logo_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._logo_view.setMaximumHeight(110)
        self._logo_scene = QGraphicsScene()
        self._logo_scene.setSceneRect(QRectF(0, 0, 2000, 100))
        self._logo_view.setScene(self._logo_scene)
        self._logo_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._logo_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._logo_view.setFocusPolicy(Qt.NoFocus)

        title_background_pixmap = self._get_title_pixmap()
        self._logo_scene.addPixmap(title_background_pixmap)
        title_layout.addWidget(self._logo_view)

        if not self._status_bar.has_url():
            self._status_bar.hide_info()

    def resizeEvent(self, event):
        """
        Overrides base tpQtLib.MainWindow resizeEvent function
        :param event: QSizeEvent
        """

        # TODO: Take the width from the QGraphicsView not hardcoded :)
        self._logo_view.centerOn(1000, 0)
        return super(ArtellaWindow, self).resizeEvent(event)

    def set_info_url(self, url):
        """
        Sets the info URL of the current window
        :param url: str
        """

        if not url:
            return

        self._status_bar.set_info_url(url)

        if not self._status_bar.has_url():
            self._status_bar.hide_info()
        else:
            self._status_bar.show_info()

    def add_logo(self, logo_pixmap, offset=(930, 0)):
        """
        Adds  new logo into window title
        :param logo_pixmap: QPixmap
        :param offset: tuple(int, int)
        """

        new_logo = self._logo_scene.addPixmap(logo_pixmap)
        new_logo.setOffset(offset[0], offset[1])

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        return artellapipe.resource.pixmap(name='artella_title', extension='png')
        # title_logo.setOffset(offset[0], offset[1])

