#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to Media related operations
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import tempfile
import mimetypes

import tpDcc
from tpDcc.libs.python import yamlio, path as path_utils

import artellapipe

LOGGER = logging.getLogger('artellapipe')


class MediaManager(object):

    TEMP_PREFIX = 'artella_mediamgr'
    TEMP_SUFFIX = 'tmp'

    _config = None

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tpDcc.ConfigsMgr().get_config(
                config_name='artellapipe-media',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    def get_media_profiles_paths(self):
        """
        Returns all used to search media profiles in
        :return: list(str)
        """

        paths_found = list()
        media_profile_paths = self.config.get('media_profiles_paths', default=list())
        for media_profile_path in media_profile_paths:
            if os.path.isdir(media_profile_path):
                if media_profile_path not in paths_found:
                    paths_found.append(media_profile_path)
            else:
                project_path = path_utils.clean_path(os.path.join(artellapipe.project.get_path(), media_profile_path))
                if os.path.isdir(project_path) and project_path not in paths_found:
                    paths_found.append(project_path)

        return paths_found

    def get_media_profiles_extensions(self):
        """
        Returns list of extensions used to define media profiles
        :return: list(str)
        """

        return self.config.get('media_profiles_extensions', default=['.yml'])

    def get_media_profiles_file_paths(self):
        """
        Returns paths to all media profiles stored in media profiles paths
        :return: list(str)
        """

        media_paths = self.get_media_profiles_paths()
        if not media_paths:
            LOGGER.warning('No media profiles paths found!')
            return list()

        supported_extensions = self.get_media_profiles_extensions()

        paths_found = list()
        for media_path in media_paths:
            for root, _, files in os.walk(media_path):
                for file_name in files:
                    file_ext = os.path.splitext(file_name)[-1].lower()
                    if file_ext in supported_extensions:
                        media_profile_path = path_utils.clean_path(os.path.join(root, file_name))
                        if media_profile_path not in paths_found:
                            paths_found.append(media_profile_path)

        return paths_found

    def get_media_profile_path(self, media_profile_name):
        """
        Returns path to given media profile name
        :param media_profile_name: str
        :return: str
        """

        media_profile_paths = self.get_media_profiles_file_paths()
        if not media_profile_paths:
            return None

        for media_profile_path in media_profile_paths:
            profile_name = os.path.basename(media_profile_path)
            if profile_name == media_profile_name:
                return media_profile_path
            profile_name = os.path.splitext(profile_name)[0]
            if profile_name == media_profile_name:
                return media_profile_path

        return None

    def get_media_profile_data(self, media_profile_name):
        """
        Returns data stored in given media profile name if exists
        :param media_profile_name: str
        :return: dict
        """

        media_profile_path = self.get_media_profile_path(media_profile_name)
        if not media_profile_path or not os.path.isfile(media_profile_path):
            return dict()

        config_data = yamlio.read_file(media_profile_path)

        # We try to update config files with proper reosurce paths
        profile_resource_folders = config_data.get('resources_folders', list())
        if profile_resource_folders:
            for profile_resource_folder in profile_resource_folders:
                for key, value in config_data.items():
                    try:
                        if value and os.path.isfile(value):
                            continue
                        resource_path = tpDcc.ResourcesMgr().get(profile_resource_folder, value, key='project')
                    except Exception:
                        continue
                    if resource_path and os.path.isfile(resource_path):
                        config_data[key] = resource_path
                        continue

        return config_data

    def create_temp_path(self, prefix=None, suffix=None):
        """
        Creates temporary folder used during media operations to store temporal files
        :param prefix: str
        :param suffix: str
        :return: str
        """

        if not prefix:
            prefix = self.TEMP_PREFIX
        if not suffix:
            suffix = self.TEMP_SUFFIX
        prefix = prefix.strip()
        suffix = suffix.strip()
        if not prefix.endswith('_'):
            prefix = '{}_'.format(prefix)
        if not suffix.startswith('_'):
            suffix = '_{}'.format(suffix)

        project_temp_folder = artellapipe.project.get_temporary_folder()
        try:
            temp_path = tempfile.mkdtemp(suffix, prefix, project_temp_folder)
        except Exception:
            temp_path = tempfile.mkdtemp(suffix, prefix, tempfile.gettempdir())

        return temp_path

    def stamp(self, source, output, config_dict=None, extra_dict=None):
        if not source or not os.path.isfile(source):
            return LOGGER.error('Impossible to stamp. Source file is not valid: {}'.format(source))
            return False

        if extra_dict is None:
            extra_dict = dict()

        if not config_dict:
            default_profile = self.config.get('default_profile', default=None)
            if default_profile:
                config_dict = self.get_media_profile_data(default_profile)
        if config_dict is None:
            config_dict = dict()

        extra_dict.update(config_dict)

        mime_start = mimetypes.guess_type(source)[0]
        if not mime_start:
            LOGGER.warning(
                'Impossible to create stamp because input file name extension is not recognized: {}!'.format(source))
            return False

        mime_start = mime_start.split('/')[0]

        if mime_start == 'video':
            return self.stamp_video(source=source, output=output, config_dict=extra_dict)
        elif mime_start == 'image':
            return self.stamp_image(source=source, output=output, config_dict=extra_dict)
        else:
            LOGGER.error('Impossible to stamp file: "{}"({})'.format(source, mime_start))
            return False

    def stamp_video(self, source, output, config_dict=None):
        pass
        # source_pixmap = QPixmap(source)
        # frame = artellapipe.Frame(source)
        # res_x = int(source_pixmap.size().width())
        # res_y = int(source_pixmap.size().height())
        #
        # if not config_dict:
        #     default_profile = self.config.get('default_profile', default=None)
        #     if default_profile:
        #         config_dict = self.get_media_profile_data(default_profile)
        #
        # frame.stamp_frame(output=output, resolution_x=res_x, resolution_y=res_y, config_dict=config_dict)

    def stamp_image(self, source, output, config_dict=None):
        pass
