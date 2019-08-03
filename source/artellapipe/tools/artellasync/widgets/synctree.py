#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to easily sync files from Artella server
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


from Qt.QtWidgets import *

from tpQtLib.core import base


class ArtellaSyncWidget(base.BaseWidget, object):
    def __init__(self, parent=None):
        super(ArtellaSyncWidget, self).__init__(parent=parent)

    def ui(self):
        super(ArtellaSyncWidget, self).ui()

        self._sync_tree = ArtellaSyncTree()
        self.main_layout.addWidget(self._sync_tree)


class ArtellaSyncTree(QTreeWidget, object):
    def __init__(self, parent=None):
        super(ArtellaSyncTree, self).__init__(parent)

    # def _search_dirs(ref_data):
    #     if isinstance(ref_data, artellaclasses.ArtellaDirectoryMetaData):
    #         for n, d in ref_data.references.items():
    #             print(n)
    #             print(d)
    #             print(d.path)
    #             print('-----------------------------')
    #             st = artellalib.get_status(d.path)
    #             _search_dirs(st)
    #
    # assets_path = self._project.get_assets_path()
    # directories = artellalib.get_status(assets_path)
    # _search_dirs(directories)