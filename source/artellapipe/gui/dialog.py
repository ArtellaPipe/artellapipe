#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base wrapper classes to create DCC dialogs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


import tpQtLib

import artellapipe


class ArtellaDialog(tpQtLib.Dialog, object):
    def __init__(self, name='ArtellaDialog', title='Artella - Dialog', parent=None):

        title_pixmap = artellapipe.resource.pixmap(name='artella_title', extension='png')

        super(ArtellaDialog, self).__init__(
            name=name,
            title=title,
            parent=parent,
            has_title=True,
            title_pixmap=title_pixmap
        )
