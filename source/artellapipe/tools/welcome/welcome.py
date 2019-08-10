#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allows to detect errors and trace calls and easily them to TDs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import random
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpQtLib
from tpQtLib.core import base, qtutils, animation
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import dialog


class WelcomeFrame(QFrame, object):
    def __init__(self, pixmap, parent=None):
        super(WelcomeFrame, self).__init__(parent)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self._pixmap = pixmap
        self.setStyleSheet('QFrame { border-radius: 10px; }')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        """
        Override base QFrame paintEvent function
        :param event: QPaintEvent
        """

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self.width(), self.height(), self._pixmap)


class WelcomeWidget(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(WelcomeWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        return main_layout

    def ui(self):
        super(WelcomeWidget, self).ui()

        self.main_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        lbl = QLabel('Welcome to {}!'.format(self._project.name.title()))
        lbl.setStyleSheet('font-size: 35px; font-family: "Montserrat";')
        self.main_layout.addWidget(lbl)
        self.main_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))


class ShortcutsWidget(base.BaseWidget, object):
    def __init__(self, project, parent=None):
        self._project = project

        super(ShortcutsWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        return main_layout

    def ui(self):
        super(ShortcutsWidget, self).ui()

        lbl = QLabel('{} Tools can be accessed through: '.format(self._project.name.title()))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet('font-size: 14px; font-family: "Montserrat";')

        shelf_lbl = QLabel('{} Shelf'.format(self._project.name.title()))
        shelf_lbl.setAlignment(Qt.AlignCenter)
        shelf_lbl.setStyleSheet('font-size: 18px; font-family: "Montserrat"; font-weight: bold')

        self.main_layout.addWidget(lbl)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(shelf_lbl)


class FinalWidget(base.BaseWidget, object):
    def __init__(self, project, parent=None):
        self._project = project

        super(FinalWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        return main_layout

    def ui(self):
        super(FinalWidget, self).ui()

        ready_lbl = QLabel('You are ready to go!')
        ready_lbl.setAlignment(Qt.AlignCenter)
        ready_lbl.setStyleSheet('font-size: 24px; font-family: "Montserrat"; font-weight: bold;')

        more_info_lbl = QLabel('You can find more info in the following links')
        more_info_lbl.setAlignment(Qt.AlignCenter)
        more_info_lbl.setStyleSheet('font-size: 18px; font-family: "Montserrat";')

        icons_layout = QHBoxLayout()
        icons_layout.setContentsMargins(2, 2, 2, 2)
        icons_layout.setSpacing(2)

        doc_icon = artellapipe.resource.icon('manual')
        change_icon = artellapipe.resource.icon('document')

        self._documentation_btn = QToolButton()
        self._documentation_btn.setText('Open Documentation')
        self._documentation_btn.setIcon(doc_icon)
        self._documentation_btn.setIconSize(QSize(64, 64))
        self._documentation_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self._changelog_btn = QToolButton()
        self._changelog_btn.setText('Show Changelog')
        self._changelog_btn.setIcon(change_icon)
        self._changelog_btn.setIconSize(QSize(64, 64))
        self._changelog_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        icons_layout.addWidget(self._documentation_btn)
        icons_layout.addWidget(self._changelog_btn)

        self.main_layout.addWidget(ready_lbl)
        self.main_layout.addWidget(more_info_lbl)
        self.main_layout.addLayout(icons_layout)

    def setup_signals(self):
        self._documentation_btn.clicked.connect(self._on_open_documentation)
        self._changelog_btn.clicked.connect(self._on_open_changelog)

    def _on_open_documentation(self):
        """
        Internal callback function that is called when Opening Documentation button is pressed
        """

        self._project.open_documentation()

    def _on_open_changelog(self):
        """
        Internal callback function that is called when Show Changelog button is pressed
        """

        pass


class WelcomeDialog(dialog.ArtellaDialog, object):

    def __init__(self, project, parent=None):

        self._project = project
        self._radio_buttons = list()
        self._offset = 0

        super(WelcomeDialog, self).__init__(
            name='ArtellaWelcome',
            title='Artella - Welcome',
            show_dragger=False,
            fixed_size=True,
            parent=parent
        )

        self._init()

    def ui(self):
        super(WelcomeDialog, self).ui()

        self.resize(685, 290)

        self.setAttribute(Qt.WA_TranslucentBackground)
        if qtutils.is_pyside2():
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        main_frame = WelcomeFrame(pixmap=self._get_welcome_pixmap())
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(10, 0, 10, 0)
        frame_layout.setSpacing(2)
        main_frame.setLayout(frame_layout)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(2)
        frame_layout.addLayout(top_layout)

        version_layout = QHBoxLayout()
        version_layout.setContentsMargins(2, 2, 2, 2)
        version_layout.setSpacing(2)
        self._version_lbl = QLabel('Version')
        version_layout.addWidget(self._version_lbl)

        self._close_btn = QPushButton('')
        self._close_btn.setIcon(tpQtLib.resource.icon('close', theme='window'))
        self._close_btn.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._close_btn.setIconSize(QSize(25, 25))

        top_layout.addLayout(version_layout)
        top_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self._logo = QLabel('Logo')
        top_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        top_layout.addWidget(self._close_btn)

        base_frame = QFrame()
        base_frame.setObjectName('baseFrame')
        base_frame.setFrameShape(QFrame.NoFrame)
        base_frame.setFrameShadow(QFrame.Plain)
        # base_frame.setAttribute(Qt.WA_TranslucentBackground)
        base_frame.setStyleSheet('QFrame#baseFrame { background-color: rgba(100, 100, 100, 80); }')
        base_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        base_layout = QVBoxLayout()
        base_layout.setContentsMargins(2, 2, 2, 2)
        base_layout.setSpacing(2)
        base_frame.setLayout(base_layout)
        frame_layout.addWidget(base_frame)

        self._stack = QStackedWidget()
        self._stack.setAutoFillBackground(False)
        self._stack.setAttribute(Qt.WA_TranslucentBackground)
        base_layout.addWidget(self._stack)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(2, 2, 2, 2)
        bottom_layout.setSpacing(2)
        frame_layout.addLayout(bottom_layout)

        self._left_btn = QPushButton('Skip')
        self._left_btn.setMinimumSize(QSize(100, 30))
        self._left_btn.setStyleSheet(
            """
            QPushButton\n{\n\nbackground-color: rgb(250,250,250,30);\ncolor: rgb(250, 250, 250);\nborder-radius: 5px;\npadding-left: 15px;\npadding-right: 15px;\n}\n\nQPushButton:hover\n{\n\nbackground-color: rgb(250,250,250,20);\n}\n\nQPushButton:pressed\n{\n\nbackground-color: rgb(0,0,0,30);\n}
            """
        )
        self._right_btn = QPushButton('Next')
        self._right_btn.setMinimumSize(QSize(100, 30))
        self._right_btn.setStyleSheet(
            """
            QPushButton\n{\n\nbackground-color: rgb(250,250,250,30);\ncolor: rgb(250, 250, 250);\nborder-radius: 5px;\npadding-left: 15px;\npadding-right: 15px;\n}\n\nQPushButton:hover\n{\n\nbackground-color: rgb(250,250,250,20);\n}\n\nQPushButton:pressed\n{\n\nbackground-color: rgb(0,0,0,30);\n}
            """
        )

        self._radio_layout = QHBoxLayout()
        self._radio_layout.setContentsMargins(2, 2, 2, 2)
        self._radio_layout.setSpacing(2)

        bottom_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        bottom_layout.addWidget(self._left_btn)
        bottom_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        bottom_layout.addLayout(self._radio_layout)
        bottom_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        bottom_layout.addWidget(self._right_btn)
        bottom_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self.main_layout.addWidget(main_frame)

    def setup_signals(self):
        self._close_btn.clicked.connect(self.fade_close)
        self._right_btn.clicked.connect(lambda: self._on_button_clicked(+1))
        self._left_btn.clicked.connect(lambda: self._on_button_clicked(-1))

    def mousePressEvent(self, event):
        """
        Overrides base ArtellaDialog mousePressEvent function
        :param event: QMouseEvent
        """

        self._offset = event.pos()

    def mouseMoveEvent(self, event):
        """
        Overrides base ArtellaDialog mouseMoveEvent function
        :param event: QMouseEvent
        """

        x = event.globalX()
        y = event.globalY()
        x_w = self._offset.x()
        y_w = self._offset.y()
        self.move(x - x_w, y - y_w)

    def _init(self):
        """
        Initializes Welcome dialog
        """

        self._tab_opacity_effect = QGraphicsOpacityEffect(self)
        self._tab_opacity_effect.setOpacity(0)
        self._stack.setGraphicsEffect(self._tab_opacity_effect)

        self._setup_pages()

        self._set_index(0)

    def _setup_pages(self):
        """
        Internal callback function that set the pages of the stack
        Overrides to add new pages
        """

        self._welcome_widget = WelcomeWidget(project=self._project)
        self._shortcuts_widget = ShortcutsWidget(project=self._project)
        self._final_widget = FinalWidget(project=self._project)

        self._add_page(self._welcome_widget)
        self._add_page(self._shortcuts_widget)
        self._add_page(self._final_widget)

    def _get_welcome_pixmap(self):
        """
        Returns pixmap to be used as splash background
        :return: Pixmap
        """

        welcome_path = self._project.resource.get('images', 'welcome.png')
        if not os.path.isfile(welcome_path):
            welcome_Dir = os.path.dirname(welcome_path)
            welcome_files = [f for f in os.listdir(welcome_Dir) if f.startswith('welcome') and os.path.isfile(os.path.join(welcome_Dir, f))]
            if welcome_files:
                welcome_index = random.randint(0, len(welcome_files)-1)
                welcome_name, splash_extension = os.path.splitext(welcome_files[welcome_index])
                welcome_pixmap = self._project.resource.pixmap(welcome_name, extension=splash_extension[1:])
            else:
                welcome_pixmap = artellapipe.resource.pixmap('welcome')
        else:
            welcome_pixmap = self._project.resource.pixmap('welcome')

        return welcome_pixmap.scaled(QSize(800, 270))

    def _add_page(self, widget):
        """
        Adds a new widget into the stack
        :param widget: QWidget
        """

        total_pages = len(self._radio_buttons)
        new_radio = QRadioButton()
        if total_pages == 0:
            new_radio.setChecked(True)
        new_radio.clicked.connect(partial(self._set_index, total_pages))

        self._stack.addWidget(widget)
        self._radio_layout.addWidget(new_radio)
        self._radio_buttons.append(new_radio)

    def _increment_index(self, input):
        """
        Internal function that increases index of the stack widget
        :param input: int
        """

        current = self._stack.currentIndex()
        self._set_index(current + input)

    def _set_index(self, index):
        """
        Internal function that updates stack index and UI
        :param index: int
        """

        animation.fade_animation(start='current', end=0, duration=400, object=self._tab_opacity_effect)

        if index <= 0:
            index = 0
        if index >= self._stack.count() - 1:
            index = self._stack.count() - 1

        self._radio_buttons[index].setChecked(True)

        self.props_timer = QTimer(singleShot=True)
        self.props_timer.timeout.connect(self._on_fade_up_tab)
        self.props_timer.timeout.connect(lambda: self._stack.setCurrentIndex(index))
        self.props_timer.start(450)

        prev_text = 'Previous'
        next_text = 'Next'
        skip_text = 'Skip'
        close_text = 'Finish'

        print(index, self._stack.count() - 1, index==self._stack.count() - 1)

        if index == 0:
            self._left_btn.setText(skip_text)
            self._right_btn.setText(next_text)
        elif index < self._stack.count() - 1:
            self._left_btn.setText(prev_text)
            self._right_btn.setText(next_text)
        elif index == self._stack.count() - 1:
            self._left_btn.setText(prev_text)
            self._right_btn.setText(close_text)

    def _launch_project(self):
        """
        Internal function that closes Welcome dialog and launches project tools
        """

        self.fade_close()

    def _on_fade_up_tab(self):
        """
        Internal callback function that is called when stack index changes
        """

        animation.fade_animation(start='current', end=1, duration=400, object=self._tab_opacity_effect)

    def _on_button_clicked(self, input):
        """
        Internal callback function that is called when Next and and Skip buttons are pressed
        :param input: int
        """

        current = self._stack.currentIndex()
        action = 'flip'
        if current == 0:
            if input == -1:
                action = 'close'
        elif current == self._stack.count() - 1:
            if input == 1:
                action = 'close'
        if action == 'flip':
            self._increment_index(input)
        elif action == 'close':
            self._launch_project()


def run(project):
    welcome_dialog = WelcomeDialog(project=project)
    welcome_dialog.exec_()