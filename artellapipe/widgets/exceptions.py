#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains exceptions related widgets
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


from Qt.QtGui import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.qt.widgets import label, buttons, dividers, message


class ArtellaExceptionDialog(tp.Dialog):
    def __init__(self, exc_text, exc_trace):
        self._text = exc_text
        self._trace = exc_trace
        super(ArtellaExceptionDialog, self).__init__(title='Artella-Error', show_on_initialize=False)

        self.setWindowIcon(tp.ResourcesMgr().icon('artella'))

    def ui(self):
        super(ArtellaExceptionDialog, self).ui()

        text_lbl = label.BaseLabel(str(self._text) if self._text else '')
        self._error_text = QPlainTextEdit(str(self._trace) if self._trace else '')
        self._error_text.setReadOnly(True)
        self._error_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout.addWidget(text_lbl)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addWidget(self._error_text)

        buttons_lyt = QHBoxLayout()
        self._copy_to_clipboard_btn = buttons.BaseButton('Copy to Clipboard')
        self._hide_details_btn = buttons.BaseButton('Hide Details...')
        buttons_lyt.addStretch()
        buttons_lyt.addWidget(self._copy_to_clipboard_btn)
        buttons_lyt.addWidget(self._hide_details_btn)
        self.main_layout.addStretch()
        self.main_layout.addLayout(buttons_lyt)

    def setup_signals(self):
        self._hide_details_btn.clicked.connect(self._on_toggle_details)
        self._copy_to_clipboard_btn.clicked.connect(self._on_copy_to_clipboard)

    def _on_toggle_details(self):
        self._error_text.setVisible(not self._error_text.isVisible())
        if self._error_text.isVisible():
            self._hide_details_btn.setText('Hide Error Trace')
        else:
            self._hide_details_btn.setText('Show Error Trace')

    def _on_copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._error_text.toPlainText(), QClipboard.Clipboard)
        if clipboard.supportsSelection():
            clipboard.setText(self._error_text.toPlainText(), QClipboard.Selection)
        message.PopupMessage.success(text='Error message copied to clipboard!.', parent=self)
