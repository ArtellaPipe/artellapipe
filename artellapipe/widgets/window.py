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

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.qt.core import qtutils

import artellapipe


class ArtellaWindow(tpDcc.Window, object):
    def __init__(
            self,
            name='Window',
            title='Window',
            size=(800, 535),
            fixed_size=False,
            parent=None,
            *args,
            **kwargs):

        self._project = artellapipe.project

        super(ArtellaWindow, self).__init__(
            name=name,
            title=title,
            size=size,
            fixed_size=fixed_size,
            auto_run=True,
            frame_less=True,
            use_style=False,
            parent=parent,
            *args,
            **kwargs
        )

        window_icon = self._get_icon()
        self.setWindowIcon(window_icon)

        screen_geo = QApplication.desktop().screenGeometry()
        screen_width = screen_geo.width()
        screen_height = screen_geo.height()
        new_width = self.width()
        new_height = self.height()
        if self.width() > screen_width:
            new_width = 500
        if self.height() > screen_height:
            new_height = 500
        self.resize(new_width, new_height)
        self.center()

    def ui(self):
        super(ArtellaWindow, self).ui()

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.main_layout.insertLayout(0, title_layout)

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

        logo_pixmap = self._get_logo()
        if logo_pixmap and not logo_pixmap.isNull():
            win_logo = self._logo_scene.addPixmap(logo_pixmap)
            win_logo.setOffset(910, 0)

        if self._project.is_dev():
            int_colors = self._project.dev_color0.split(',')
            dev_style = "background-color: rgb({}, {}, {})".format(
                int_colors[0], int_colors[1], int_colors[2], 255)
            self._dragger.setStyleSheet(dev_style)

    def setWindowTitle(self, title):
        if self._project.is_dev() and self._project.get_environment() not in title:
            title = '{} - [{}]'.format(title, self._project.get_environment())

        super(ArtellaWindow, self).setWindowTitle(title)

    def closeEvent(self, event):
        # if self._tool:
        #     self._tool.close_tool()
        super(ArtellaWindow, self).closeEvent(event)

    def resizeEvent(self, event):
        """
        Overrides base tpQtLib.MainWindow resizeEvent function
        :param event: QSizeEvent
        """

        # TODO: Take the width from the QGraphicsView not hardcoded :)
        self._logo_view.centerOn(1000, 0)
        return super(ArtellaWindow, self).resizeEvent(event)

    @property
    def project(self):
        """
        Returns Artella project this window is linked to
        :return: ArtellaProject
        """

        return self._project

    def add_toolbar(self, name, area=Qt.TopToolBarArea):
        """
        Overrides base MainWindow add_toolbar function
        :param name: str
        :param area:
        :return:
        """

        new_toolbar = QToolBar(name)
        # The 0 widget is always the header view of the window
        self.main_layout.insertWidget(1, new_toolbar)
        return new_toolbar

    def add_logo(self, logo_pixmap, offset_x, offset_y):
        """
        Adds a new logo into the title with the given offset
        :param logo_pixmap: QPixmap
        :param offset_x: int
        :param offset_y: int
        """

        win_logo = self._logo_scene.addPixmap(logo_pixmap)
        win_logo.setOffset(offset_x, offset_y)

    def _get_logo(self):
        """
        Internal function that returns the logo used in window title
        """

        if self._config:
            config_logo = self._config.get('logo', None)
            if config_logo:
                win_logo = tpDcc.ResourcesMgr().pixmap(config_logo, extension='png', key='project')
                if not win_logo.isNull():
                    return win_logo

        return None

    def _get_icon(self):
        """
        Internal function that returns the icon used for the window
        :return: QIcon
        """

        if self._project:
            window_icon = self._project.icon
            if not window_icon.isNull():
                return window_icon
            else:
                self._project.logger.warning(
                    '{} Project Icon not found: {}!'.format(
                        self._project.name.title(), self._project.icon_name + '.png'
                    )
                )

        return tpDcc.ResourcesMgr().icon('artella')

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        if self._project:
            title_background = self._project.config.get('title_background')
            title_pixmap = tpDcc.ResourcesMgr().pixmap(name=title_background, extension='png', key='project')
            if not title_pixmap.isNull():
                return title_pixmap
            else:
                self._project.logger.warning('{} Project Title Background image not found: {}!'.format(
                    self._project.name.title(), title_background + '.png'))

        return tpDcc.ResourcesMgr().pixmap(name='title_background', extension='png')


def dock_window(project, window_class, min_width=300):
    """
    Utility function to dock Maya window
    :param project: ArtellaProject
    :param window_class: cls
    """

    if not tpDcc.is_maya():
        return

    import maya.cmds as cmds
    import maya.OpenMayaUI as OpenMayaUI
    try:
        cmds.deleteUI(window_class.name)
    except Exception:
        pass

    main_control = cmds.workspaceControl(
        window_class.name, ttc=["AttributeEditor", -1], iw=min_width, mw=True, wp='preferred', label=window_class.title)

    control_widget = OpenMayaUI.MQtUtil.findControl(window_class.name)
    control_wrap = qtutils.wrapinstance(int(control_widget), QWidget)
    control_wrap.setAttribute(Qt.WA_DeleteOnClose)
    win = window_class(project=project, parent=control_wrap)

    cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control, e=True, rs=True))

    win.show()

    return win
