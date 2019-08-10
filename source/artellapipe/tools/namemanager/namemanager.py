#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow to define the nomenclature of the pipeline files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from artellapipe.gui import window

from tpNameIt.core import nameit


class NameWidget(nameit.NameIt, object):
    def __init__(self, project, parent=None):
        self._project = project
        NameWidget.DATA_FILE = self._project.naming_file
        super(NameWidget, self).__init__(parent=parent)


class NameManager(window.ArtellaWindow, object):

    LOGO_NAME = 'manager_logo'

    def __init__(self, project):
        super(NameManager, self).__init__(
            project=project,
            name='NameManagerWindow',
            title='Name Manager',
            size=(600, 900)
        )

    def ui(self):
        super(NameManager, self).ui()

        self._name_widget = NameWidget(project=self._project)
        self.main_layout.addWidget(self._name_widget)

    @property
    def nameit(self):
        return self._name_widget


def run(project):
    win = NameManager(project=project)
    win.show()

    return win
