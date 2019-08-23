#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base definition for property list widgets
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *
from Qt.QtCore import *

import tpDccLib as tp

from artellapipe.tools.shotexporter.core import defines


class ExporterAssetItem(object):

    clicked = Signal(QObject, QEvent)
    contextRequested = Signal(QObject, QAction)

    def __init__(self, asset):
        super(ExporterAssetItem, self).__init__()

        self._asset = asset
        self._attrs = dict()

        self._update_attrs()

    @property
    def name(self):
        return self._asset.name

    @property
    def short_name(self):
        return self._asset.get_short_name()

    @property
    def path(self):
        return self._asset.asset_path

    @property
    def attrs(self):
        return self._attrs

    def _update_attrs(self):
        """
        Internal function that updates the attributes of the item
        """

        if self._attrs:
            return

        xform_attrs = tp.Dcc.list_attributes(self._asset.name)
        for attr in xform_attrs:
            if attr in defines.MUST_ATTRS:
                self._attrs[attr] = True
            else:
                self._attrs[attr] = False
