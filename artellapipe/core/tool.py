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
import webbrowser

import tpDcc
from tpDcc.core import tool
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import toolset, buttons

import artellapipe
import artellapipe.register


class ToolAttacher(object):
    Window = 0
    Dialog = 1


class ArtellaTool(tool.DccTool, object):
    def __init__(self, *args, **kwargs):

        self._project = kwargs.pop('project')
        project_name = self._project.get_clean_name()
        config_name = kwargs['config'].data['fullname'].replace('.', '-')
        config_dict = kwargs.get('config_dict', dict())
        config_dict.update({
            'join': os.path.join,
            'user': os.path.expanduser('~'),
            'filename': kwargs['config'].data['filename'],
            'fullname': kwargs['config'].data['fullname'],
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

    def launch(self, *args, **kwargs):
        return self.launch_frameless(*args, **kwargs)

    def run_tool(self, frameless_active=True, tool_kwargs=None):
        """
        Overrides tool.DccTool run_tool function
        Function that launches current tool
        :param frameless_active: bool, Whether the tool will be launch in frameless mode or not
        :param tool_kwargs: dict, dictionary of arguments to launch tool with
        :return:
        """

        tool_name = self.config.get('name', default='Tool')
        tool_id = self.config.get('id')
        if not tool_id:
            artellapipe.logger.warning('Impossible to run tool with id: "{}"'.format(tool_id))
            return None

        toolset_class = tpDcc.ToolsetsMgr().toolset(tool_id)
        if not toolset_class:
            artellapipe.logger.warning('Impossible to run tool! No toolset found with id: "{}"'.format(tool_id))
            return None

        toolset_inst = toolset_class(**tool_kwargs if tool_kwargs else dict())
        toolset_inst.pre_content_setup()
        toolset_contents = toolset_inst.contents()
        for toolset_widget in toolset_contents:
            toolset_inst.add_stacked_widget(toolset_widget)
        toolset_inst.post_content_setup()
        # toolset_inst.expand()

        project = toolset_inst.project

        self._attacher = artellapipe.Window(
            project=project, id=tool_id, title=tool_name, config=self.config, settings=self.settings,
            show_on_initialize=True, frameless=frameless_active, dockable=True)
        self._attacher.main_layout.addWidget(toolset_inst)
        # for toolset_widget in toolset_contents:
        #     self._attacher.main_layout.addWidget(toolset_widget)

        self._attacher.show()

        return self._attacher


class ArtellaToolset(toolset.ToolsetWidget, object):
    def __init__(self, *args, **kwargs):

        self._project = kwargs.pop('project', None)
        self._settings = kwargs.pop('settings', None)
        self._config = kwargs.pop('config', None)

        super(ArtellaToolset, self).__init__(*args, **kwargs)

    @property
    def project(self):
        return self._project

    def ui(self):
        super(ArtellaToolset, self).ui()

        info_icon = tpDcc.ResourcesMgr().icon('info1')
        bug_icon = tpDcc.ResourcesMgr().icon('bug')

        self._info_btn = buttons.BaseMenuButton()
        self._info_btn.set_icon(info_icon, size=12, color_offset=40)
        self._bug_btn = buttons.BaseMenuButton()
        self._bug_btn.set_icon(bug_icon, size=12, color_offset=40)

        self._title_frame._horizontal_layout.addWidget(self._info_btn)
        self._title_frame._horizontal_layout.addWidget(self._bug_btn)

        self._info_btn.clicked.connect(self._on_open_url)
        self._bug_btn.clicked.connect(self._on_send_bug)

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


class ArtellaToolWidget(base.BaseWidget, object):
    def __init__(self, project, config, parent=None):

        self._project = project
        self._config = config

        super(ArtellaToolWidget, self).__init__(parent=parent)

    @property
    def project(self):
        return self._project

    @property
    def config(self):
        return self._config


artellapipe.register.register_class('Tool', ArtellaTool)
artellapipe.register.register_class('Toolset', ArtellaToolset)
artellapipe.register.register_class('ToolWidget', ArtellaToolWidget)
