#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base wrapper classes to create DCC windows
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpQtLib


class ArtellaWindow(tpQtLib.MainWindow, object):
    def __init__(self):
        super(ArtellaWindow, self).__init__(
            name='ArtellaPipeWindow',
            title='Artella Pipe - Window',
            size=(800, 535),
            fixed_size=False,
            auto_run=True,
            frame_less=True,
            use_style=False
        )
