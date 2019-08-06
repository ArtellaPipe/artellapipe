#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions for prop assets in Artella
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import artellapipe
from artellapipe.core import asset, defines


class ArtellaPropAsset(asset.ArtellaAsset, object):

    ASSET_FILES = {
        defines.ARTELLA_TEXTURES_ASSET_TYPE: artellapipe.resource.icon(defines.ARTELLA_TEXTURES_ASSET_TYPE),
        defines.ARTELLA_MODEL_ASSET_TYPE: artellapipe.resource.icon(defines.ARTELLA_MODEL_ASSET_TYPE),
        defines.ARTELLA_SHADING_ASSET_TYPE: artellapipe.resource.icon(defines.ARTELLA_SHADING_ASSET_TYPE),
        defines.ARTELLA_RIG_ASSET_TYPE: artellapipe.resource.icon(defines.ARTELLA_RIG_ASSET_TYPE)
    }

    def __init__(self, project, asset_data):
        super(ArtellaPropAsset, self).__init__(project=project, asset_data=asset_data)
