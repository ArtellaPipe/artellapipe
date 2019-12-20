#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle playblasts
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

import tpDccLib as tp
from tpPyUtils import decorators, path as path_utils

import artellapipe.register
from artellapipe.core import config

LOGGER = logging.getLogger()


class PlayblastsManager(object):
    def __init__(self):
        super(PlayblastsManager, self).__init__()

        self._project = None
        self._config = None
        self._registered_tokens = dict()

    @property
    def config(self):
        return self._config

    @property
    def tokens(self):
        return self._registered_tokens

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project
        self._config = config.get_config(project, 'artellapipe-playblasts')

    def get_presets_paths(self):
        """
        Returns paths where playblasts presets are located
        :return: str
        """

        playblasts_paths = self.config.get('presets_paths')
        return [path_utils.clean_path(
            os.path.join(self._project.get_path(), p)) for p in playblasts_paths]

    def list_tokens(self):
        """
        Returns the name of all the registered playblast tokens
        :return: list(str)
        """

        return self._registered_tokens.keys()

    def format_tokens(self, token_str, attrs_dict):
        """
        Replace the tokens with the given strings
        :param token_str: str, filename of the playbalst with tokens
        :param attrs_dict: dict, parsed capture options
        :return: str, formatted filename with all tokens resolved
        """

        if not token_str:
            return token_str

        for token, value in self._registered_tokens.items():
            if token in token_str:
                fn = value['fn']
                token_str = token_str.replace(token, fn(attrs_dict))

        return token_str

    def register_token(self, token, fn, label=''):
        """
        Registers given token
        :param token: str
        :param fn: fn
        :param label: str
        """

        assert token.startswith('<') and token.endswith('>')
        assert callable(fn)
        self._registered_tokens[token] = {'fn': fn, 'label': label}

    def get_camera_token(self, attrs_dict):
        """
        Returns short name of camera from options
        :param attrs_dict: dict, parsed capture options
        """

        camera = attrs_dict['camera']
        camera = camera.rsplit('|', 1)[-1]
        camera = camera.replace(':', '_')

        return camera

    def parse_current_scene(self):
        """
        Parse current DCC scene looking for settings related with play blasts
        :return: dict
        """

        return dict()

    def capture_context(self):
        """
        Returns context used during capture
        :return:
        """

    def capture_scene(self, options):
        """
        Capturing using scene settings
        :param options: dict, collection of output options
        :return: str, path to playblast file
        """

        filename = options.get('filename', '%TEMP%')
        LOGGER.info('Capturing to {}'.format(filename))
        options = options.copy()

        # Force viewer to False in call to capture because we have our own viewer opening call to allow a signal
        # to trigger between playblast and viewer
        options['viewer'] = False
        options.pop('panel', None)

        path = self.capture(**options)

        return path

    def capture(self, **kwargs):
        """
        Creates a playblast in an independent panel
        :param kwargs:
        """

        camera = kwargs.get('camera', 'persp')
        sound = kwargs.get('sound', None)
        width = kwargs.get('width', tp.Dcc.get_default_render_resolution_width())
        height = kwargs.get('height', tp.Dcc.get_default_render_resolution_height())
        maintain_aspect_ratio = kwargs.get('maintain_aspect_ratio', True)
        frame = kwargs.get('frame', None)
        start_frame = kwargs.get('start_frame', tp.Dcc.get_start_frame())
        end_frame = kwargs.get('end_frame', tp.Dcc.get_end_frame())
        complete_filename = kwargs.get('complete_filename', None)
        raw_frame_numbers = kwargs.get('raw_frame_numbers', False)

        camera = camera or 'persp'
        if not tp.Dcc.object_exists(camera):
            raise RuntimeError('Camera does not exists!'.format(camera))

        width = width or tp.Dcc.get_default_render_resolution_width()
        height = height or tp.Dcc.get_default_render_resolution_height()
        if maintain_aspect_ratio:
            ratio = tp.Dcc.get_default_render_resolution_aspect_ratio()
            height = round(width / ratio)

        if start_frame is None:
            start_frame = tp.Dcc.get_start_frame()
        if end_frame is None:
            end_frame = tp.Dcc.get_end_frame()

        if raw_frame_numbers and frame is None:
            frame = range(int(start_frame), int(end_frame) + 1)

        playblast_kwargs = dict()
        if complete_filename:
            playblast_kwargs['completeFilename'] = complete_filename
        if frame is not None:
            playblast_kwargs['frame'] = frame
        if sound is not None:
            playblast_kwargs['sound'] = sound

        if frame and raw_frame_numbers:
            check = frame if isinstance(frame, (list, tuple)) else [frame]
            if any(f < 0 for f in check):
                raise RuntimeError(
                    'Negative frames are not supported with raw frame numbers and explicit frame numbers')

        tp.Dcc.set_current_frame(tp.Dcc.get_current_frame())

        kwargs['camera'] = camera
        kwargs['width'] = width
        kwargs['height'] = height
        output = self._generate_playblast(**kwargs)

        return output

    def _generate_playblast(self, width, height, off_screen, **kwargs):
        """
        Internal function that calls the DCC function to generate playblast
        :return: str
        """

        raise NotImplementedError('_generate_playblast function is not implemented!')


@decorators.Singleton
class ArtellaPlayblastsManagerSingleton(PlayblastsManager, object):
    def __init__(self):
        PlayblastsManager.__init__(self)


artellapipe.register.register_class('PlayblastsMgr', ArtellaPlayblastsManagerSingleton)