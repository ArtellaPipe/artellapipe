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
import logging

import tpDcc

import artellapipe
from artellapipe.core import abstract, defines

LOGGER = logging.getLogger('artellapipe')


class ArtellaAsset(abstract.AbstractAsset, object):

    def __init__(self, project, asset_data, node=None):

        self._artella_data = None

        super(ArtellaAsset, self).__init__(project=project, asset_data=asset_data, node=node)

    def get_id(self):
        """
        Implements abstract get_id function
        Returns the id of the asset
        :return: str
        """

        id_attr = artellapipe.AssetsMgr().config.get('data', 'id_attribute')
        asset_id = self._asset_data.get(id_attr, None)
        if not asset_id:
            LOGGER.warning(
                'Impossible to retrieve asset ID because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(id_attr, self._asset_data))
            return None

        return asset_id.rstrip()

    def set_id(self, new_id):
        """
        Sets the ID of this asset
        :param new_id: str
        """

        id_attr = artellapipe.AssetsMgr().config.get('data', 'id_attribute')
        asset_id = self._asset_data.get(id_attr, None)
        if not asset_id:
            LOGGER.warning(
                'Impossible to retrieve asset ID because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(id_attr, self._asset_data))
            return None

        self._asset_data[id_attr] = new_id

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the asset
        :return: str
        """

        name_attr = artellapipe.AssetsMgr().config.get('data', 'name_attribute')
        asset_name = self._asset_data.get(name_attr, None)
        if not asset_name:
            LOGGER.warning(
                'Impossible to retrieve asset name because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(name_attr, self._asset_data))
            return None

        return asset_name.rstrip()

    def get_tags(self):
        """
        Returns tags of the asset
        Implements abstract get_tags function
        :return: list(str)
        """

        tags_attr = artellapipe.AssetsMgr().config.get('data', 'tag_attribute')
        tags_list = self._asset_data.get(tags_attr, None)
        if not tags_list:
            LOGGER.warning(
                'Impossible to retrieve tags name because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(tags_attr, self._asset_data))
            return None

        return tags_list

    def get_path(self):
        """
        Implements abstract get_path function
        Returns the path of the asset
        :return: str
        """

        path_template_name = artellapipe.AssetsMgr().config.get('data', 'path_template_name')
        template = artellapipe.FilesMgr().get_template(path_template_name)
        if not template:
            LOGGER.warning(
                'Impossible to retrieve asset path because template "{}" is not in configuration file'.format(
                    path_template_name))
            return None

        template_dict = {
            'project_id': self._project.id,
            'project_id_number': self._project.id_number,
            'asset_type': self.get_category(),
            'asset_name': self.get_name()
        }
        asset_path = template.format(template_dict)

        if not asset_path:
            LOGGER.warning(
                'Impossible to retrieve asset path from template: "{} | {} | {}"'.format(
                    template.name, template.pattern, template_dict))
            return None

        asset_path = os.path.expandvars(asset_path)
        asset_path = artellapipe.FilesMgr().prefix_path_with_project_path(asset_path)

        return asset_path

    def get_thumbnail_path(self):
        """
        Implements abstract get_path function
        Returns the path where asset thumbnail is located
        :return: str
        """

        thumb_attr = artellapipe.AssetsMgr().config.get('data', 'thumb_attribute')
        thumb_path = self._asset_data.get(thumb_attr, None)

        return thumb_path

    def get_category(self):
        """
        Implements abstract get_category function
        Returns the category of the asset
        :return: str
        """

        category_attr = artellapipe.AssetsMgr().config.get('data', 'category_attribute')

        category = self._asset_data.get(category_attr, None)
        if not category:
            LOGGER.warning(
                'Impossible to retrieve asset category because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(category_attr, self._asset_data))

        return category

    def get_icon(self):
        """
        Returns the icon of the asset depending of the category
        :return: QIcon
        """

        return tpDcc.ResourcesMgr().icon(self.get_category().lower().replace(' ', '_'))

    # ==========================================================================================================
    # SHADERS
    # ==========================================================================================================

    def get_shaders_path(self, status=defines.ArtellaFileStatus.WORKING, next_version=False):
        """
        Returns path where asset shaders are stored
        :return: str
        """

        shaders_path_file_type = artellapipe.ShadersMgr().get_shaders_path_file_type()
        if not shaders_path_file_type:
            LOGGER.warning('No Asset Shaders Path file type available!')
            return None

        shader_file_path_template = artellapipe.FilesMgr().get_template('shaders')
        if not shader_file_path_template:
            LOGGER.warning('No shaders path template found!')
            return None

        template_dict = {
            'project_id': self._project.id,
            'project_id_number': self._project.id_number,
            'asset_type': self.get_category(),
            'asset_name': self.get_name()
        }

        asset_shaders_path = self.solve_path(
            file_type=shaders_path_file_type, template=shader_file_path_template, template_dict=template_dict,
            status=status, check_file_type=False)

        return asset_shaders_path

    # ==========================================================================================================
    # PRIVATE
    # ==========================================================================================================

    def _get_file_name(self, asset_name, **kwargs):
        """
        Returns asset file name without extension
        :param asset_name: str
        :param kwargs: dict
        :return: str
        """

        return self._project.solve_name('asset_file', asset_name, **kwargs)
