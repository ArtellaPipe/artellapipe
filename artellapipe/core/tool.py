#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core classes for tools
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging.config

from tpQtLib.core import base

import artellapipe.register

LOGGER = logging.getLogger()


class ToolAttacher(object):
    Window = 0
    Dialog = 1


class Tool(base.BaseWidget, object):

    ATTACHER_TYPE = ToolAttacher.Window

    def __init__(self, project, config, parent=None):

        self._project = project
        self._config = config
        self._attacher = None

        super(Tool, self).__init__(parent=parent)

    @property
    def project(self):
        return self._project

    @property
    def config(self):
        return self._config

    def set_attacher(self, attacher):
        self._attacher = attacher
        if attacher:
            self.post_attacher_set()

    def close_tool_attacher(self):
        if not self._attacher:
            self.close_tool()

        if self.ATTACHER_TYPE == ToolAttacher.Window:
            self._attacher.fade_close()
        elif self.ATTACHER_TYPE == ToolAttacher.Dialog:
            self._attacher.fade_close()
        else:
            self.close_tool()

    def post_attacher_set(self):
        """
        Function that is called once an attacher has been set
        Override in child classes
        """

        pass

    def settings(self):
        """
        Returns settings of the attacher
        :return: QtSettings
        """

        if not self._attacher:
            return None

        return self._attacher.settings()

    def save_settings(self):
        """
        Save settings of the attacher
        """

        if not self._attacher:
            return None

        return self._attacher.save_settings()

    def show_ok_message(self, msg):
        """
        Shows an ok message in the attacher
        :param msg: str
        """

        if not self._attacher:
            return

        if not hasattr(self._attacher, 'show_ok_message'):
            LOGGER.warning(
                'Tool Attacher for "{}" has no show_ok_message available!'.format(self.__class__.__name__))

        LOGGER.info(msg)
        self._attacher.show_ok_message(msg)

    def show_warning_message(self, msg):
        """
        Shows a warning message in the attacher
        :param msg: str
        """

        if not self._attacher:
            return

        if not hasattr(self._attacher, 'show_warning_message'):
            LOGGER.warning(
                'Tool Attacher for "{}" has no show_warning_message available!'.format(self.__class__.__name__))

        LOGGER.warning(msg)
        self._attacher.show_warning_message(msg)

    def show_error_message(self, msg):
        """
        Shows an error message in the attacher
        :param msg: str
        """

        if not self._attacher:
            return

        if not hasattr(self._attacher, 'show_error_message'):
            LOGGER.warning(
                'Tool Attacher f>or "{}" has no show_error_message available!'.format(self.__class__.__name__))

        LOGGER.error(msg)
        self._attacher.show_error_message(msg)

    def close_tool(self):
        """
        Close tool
        """

        self.close()


artellapipe.register.register_class('Tool', Tool)
