#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions for asset in Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpPyUtils import strings

from tpQtLib.core import base, image

import artellapipe
from artellapipe.core import abstract, defines


class ArtellaAsset(abstract.AbstractAsset, object):

    def __init__(self, asset_data):

        self._thumbnail_icon = None
        self._category = None

        super(ArtellaAsset, self).__init__(asset_data)

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the asset
        :return: str
        """

        return self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_NAME_ATTR, defines.ARTELLA_DEFAULT_ASSET_NAME)

    def get_path(self):
        """
        Implements abstract get_path function
        Returns the path of the asset
        :return: str
        """

        return self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_PATH_ATTR, '')

    def get_thumbnail_icon(self):
        """
        Implements abstract get_thumbnail_icon function
        Returns the icon of the asset
        :return: QIcon
        """

        # If the icon is already cached we return it
        if self._thumbnail_icon:
            return self._thumbnail_icon

        str_icon = self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_ICON_ATTR, None)
        icon_format = self._asset_data[defines.ARTELLA_ASSET_DATA_ATTR].get(defines.ARTELLA_ASSET_DATA_ICON_FORMAT_ATTR, None)
        if not str_icon or not icon_format:
            return self.DEFAULT_iCON

        self._thumbnail_icon = QPixmap.fromImage(image.base64_to_image(str_icon.encode('utf-8'), image_format=icon_format))
        if not self._thumbnail_icon:
            self._thumbnail_icon = self.DEFAULT_iCON

        return self._thumbnail_icon

    def get_category(self):
        """
        Implements abstract get_thumbnail_icon function
        Returns the category of the asset
        :return: str
        """

        if self._category:
            return self._category

        asset_path = self.get_path()
        if not asset_path:
            return ''

        self._category = strings.camel_case_to_string(os.path.basename(os.path.dirname(asset_path)))

        return self._category


class ArtellaAssetWidget(base.BaseWidget, object):

    DEFAULT_ICON = artellapipe.resource.icon('default')

    clicked = Signal(object)

    def __init__(self, asset, parent=None):

        self._asset = asset

        super(ArtellaAssetWidget, self).__init__(parent=parent)

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(ArtellaAssetWidget, self).ui()

        self.setFixedWidth(160)
        self.setFixedHeight(160)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(2, 2, 2, 2)
        widget_layout.setSpacing(0)
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        self._asset_btn = QPushButton('', self)
        self._asset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._asset_btn.setIconSize(QSize(150, 150))
        self._asset_lbl = QLabel(self.get_name())
        self._asset_lbl.setAlignment(Qt.AlignCenter)

        widget_layout.addWidget(self._asset_btn)
        widget_layout.addWidget(self._asset_lbl)

    def setup_signals(self):
        self._asset_btn.clicked.connect(partial(self.clicked.emit, self))

    def get_name(self):
        """
        Returns name of the asset
        :return: str
        """

        return self._asset.get_name()

    def get_default_thumbnail_icon(self):
        """
        Returns the default thumbnail icon
        :return: QIcon
        """

        return self.DEFAULT_ICON

    def get_thumbnail_icon(self):
        """
        Returns thumbnail icon of the item
        """

        return self._asset.get_thumbnail_icon()

    def get_category(self):
        """
        Returns the category of the asset
        :return: str
        """

        return self._asset.get_category()

    def _init(self):
        """
        Internal function that initializes asset widget
        Can be extended to add custom initialization functionality to asset widgets
        """

        thumb_icon = self.get_thumbnail_icon()
        if thumb_icon:
            self._asset_btn.setIcon(thumb_icon)
