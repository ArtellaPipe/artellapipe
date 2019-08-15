#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains publisher implementation for Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

import pyblish.api
import pyblish_lite

import tpDccLib as tp

from artellapipe.gui import window


class ArtellaPublisher(window.ArtellaWindow, object):

    LOGO_NAME = 'publisher_logo'

    def __init__(self, project):

        self._pyblish_window = None
        self._registered_plugin_paths = list()

        super(ArtellaPublisher, self).__init__(
            project=project,
            name='ArtellaPublisherWindow',
            title='Publisher',
            size=(1100, 900)
        )

        self._register_plugins()

    def setup_signals(self):
        self.windowClosed.connect(self._on_window_closed)

    def set_pyblish_window(self, pyblish_window):
        """
        Sets the Pyblish window wrapped by this window
        :param pyblish_window:
        """

        if self._pyblish_window:
            return

        # print(type(pyblish_window.controller.context))
        # pyblish_window.controller.context.data['project'] = self._project
        # pyblish_window.refresh()

        pyblish_window.controller.was_reset.connect(self._on_controller_reset)

        self.main_layout.addWidget(pyblish_window)
        self._pyblish_window = pyblish_window

    def _on_controller_reset(self):
        self._pyblish_window.controller.context.data['project'] = self._project

    def register_plugin_path(self, plugin_path):
        """
        Registers given plugin path
        :param plugin_path: str
        """

        if not os.path.exists(plugin_path):
            return
        pyblish.api.register_plugin_path(str(plugin_path))
        self._registered_plugin_paths.append(plugin_path)

    def _register_plugins(self):
        """
        Internal function that registers current available plugins in project
        """

        plugin_paths = self._project.get_publisher_plugin_paths()
        for p in plugin_paths:
            self.register_plugin_path(p)

    def _deregister_plugins(self):
        """
        Internal function that deregister current registered plugin paths
        """

        for p in self._registered_plugin_paths:
            pyblish.api.deregister_plugin_path(str(p))

    def _on_window_closed(self):
        """
        Internal callback function that is called when window is closed
        """

        self._deregister_plugins()


def run(project):

    if tp.is_maya():
        pyblish.api.register_host('maya')
    elif tp.is_houdini():
        pyblish.api.register_host('houdini')

    win = ArtellaPublisher(project=project)
    win.show()
    win.setStyleSheet(win.styleSheet() + """\n
          #Header {
          background: "#555";
          border: 1px solid "#444";
      }

      #Header QRadioButton {
          border-right: 1px solid #333;
          left: 2px;
      }

      #Header QRadioButton::indicator {
          width: 65px;
          height: 40px;
          border: 0px solid "transparent";
          border-bottom: 3px solid "transparent";
          background-repeat: no-repeat;
          background-position: center center;
      }

      #Header QRadioButton::indicator:checked {
          width: 65px;
          height: 40px;
          border: 0px solid "transparent";
          border-bottom: 3px solid "transparent";
          background-repeat: no-repeat;
          background-position: center center;
          image: none;
      }

      #Header QRadioButton:checked {
          background-color: rgba(255, 255, 255, 20);
          border-bottom: 3px solid "lightblue";
      }

      #Header QRadioButton::indicator:unchecked {
          image: none;
      }
      """)

    pyblish_win = pyblish_lite.show()
    win.set_pyblish_window(pyblish_win)

    return win
