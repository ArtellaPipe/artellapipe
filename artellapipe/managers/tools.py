#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager that handles Artella Tools
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDcc

import artellapipe


class ToolsManager(object):

    def run_tool(self, tool_id, do_reload=False, debug=False, project=None, *args, **kwargs):
        """
        Launches artellapipe tool
        :param tool_id: str
        :param do_reload: bool
        :param debug: bool
        :param project: ArtellaProject or None
        """

        if not project:
            project = artellapipe.project

        return tpDcc.ToolsMgr().launch_tool_by_id(
            tool_id, do_reload=do_reload, debug=debug, project=project, *args, **kwargs)
