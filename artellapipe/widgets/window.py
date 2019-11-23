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

import tpDccLib as tp

import tpQtLib
from tpQtLib.core import qtutils, statusbar

import artellapipe
from artellapipe.utils import resource


class ArtellaWindowStatusBar(statusbar.StatusWidget, object):
    def __init__(self, parent=None):
        super(ArtellaWindowStatusBar, self).__init__(parent)

        self._project = None
        self._info_url = None
        self._tool = None

        self.setFixedHeight(25)
        self._info_btn = QPushButton()
        self._info_btn.setIconSize(QSize(25, 25))
        self._info_btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._info_btn.setIcon(resource.ResourceManager().icon('info1'))
        self._info_btn.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')

        self._bug_btn = QPushButton()
        self._bug_btn.setIconSize(QSize(25, 25))
        self._bug_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._bug_btn.setIcon(resource.ResourceManager().icon('bug'))
        self._bug_btn.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')

        self.main_layout.insertWidget(0, self._info_btn)
        self.main_layout.insertWidget(1, self._bug_btn)

        self._info_btn.clicked.connect(self._on_open_url)
        self._bug_btn.clicked.connect(self._on_send_bug)

    def set_project(self, project):
        self._project = project

    def set_info_url(self, url):
        """
        Sets the URL used to open tool info documentation web
        :param url: str
        """

        self._info_url = url

    def set_tool(self, tool):
        """

        :param tool:
        :return:
        """

        self._tool = tool

    def has_url(self):
        """
        Returns whether the URL documentation web is set or not
        :return: bool
        """

        if not self._project:
            return False

        if self._info_url:
            return True

        return False

    def has_tool(self):

        if not self._project:
            return False

        if self._tool:
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

    def show_bug(self):
        self._bug_btn.setVisible(True)

    def hide_bug(self):
        self._bug_btn.setVisible(False)

    def open_info_url(self):
        """
        Opens tool documentation URL in user web browser
        """

        if not self._project:
            return False

        if self._info_url:
            webbrowser.open_new_tab(self._info_url)

    def _on_send_bug(self):

        if not self._project:
            return False

        artellapipe.ToolsMgr().run_tool(self._project, 'bugtracker', extra_args={'tool': self._tool})

    def _on_open_url(self):
        """
        Internal callback function that is called when the user presses the info icon button
        :return:
        """

        self.open_info_url()


class ArtellaWindow(tpQtLib.Window, object):

    LOGO_NAME = None
    STATUS_BAR_WIDGET = ArtellaWindowStatusBar

    def __init__(
            self,
            project=None,
            tool=None,
            name='Window',
            title='Window',
            size=(800, 535),
            fixed_size=False,
            parent=None,
            *args,
            **kwargs):

        self._project = project
        self._tool = tool

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

        if self.parent():
            for widget in self.parent().findChildren(QMainWindow):
                if widget is not self:
                    if widget.objectName() == self.objectName():
                        widget.close()

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

        self.setAttribute(Qt.WA_DeleteOnClose, True)

        window_icon = self._get_icon()
        self.setWindowIcon(window_icon)

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

        self._status_bar.set_project(self._project)
        self._status_bar.set_tool(self._tool)
        if not self._status_bar.has_url():
            self._status_bar.hide_info()
        if not self._status_bar.has_tool():
            self._status_bar.hide_bug()

        if self._tool:
            self.main_layout.addWidget(self._tool)

        if self._project.is_dev():
            int_colors = self._project.dev_color0.split(',')
            dev_style = "background-color: rgb({}, {}, {})".format(
                int_colors[0], int_colors[1], int_colors[2], 255)
            self._dragger.setStyleSheet(dev_style)

    def setWindowTitle(self, title):
        if self._project.is_dev():
            title = '{} - [{}]'.format(title, self._project.get_environment())

        super(ArtellaWindow, self).setWindowTitle(title)

    def closeEvent(self, event):
        if self._tool:
            self._tool.close_tool()
        super(ArtellaWindow, self).closeEvent(event)
        # event.accept()

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

    def _get_logo(self):
        """
        Internal function taht returns the logo used in window title
        """

        if self.LOGO_NAME:
            if self._project:
                win_logo = resource.ResourceManager().pixmap(self.LOGO_NAME, extension='png')
                if not win_logo.isNull():
                    return win_logo
                else:
                    self._project.logger.warning(
                        '{} Project Logo Image not found: {}!'.format(
                            self._project.name.title(), self.LOGO_NAME + '.png'
                        )
                    )

            win_logo = resource.ResourceManager().pixmap(self.LOGO_NAME, extension='png')
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

        return resource.ResourceManager().icon('artella')

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        if self._project:
            title_background = self._project.config.get('title_background')
            title_pixmap = resource.ResourceManager().pixmap(name=title_background, extension='png')
            if not title_pixmap.isNull():
                return title_pixmap
            else:
                self._project.logger.warning('{} Project Title Background image not found: {}!'.format(
                    self._project.name.title(), title_background + '.png'))

        return resource.ResourceManager().pixmap(name='title_background', extension='png')


def dock_window(project, window_class, min_width=300):
    """
    Utility function to dock Maya window
    :param project: ArtellaProject
    :param window_class: cls
    """

    if not tp.is_maya():
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


artellapipe.register.register_class('Window', ArtellaWindow)
