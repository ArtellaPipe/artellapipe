#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class that defines Artella Shot
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

import tpDcc as tp
from tpDcc.libs.python import folder

import artellapipe
from artellapipe.core import abstract

LOGGER = logging.getLogger('artellapipe')


class ArtellaShot(abstract.AbstractShot, object):

    def __init_(self, project, shot_data):
        super(ArtellaShot, self).__init__(project=project, shot_data=shot_data)

        self._data = None

    def get_id(self):
        """
        Implements abstract get_id function
        Returns the id of the shot
        :return: str
        """

        id_attr = artellapipe.ShotsMgr().config.get('data', 'id_attribute')
        asset_id = self._shot_data.get(id_attr, None)
        if not asset_id:
            LOGGER.warning(
                'Impossible to retrieve asset ID because asset data does not contains "{}" attribute.'
                '\nAsset Data: {}'.format(id_attr, self._shot_data))
            return None

        return asset_id.rstrip()

    def get_name(self):
        """
        Implements abstract get_name function
        Returns the name of the sequence
        :return: str
        """

        name_attr = artellapipe.ShotsMgr().config.get('data', 'name_attribute')
        shot_name = self._shot_data.get(name_attr, None)
        if not shot_name:
            LOGGER.warning(
                'Impossible to retrieve shot name because shot data does not contains "{}" attribute.'
                '\nSequence Data: {}'.format(name_attr, self._shot_data))
            return None

        return shot_name.rstrip()

    def get_thumbnail_path(self):
        """
        Implements abstract get_path function
        Returns the path where shot thumbnail is located
        :return: str
        """

        thumb_attr = artellapipe.ShotsMgr().config.get('data', 'thumb_attribute')
        thumb_path = self._shot_data.get(thumb_attr, None)

        return thumb_path

    def get_node(self):
        """
        Returns DCC node attached to this shot
        :return: str
        """

        node_name = self.get_name()
        if not node_name:
            return None

        if not tp.Dcc.object_exists(node_name):
            return None

        if tp.is_maya() and not tp.Dcc.node_type(node_name) == 'shot':
            return None

        return node_name

    def get_sequence(self):
        """
        Returns the name of the sequence this shot belongs to
        :return: str
        """

        sequence_attr = artellapipe.ShotsMgr().config.get('data', 'sequence_attribute')
        sequence_name = self._shot_data.get(sequence_attr, None)
        if not sequence_name:
            LOGGER.warning(
                'Impossible to retrieve sequence name because shot data does not contains "{}" attribute.'
                '\nSequence Data: {}'.format(sequence_attr, self._shot_data))
            return None

        return sequence_name

    def get_number(self):
        """
        Returns the number of the shot
        :return: str
        """

        name_attr = artellapipe.ShotsMgr().config.get('data', 'number_attribute')
        shot_number = self._shot_data.get(name_attr, None)
        if not shot_number:
            LOGGER.warning(
                'Impossible to retrieve shot number because shot data does not contains "{}" attribute.'
                '\nSequence Data: {}'.format(name_attr, self._shot_data))
            return None

        return shot_number.rstrip()

    def is_muted(self):
        """
        Returns whether this shot is muted in current scene or not
        :return: bool
        """

        shot_node = self.get_node()
        if not shot_node:
            return True

        return tp.Dcc.shot_is_muted(shot_node)

    def get_track_number(self):
        """
        Return tracker this shot is located into
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_track_number(shot_node)

    def get_sequencer_start_frame(self):
        """
        Returns start frame of the shot in sequencer time
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_start_frame_in_sequencer(shot_node)

    def get_sequencer_end_frame(self):
        """
        Returns end frame of the shot in sequencer time
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_end_frame_in_sequencer(shot_node)

    def get_pre_hold(self):
        """
        Returns shot prehold value
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_pre_hold(shot_node)

    def get_post_hold(self):
        """
        Returns shot posthold value
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_post_hold(shot_node)

    def get_scale(self):
        """
        Returns shot scale
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_scale(shot_node)

    def get_start_frame(self):
        """
        Returns shot start frame
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_start_frame(shot_node)

    def get_end_frame(self):
        """
        Returns shot end frame
        :return: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return -1

        return tp.Dcc.shot_end_frame(shot_node)

    def set_start_frame(self, start_frame):
        """
        Sets the start frame of the shot
        :param start_frame: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return

        return tp.Dcc.set_shot_start_frame(shot_node, start_frame)

    def set_end_frame(self, end_frame):
        """
        Sets the end frame of the shot
        :param end_frame: int
        """

        shot_node = self.get_node()
        if not shot_node:
            return

        return tp.Dcc.set_shot_end_frame(shot_node, end_frame)

    def get_camera(self):
        """
        Returns camera associated to this shot
        :return: str or None
        """

        shot_node = self.get_node()
        if not shot_node:
            return None

        return tp.Dcc.shot_camera(shot_node)

    def get_range_frames_in_sequence(self, sequence_range):
        """
        Returns list of frames this shot belongs to in sequence
        :param sequence_range: list(int, int), start and enf frame of shot in sequencer timeline
        :return: list(int)
        """

        shot_data = self.get_data(sequence_range=sequence_range)
        start_frame = shot_data['sequence_start_frame']
        end_frame = shot_data['sequence_end_frame']

        return range(start_frame, end_frame + 1)

    def get_range_frames_in_time(self, sequence_range):
        """
        Returns list of frames this shot belongs to in time
        :param sequence_range: list(int, int), start and enf frame of shot in sequencer timeline
        :return: list(int)
        """

        shot_data = self.get_data(sequence_raRnge=sequence_range)
        start_frame = shot_data['time_start_frame']
        end_frame = shot_data['time_end_frame']

        return range(start_frame, end_frame + 1)

    def get_max_sequencer(self):
        """
        Returns maximum frame in sequencer of shot taking into account all non muted shots
        :return: int
        """

        non_muted_shots = artellapipe.ShotsMgr().find_non_muted_shots()
        if not non_muted_shots:
            return 0.0

        greatest_time = max([shot.get_sequencer_end_frame() for shot in non_muted_shots])

        return greatest_time

    def get_min_sequencer(self):
        """
        Returns minimum frame in sequencer of shot taking into account all non muted shots
        :return: int
        """

        non_muted_shots = artellapipe.ShotsMgr().find_non_muted_shots()
        if not non_muted_shots:
            return 0.0

        greatest_time = min([shot.get_sequencer_start_frame() for shot in non_muted_shots])

        return greatest_time

    def get_max_time(self):
        """
        Returns maximum frame in timeline of shot taking into account all non muted shots
        :return: int
        """

        non_muted_shots = artellapipe.ShotsMgr().find_non_muted_shots()
        if not non_muted_shots:
            return 0.0

        greatest_time = max([shot.get_end_frame() for shot in non_muted_shots])

        return greatest_time

    def get_min_time(self):
        """
        Returns minimum frame in timeline of shot taking into account all non muted shots
        :return: int
        """

        non_muted_shots = artellapipe.ShotsMgr().find_non_muted_shots()
        if not non_muted_shots:
            return 0.0

        least_time = min([shot.get_start_frame() for shot in non_muted_shots])

        return least_time

    def get_data(self, sequence_range, start_duplicate_index=None, force_update=False):
        """
        Returns data of current node
        :param sequence_range: list(int, int), start and enf frame of shot in sequencer timeline
            when shot range is different than shot's sequence range.
            When the shot has one or more shots overlapping, it causes section of the shot to be played multiple times
        :param start_duplicate_index: int, pass if we want to duplicate camera
        :param force_update: bool
        :return: dict
        """

        if self._data and not force_update:
            return self._data

        sequence_start_frame = sequence_range[0]
        sequence_end_frame = sequence_range[-1]
        shot_sequencer_start_frame = self.get_sequencer_start_frame()
        shot_sequencer_end_frame = self.get_sequencer_end_frame()
        shot_pre_hold = self.get_pre_hold()
        shot_post_hold = self.get_post_hold()
        shot_scale = self.get_scale()
        shot_start_frame = self.get_start_frame()
        shot_end_frame = self.get_end_frame()

        pre_hold = 0.0
        pre_hold_in = None
        if sequence_start_frame < shot_sequencer_start_frame + shot_pre_hold:
            pre_hold = shot_sequencer_start_frame + shot_pre_hold - sequence_start_frame
        elif sequence_start_frame > shot_sequencer_start_frame + shot_pre_hold:
            pre_hold_in = sequence_start_frame - (shot_sequencer_start_frame + shot_pre_hold)

        post_hold = 0.0
        post_hold_in = None
        if sequence_end_frame > shot_sequencer_end_frame - shot_post_hold:
            post_hold = sequence_end_frame - (shot_sequencer_end_frame - shot_post_hold)
        elif sequence_end_frame < shot_sequencer_end_frame - shot_post_hold:
            post_hold_in = shot_sequencer_end_frame - shot_post_hold - sequence_end_frame

        time_start_frame = shot_start_frame
        if pre_hold_in is not None:
            time_start_frame = pre_hold_in / shot_scale + shot_start_frame

        time_end_frame = shot_end_frame
        if post_hold_in is not None:
            time_end_frame = (sequence_end_frame - shot_sequencer_start_frame) / shot_scale + shot_start_frame

        shot_node_name = self.get_name()
        if start_duplicate_index is not None:
            shot_node_name = artellapipe.ShotsMgr().get_shot_unique_name(self.get_name(), start=start_duplicate_index)

        shot_camera = self.get_camera()
        shot_track = self.get_track_number()

        shot_dict = {
            'shot_name': shot_node_name,
            'track': shot_track,
            'camera': shot_camera,
            'sequence_start_frame': sequence_start_frame,
            'sequence_end_frame': sequence_end_frame,
            'prehold': pre_hold,
            'posthold': post_hold,
            'shot_scale': shot_scale,
            'time_start_frame': time_start_frame,
            'time_end_frame': time_end_frame
        }

        return shot_dict

    def export_animation(self, export_path):
        """
        Exports all the animation of the current shot into
        :return:
        """

        if not tp.is_maya():
            LOGGER.warning('Shot Animation Export is only supported in Maya!')
            return

        from artellapipe.dccs.maya.core import sequencer

        all_anim_curves = tp.Dcc.all_animation_curves()
        if not all_anim_curves:
            LOGGER.warning(
                'Impossible teo export shot animation because no animation curves were found in current scene!')
            return False

        export_name = os.path.basename(export_path)
        export_dir = os.path.dirname(export_path)
        if not os.path.isdir(export_dir):
            folder.create_folder(export_name, export_dir)

        start_frame = self.get_start_frame()
        end_frame = self.get_end_frame()
        max_time = self.get_max_time()
        min_time = self.get_min_time()

        post_hold = self.get_post_hold()
        if post_hold > 0.0:
            raise NotImplementedError('post_hold greater than 0.0 is not supported yet')

        valid_export = sequencer.SequencerShotExporter(anim_curves=all_anim_curves).export_shot_animation_curves(
            export_file_path=export_path, start_frame=start_frame, end_frame=end_frame,
            sequencer_least_key=min_time, sequencer_great_key=max_time)

        return valid_export

    def import_animation(self, import_path, start_frame=101):
        """
        Imports all the animation of the current shot
        :param import_path: str
        :param start_frame: int
        :return:
        """

        if not tp.is_maya():
            LOGGER.warning('Shot Animation Import is only supported in Maya!')
            return

        from artellapipe.dccs.maya.core import sequencer

        all_anim_curves = tp.Dcc.all_animation_curves()

        start_offset = self.get_start_frame() - start_frame
        start_frame = self.get_start_frame() - start_offset
        end_frame = self.get_end_frame() - start_offset
        sequence_start_frame = self.get_sequencer_start_frame()
        sequence_end_frame = self.get_sequencer_end_frame()

        pre_hold = self.get_pre_hold()
        post_hold = self.get_post_hold()
        if pre_hold > 0.0:
            raise NotImplementedError('pre_hold greater than 0.0 is not supported yet')
        if post_hold > 0.0:
            raise NotImplementedError('post_hold greater than 0.0 is not supported yet')

        LOGGER.info(
            'Importing animation on frame range ({} - {}) from file "{}"'.format(
                start_frame, end_frame, os.path.basename(import_path)))

        valid_import = sequencer.SequencerShotExporter(anim_curves=all_anim_curves).import_shot_animation_curves(
            import_file_path=import_path, start_frame=start_frame, end_frame=end_frame,
            sequence_start_frame=sequence_start_frame, sequence_end_frame=sequence_end_frame)

        return valid_import

    def get_assets_from_breakdown(self):
        """
        Returns all the assets contained in shot breakdown defined in production tracker
        :return: list(ArtellaAsset)
        """

        shot_id = self.get_id()
        return artellapipe.AssetsMgr().get_assets_in_shot(shot_id)
