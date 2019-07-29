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
import sys
import shutil
import getpass
import datetime
import tempfile
import webbrowser
try:
    from urllib import quote
except ImportError:
    from urllib2 import quote

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpQtLib.widgets import splitters
from tpQtLib.core import qtutils, image

import artellapipe
from artellapipe.gui import dialog


class ArtellaBugTracker(dialog.ArtellaDialog, object):
    def __init__(self, project, tool_name=None, parent=None):

        self._screen_pixmap = None
        self._tool_name = tool_name
        self._project = project

        super(ArtellaBugTracker, self).__init__(
            name='ArtellaBugTracker',
            title='Artella - Bug Tracker',
            parent=parent
        )
    @classmethod
    def run(cls, project, traceback):
        dlg = cls(project=project)
        dlg.update_capture()
        dlg.set_trace(traceback)
        dlg.exec_()

    def ui(self):
        super(ArtellaBugTracker, self).ui()

        logo_pixmap = artellapipe.resource.pixmap(name='bugtracker_logo', extension='png')
        warning_pixmap = artellapipe.resource.pixmap(name='warning', category='icons', theme='color').scaled(QSize(24, 24))
        bug_icon = artellapipe.resource.icon('bug')

        self.setWindowIcon(bug_icon)
        self.set_logo(logo_pixmap)

        self._capture_lbl = QLabel()
        self._capture_lbl.setAlignment(Qt.AlignCenter)
        self._trace_text = QTextEdit()
        self._trace_text.setReadOnly(True)
        self._trace_text.setEnabled(False)
        self._send_btn = QPushButton('Send Bug')
        self._send_btn.setEnabled(False)

        self._add_error_img_cbx = QCheckBox('Include Error Image')
        self._add_error_img_cbx.setChecked(True)
        note_layout = QHBoxLayout()
        note_layout.setAlignment(Qt.AlignLeft)
        self._note_icon = QLabel()
        self._note_icon.setPixmap(warning_pixmap)
        self._note_text = QLabel('Error image will be sended to: \n\n{}\n\nThey will be able to access to it. So make sure your screen does not have sensible or confidential information'.format('\n    '.join(self._project.emails)))
        note_layout.addWidget(self._note_icon)
        note_layout.addWidget(qtutils.get_horizontal_separator())
        note_layout.addWidget(self._note_text)

        self._steps_area = QTextEdit()

        txt_msg = 'Explain briefly how to reproduce the error'
        steps_lbl = QLabel(txt_msg)
        if qtutils.is_pyside2():
            self._steps_area.setPlaceholderText(txt_msg)
        self._steps_area.setMinimumHeight(200)

        self.main_layout.addWidget(self._capture_lbl)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._trace_text)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._add_error_img_cbx)
        self.main_layout.addLayout(note_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())
        if qtutils.is_pyside():
            self.main_layout.addWidget(steps_lbl)
        self.main_layout.addWidget(self._steps_area)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._send_btn)

        self._on_update_error_info()

    def setup_signals(self):
        self._send_btn.clicked.connect(self._on_send_bug)
        self._add_error_img_cbx.toggled.connect(self._on_update_error_info)

    def update_capture(self):
        """
        Updates current capture
        """

        if qtutils.is_pyside2():
            self._screen_pixmap = QApplication.primaryScreen().grabWindow(QApplication.desktop().winId())
        else:
            self._screen_pixmap = QPixmap.grabWindow(QApplication.desktop().winId())
        self._capture_lbl.setPixmap(self._screen_pixmap.scaled(850, 338, Qt.KeepAspectRatio))
        self._update_ui()

    def set_trace(self, trace):
        """
        Sets the traceback text
        :param trace: str
        """

        self._trace_text.setPlainText(str(trace))
        self._update_ui()

    def _update_ui(self):
        """
        Internal function that updates Artella Bug Tracker UI
        """

        self._send_btn.setEnabled(self._trace_text.toPlainText() != '')

    def _on_update_error_info(self):
        self._note_icon.setVisible(self._add_error_img_cbx.isChecked())
        self._note_text.setVisible(self._add_error_img_cbx.isChecked())

    def _on_send_bug(self):
        """
        Internal callback function that is called when the user press Send Bug button
        """

        if not self._project:
            artellapipe.logger.warning('Impossible to send bug because there is project defined')
            return

        project_name = self._project.name.title()
        if not self._project.emails:
            artellapipe.logger.warning('Impossible to send bug because there is no emails defined in the project: {}'.format(project_name))
            return

        user = '{0}_{1}'.format(getpass.getuser(), sys.platform)
        current_time = str(datetime.datetime.now())
        bug_name = '{} : {}'.format(user, current_time)
        current_steps = self._steps_area.toPlainText()

        image_base64 = 'none'
        temp_dir = tempfile.mkdtemp()
        try:
            temp_path = os.path.join(temp_dir, 'artella_bug.png')
            self._screen_pixmap.scaled(500, 200, Qt.KeepAspectRatio).save(temp_path)
            image_base64 = image.image_to_base64(image_path=temp_path)
        finally:
            try:
                shutil.rmtree(temp_path)
            except Exception:
                pass

        msg = self._trace_text.toPlainText()
        msg += '\n----------------------------\n'
        msg += 'User: {}\n'.format(user)
        msg += 'Time: {}\n'.format(current_time)
        msg += 'Bug Name: {}\n'.format(os.path.basename(bug_name))
        msg += 'Date: {}\n'.format(current_time)
        msg += 'Steps: \n{}\n'.format(current_steps)

        if len(image_base64) <= 30000 and self._add_error_img_cbx.isChecked():
            msg += 'Bug: {}\n'.format(str(image_base64))

        if self._tool_name:
            subject = '[{}][Bug][{}]{}'.format(project_name, self._tool_name, user)
        else:
            subject = '[{}][Bug]{}'.format(project_name, user)

        webbrowser.open("mailto:{}?subject={}&body={}".format(';'.join(self._project.emails), subject, quote(str(msg))))


