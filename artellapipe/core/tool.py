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

import os

import tpDcc
from tpDcc.core import tool
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import toolset, buttons, message

import artellapipe
import artellapipe.register


class ToolAttacher(object):
    Window = 0
    Dialog = 1


class ArtellaTool(tool.DccTool, object):
    def __init__(self, *args, **kwargs):

        self._project = kwargs.pop('project')
        project_name = self._project.get_clean_name()
        config_name = self.FULL_NAME.replace('.', '-')
        config_dict = kwargs.get('config_dict', dict())
        config_dict.update({
            'join': os.path.join,
            'user': os.path.expanduser('~'),
            'filename': self.FILE_NAME,
            'fullname': self.FULL_NAME,
            'project': project_name
        })
        new_config = tpDcc.ConfigsMgr().get_config(
            config_name=config_name,
            package_name=project_name,
            root_package_name='artellapipe',
            environment=self._project.get_environment(),
            config_dict=config_dict
        )
        kwargs['config'] = new_config

        super(ArtellaTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = tool.DccTool.config_dict(file_name=file_name)
        tool_config = {
            'logo': 'artella'
        }
        base_tool_config.update(tool_config)

        return base_tool_config

    def launch(self, *args, **kwargs):
        return self.launch_frameless(*args, **kwargs)

    def run_tool(self, frameless_active=True, tool_kwargs=None, attacher_class=None):
        if 'project' not in tool_kwargs or not tool_kwargs['project']:
            tool_kwargs['project'] = self._project
        return super(ArtellaTool, self).run_tool(
            frameless_active=frameless_active, tool_kwargs=tool_kwargs, attacher_class=artellapipe.Window)


class ArtellaToolset(toolset.ToolsetWidget, object):
    def __init__(self, *args, **kwargs):

        self._project = kwargs.pop('project', None)
        self._settings = kwargs.pop('settings', None)
        self._config = kwargs.pop('config', None)

        super(ArtellaToolset, self).__init__(*args, **kwargs)

    @property
    def project(self):
        return self._project

    @property
    def settings(self):
        return self._settings

    @property
    def config(self):
        return self._config

    def ui(self):
        super(ArtellaToolset, self).ui()

        bug_icon = tpDcc.ResourcesMgr().icon('bug')

        self._bug_btn = buttons.BaseMenuButton(parent=self)
        self._bug_btn.setFixedWidth(22)
        self._bug_btn.setFixedHeight(22)
        self._bug_btn.set_icon(bug_icon, size=12, color_offset=40)

        self._title_frame._horizontal_layout.addWidget(self._bug_btn)

        self._bug_btn.clicked.connect(self._on_send_bug)

    def show_bug(self):
        self._bug_btn.setVisible(True)

    def hide_bug(self):
        self._bug_btn.setVisible(False)

    def _on_send_bug(self):

        if not self._project:
            return False
        # artellapipe.ToolsMgr().run_tool('artellapipe-tools-bugtracker', extra_args={'tool': self._tool})


class ArtellaToolWidget(base.BaseWidget, object):
    def __init__(self, project, config, settings, parent):

        self._project = project
        self._config = config
        self._settings = settings
        self._toolset = parent

        super(ArtellaToolWidget, self).__init__(parent=parent)

    @property
    def project(self):
        return self._project

    @property
    def config(self):
        return self._config

    @property
    def settings(self):
        return self._settings

    @property
    def toolset(self):
        return self._toolset

    def close_tool_attacher(self):
        if self.toolset and hasattr(self.toolset, 'attacher'):
            if not self.toolset.attacher:
                return
            try:
                self.toolset.attacher.fade_close()
            except Exception:
                self.toolset.attacher.close()

    def show_ok_message(self, msg, msecs=3):
        """
        Set a success message to be displayed in the status widget
        :param msg: str
        :param msecs: float
        """

        message.PopupMessage.success(msg, parent=self, duration=msecs, closable=True)

    def show_info_message(self, msg, msecs=3):
        """
        Set an info message to be displayed in the status widget
        :param msg: str
        :param msecs: float
        """

        message.PopupMessage.info(msg, parent=self, duration=msecs, closable=True)

    def show_warning_message(self, msg, msecs=3):
        """
        Set a warning message to be displayed in the status widget
        :param msg: str
        :param msecs: float
        """

        message.PopupMessage.warning(msg, parent=self, duration=msecs, closable=True)

    def show_error_message(self, msg, msecs=3):
        """
        Set an error message to be displayed in the status widget
        :param msg: str
        :param msecs: float
        """

        message.PopupMessage.error(msg, parent=self, duration=msecs, closable=True)
