#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow artists to interact with Artella functionality inside DCCS
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"


from artellapipe.gui import window
from artellapipe.tools.artellamanager.widgets import user


class ArtellaManager(window.ArtellaWindow, object):
    def __init__(self):
        super(ArtellaManager, self).__init__(
            name='ArtellaManagerWindow',
            title='Artella Manager',
            size=(1100, 900)
        )

    def ui(self):
        super(ArtellaManager, self).ui()

        self._user_icon = user.ArtellaUserInfoWidget()
        self._user_icon.move(1030, 5)
        self._logo_scene.addWidget(self._user_icon)




def run():
    win = ArtellaManager()
    win.show()

    return win
