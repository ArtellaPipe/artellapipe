#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for the items used by Artella Syncer Tree
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *


class DirectoryItem(QTreeWidgetItem, object):
    def __init__(self, parent=None):
        super(DirectoryItem, self).__init__(parent)