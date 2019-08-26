#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants for Artella ShotExporter Tool
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


MUST_ATTRS = [
    'worldMatrix',
    'translateX', 'translateY', 'translateZ',
    'rotateX', 'rotateY', 'rotateZ',
    'scaleX', 'scaleY', 'scaleZ']

ABC_ATTRS = [
    'speed', 'offset', 'abc_file', 'time', 'startFrame', 'endFrame', 'cycleType'
]

DEFAULT_EXPORT_LIST_PADDING = 5
DEFAULT_EXPORT_LIST_ZOOM_AMOUNT = 90
DEFAULT_EXPORT_LIST_HEIGHT = 20
DEFAULT_EXPORT_LIST_WHEEL_SCROLL_STEP = 2
DEFAULT_EXPORT_LIST_MIN_SPACING = 0
DEFAULT_EXPORT_LIST_MAX_SPACING = 50
DEFAULT_EXPORT_LIST_MIN_LIST_SIZE = 15
DEFAULT_EXPORT_LIST_MIN_ICON_SIZE = 50
