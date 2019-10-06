#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that handles mock imports for unit artellapipe-utils unit tests
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


import sys

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

sys.modules['sentry_sdk'] = MagicMock()
sys.modules['pythonjsonlogger'] = MagicMock()


def prepare_modules():
    """
    Prepares modules imports
    """

    sys.modules['tpDccLib'] = MagicMock()
    sys.modules['tpMayaLib'] = MagicMock()
    sys.modules['tpMayaLib.core'] = MagicMock()
    sys.modules['maya'] = MagicMock()
    sys.modules['maya.cmds'] = MagicMock()


def clean_modules():
    """
    Clean modules imports
    """

    del sys.modules['tpDccLib']
    del sys.modules['tpMayaLib']
    del sys.modules['tpMayaLib.core']
    del sys.modules['maya']
    del sys.modules['maya.cmds']
