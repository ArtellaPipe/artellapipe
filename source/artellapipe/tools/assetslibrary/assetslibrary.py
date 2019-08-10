#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to interact with Artella functionality inside DCCS
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import weakref

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from artellapipe.core import assetsviewer
from artellapipe.gui import window

global asset_viewer_window


class ArtellaAssetsViewer(QWidget, object):

    # Necessary to support Maya dock
    name = 'ArtellaAssetsLibrary'
    title = 'Artella Assets Viewer'

    _instances = list()

    def __init__(self, project, parent=None):

        self._project = project

        main_window = tp.Dcc.get_main_window()
        if parent is None:
            parent = main_window

        super(ArtellaAssetsViewer, self).__init__(parent=parent)

        if tp.is_maya():
            ArtellaAssetsViewer._delete_instances()
            self.__class__._instances.append(weakref.proxy(self))

        self.ui()
        self.resize(150, 800)

        global asset_viewer_window
        asset_viewer_window = self

        self._assets_viewer.update_assets()

    @staticmethod
    def _delete_instances():
        for ins in ArtellaAssetsViewer._instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except Exception:
                pass

            ArtellaAssetsViewer.instances.remove(ins)
            del ins

    def ui(self):

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        if tp.is_maya():
            self.parent().layout().addLayout(self.main_layout)
        else:
            self.setLayout(self.main_layout)

        self._assets_viewer = assetsviewer.AssetsViewer(
            project=self._project,
            column_count=2,
            parent=self
        )
        self._assets_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        top_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.addLayout(top_layout)

        self.main_layout.addWidget(self._assets_viewer)


class ArtellaAssetsLibrary(window.ArtellaWindow, object):

    LOGO_NAME = 'assetsmanager_logo'

    def __init__(self, project, parent=None):
        super(ArtellaAssetsLibrary, self).__init__(
            project=project,
            name='ManagerWindow',
            title='Manager',
            size=(1100, 900),
            parent=parent
        )

    def ui(self):
        super(ArtellaAssetsLibrary, self).ui()


def run(project):
    if tp.is_maya():
        win = window.dock_window(project=project, window_class=ArtellaAssetsViewer)
        return win
    else:
        win = ArtellaAssetsLibrary(project=project)
        win.show()
        return win
