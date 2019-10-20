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

from artellapipe.utils import resource
from artellapipe.gui import defines


class ArtellaDialog(tpQtLib.Dialog, object):

    LOGO_NAME = None

    def __init__(
            self,
            name='ArtellaDialog',
            title='Artella - Dialog',
            show_dragger=True, size=(200, 125),
            fixed_size=False,
            parent=None):

        title_pixmap = resource.ResourceManager().pixmap(name='artella_title', extension='png')

        super(ArtellaDialog, self).__init__(
            name=name,
            title=title,
            parent=parent,
            show_dragger=show_dragger,
            size=size,
            fixed_size=fixed_size,
            title_pixmap=title_pixmap
        )

    def _get_logo(self):
        """
        Internal function taht returns the logo used in window title
        """

        if self.LOGO_NAME:
            if self._project:
                win_logo = resource.ResourceManager().pixmap(self.LOGO_NAME, extension='png')
                if not win_logo.isNull():
                    return win_logo
                else:
                    self._project.logger.warning(
                        '{} Project Logo Image not found: {}!'.format(
                            self._project.name.title(), self.LOGO_NAME + '.png'
                        )
                    )

            win_logo = resource.ResourceManager().pixmap(self.LOGO_NAME, extension='png')
            if not win_logo.isNull():
                return win_logo

        return None

    def _get_icon(self):
        """
        Internal function that returns the icon used for the window
        :return: QIcon
        """

        if self._project:
            window_icon = self._project.icon
            if not window_icon.isNull():
                return window_icon
            else:
                self._project.logger.warning(
                    '{} Project Icon not found: {}!'.format(
                        self._project.name.title(), self._project.icon_name + '.png'))

        return resource.ResourceManager().icon(defines.ARTELLA_PROJECT_DEFAULT_ICON)

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        if self._project:
            title_pixmap = resource.ResourceManager().pixmap(
                name=defines.ARTELLA_TITLE_BACKGROUND_FILE_NAME, extension='png')
            if not title_pixmap.isNull():
                return title_pixmap
            else:
                self._project.logger.warning(
                    '{} Project Title Background image not found: {}!'.format(
                        self._project.name.title(), defines.ARTELLA_TITLE_BACKGROUND_FILE_NAME + '.png'))

        return resource.ResourceManager().pixmap(
            name=defines.ARTELLA_TITLE_BACKGROUND_FILE_NAME, extension='png')
