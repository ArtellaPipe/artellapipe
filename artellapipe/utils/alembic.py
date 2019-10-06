#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions to work with Alembics
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

from tpPyUtils import decorators

import tpDccLib as tp

from artellapipe.utils import exceptions

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import decorators as maya_decorators

    SHOW_WAIT_CURSOR_DECORATOR = maya_decorators.show_wait_cursor
else:
    SHOW_WAIT_CURSOR_DECORATOR = decorators.empty_decorator

LOGGER = logging.getLogger()


def load_alembic_plugin():
    """
    Forces the loading of the Alembic plugin if it is not already loaded
    """

    if not tp.is_maya():
        return

    if not tp.Dcc.is_plugin_loaded('AbcExport.mll'):
        tp.Dcc.load_plugin('AbcExport.mll')
    if not tp.Dcc.is_plugin_loaded('AbcImport.mll'):
        tp.Dcc.load_plugin('AbcImport.mll')


# (too-many-branches)  pylint: disable=R0912
# (too_many_arguments) pylint: disable=R0913
# (too_many_locals)    pylint: disable=R0914
def export_alembic(alembic_file,
                   euler_filter=False,
                   no_normals=False,
                   pre_roll=False,
                   renderable_only=False,
                   selection=False,
                   uv_write=False,
                   write_color_sets=False,
                   write_face_sets=False,
                   whole_frame_geo=False,
                   world_space=False,
                   write_visibility=False,
                   write_uv_sets=False,
                   write_creases=False,
                   data_format="Ogawa",
                   step=1.0,
                   mel_per_frame_callback="",
                   mel_post_job_callback="",
                   python_per_frame_callback="",
                   python_post_job_callback="",
                   user_attr=None,
                   user_attr_prefix=None,
                   attr=None,
                   attr_prefix=None,
                   root=None,
                   frame_relative_sample=None,
                   frame_range=None,
                   strip_namespaces=-1,
                   dont_skip_unwritten_frames=False,
                   verbose=False,
                   pre_roll_start_frame=0):
    """
    Exports Alembic file with given attributes

    :param str alembic_file: File location to write the Alembic data.
    :param euler_filter: Apply Euler filter while sampling rotations. Defaults to False.
    :type euler_filter: bool, optional
    :param no_normals: Present normal data for Alembic poly meshes will not be written. Defaults to False.
    :type no_normals: bool, optional
    :param pre_roll: his frame range will not be sampled. Defaults to False.
    :type pre_roll: bool, optional
    :param renderable_only: Non-renderable hierarchy (invisible, or template) will not be written out.
        Defaults to False.
    :type renderable_only: bool, optional
    :param selection: Write out all all selected nodes from the active selection list that are descendents of the roots
        specified with -root. Defaults to False.
    :type selection: bool, optional
    :param uv_write: Uv data for PolyMesh and SubD shapes will be written to the Alembic file. Only the current uv map
        is used. Defaults to False.
    :type selection: bool, optional
    :param write_color_sets: Write all color sets on MFnMeshes as color 3 or color 4 indexed geometry parameters with
        face varying scope. Defaults to False.
    :type write_color_sets: bool, optional
    :param write_face_sets: Write all Face sets on MFnMeshes. Defaults to False.
    :type write_face_sets: bool, optional
    :param whole_frame_geo: Data for geometry will only be written  out on whole frames. Defaults to
        False.
    :type whole_frame_geo: bool, optional
    :param world_space: Any root nodes will be stored in world space. Defaults to False.
    :type world_space: bool, optional
    :param write_visibility: Visibility state will be stored in the Alembic file.
        Otherwise everything written out is treated as visible. Defaults to False.
    :type write_visibility: bool, optional
    :param write_uv_sets: Write all uv sets on MFnMeshes as vector 2 indexed geometry parameters with face varying
        scope. Defaults to False.
    :type write_uv_sets: bool, optional
    :param write_creases: If the mesh has crease edges or crease vertices, the mesh (OPolyMesh) would
        now be written out as an OSubD and crease info will be stored in the Alembic file. Otherwise, creases info won't
        be preserved in Alembic file unless a custom Boolean attribute SubDivisionMesh has been added to mesh node and
        its value is true. Defaults to False.
    :type write_creases: bool, optional
    :param data_format: The data format to use to write the file. Can be either "HDF" or "Ogawa". Defaults to "Ogawa".
    :type write_creases: str, optional
    :param step:  The time interval (expressed in frames) at which the frame range is sampled.
        Additional samples around each frame can be specified with -frs. Defaults to 1.0.
    :type step: float, optional
    :param mel_per_frame_callback: When each frame (and the static frame) is evaluated the string
        specified is evaluated as a Mel command. See below for special processing rules. Defaults to "".
    :type mel_per_frame_callback: str, optional
    :param mel_post_job_callback: When the translation has finished the string specified is evaluated
        as a Mel command. See below for special processing rules. Defaults to "".
    :type mel_post_job_callback: str, optional
    :param python_per_frame_callback: When each frame (and the static frame) is evaluated the string
        specified is  evaluated as a python command. See below for special processing rules. Defaults to "".
    :type python_per_frame_callback: str, optional
    :param python_post_job_callback: When the translation has finished the string specified is evaluated
        as a python command. See below for special processing rules. Defaults to "".
    :type python_post_job_callback: str, optional
    :param user_attr: Specific user attributes to write out. Defaults to [].
    :type user_attr: list(str), optional
    :param user_attr_prefix: Prefix filter for determining which user attributes to write out. Defaults to [].
    :type user_attr_prefix: list(str), optional
    :param attr: A specific geometric attribute to write out. Defaults to [].
    :type attr: list(str), optional
    :param attr_prefix: Prefix filter for determining which geometric attributes to write out. Defaults to ["ABC_"].
    :type attr_prefix: str, optional
    :param root: Maya dag path which will be parented to the root of the Alembic file. Defaults
        to [], which means the entire scene will be written out.
    :type root: list(str), optional
    :param frame_relative_sample: Frame relative sample that will be written out along the frame range. Defaults to [].
    :type frame_relative_sample: list(float), optional
    :param frame_range: The frame range to write. Each list of two floats defines a new frame range. step or
        frameRelativeSample will affect the current frame range only.
    :type frame_range: list(list(float, float), optional
    :param strip_namespaces: Namespaces will be stripped off of the node before being written to Alembic.
        The int specifies how many namespaces will be stripped off of the node name. Be careful that the new stripped
        name does not collide with other sibling node names. Defaults to -1, which means namespaces will be preserved.
    :type strip_namespaces: int, optional
    .. tip::
        taco:foo:bar would be written as just bar with stripNamespaces=0

        taco:foo:bar would be written as foo:bar with stripNamespaces=1
    :param bool, optional dont_skip_unwritten_frames: When evaluating multiple translate jobs, this decides whether to
        evaluate frames between jobs when there is a gap in their frame ranges. Defaults to False.
    :param bool, optional verbose: Prints the current frame that is being evaluated. Defaults to False.
    :param float, optional pre_roll_start_frame: The frame to start scene evaluation at.  This is used to set the
        starting frame for time dependent translations and can be used to evaluate run-up that isn't actually
        translated. Defaults to 0.
    :return: Whether the Alembic operation was successful or not
    :rtype: bool

    .. note::
        Special callback information:
        On the callbacks, special tokens are replaced with other data, these tokens
        and what they are replaced with are as follows:
        #FRAME# replaced with the frame number being evaluated.
        #FRAME# is ignored in the post callbacks.
        #BOUNDS# replaced with a string holding bounding box values in minX minY
        minZ maxX maxY maxZ space separated order.
        #BOUNDSARRAY# replaced with the bounding box values as above, but in
        array form.
        In Mel: {minX, minY, minZ, maxX, maxY, maxZ}
        In Python: [minX, minY, minZ, maxX, maxY, maxZ]

    """

    if not tp.is_maya():
        LOGGER.warning(
            'DCC %s does not support Alembic Export functionality yet!',
            tp.Dcc.get_name())
        return False

    if user_attr is None:
        user_attr = list()
    if attr is None:
        attr = list()
    if attr_prefix is None:
        attr_prefix = list()
    if root is None:
        root = list()
    if frame_relative_sample is None:
        frame_relative_sample = list()
    if frame_range is None:
        frame_range = list()
    if user_attr_prefix is None:
        user_attr_prefix = ["ABC_"]

    # Generate job add_argument
    job_arg = ""

    # Boolean flags
    booleans = {
        "eulerFilter": euler_filter,
        "noNormals": no_normals,
        "preRoll": pre_roll,
        "renderableOnly": renderable_only,
        "selection": selection,
        "uvWrite": uv_write,
        "writeColorSets": write_color_sets,
        "writeFaceSets": write_face_sets,
        "wholeFrameGeo": whole_frame_geo,
        "worldSpace": world_space,
        "writeVisibility": write_visibility,
        "writeUVSets": write_uv_sets,
        "writeCreases": write_creases
    }
    for key, value in booleans.items():
        if value:
            job_arg += " -{0}".format(key)

    # Single argument flags
    single_arguments = {
        "dataFormat": data_format,
        "step": step,
        "melPerFrameCallback": mel_per_frame_callback,
        "melPostJobCallback": mel_post_job_callback,
        "pythonPerFrameCallback": python_per_frame_callback,
        "pythonPostJobCallback": python_post_job_callback
    }
    for key, value in single_arguments.items():
        if value:
            job_arg += " -{0} \"{1}\"".format(key, value)

    # Multiple arguments flags
    multiple_arguments = {
        "attr": attr,
        "attrPrefix": attr_prefix,
        "root": root,
        "userAttrPrefix": user_attr_prefix,
        "userAttr": user_attr,
        "frameRelativeSample": frame_relative_sample
    }
    for key, value in multiple_arguments.items():
        for item in value:
            job_arg += " -{0} \"{1}\"".format(key, item)

    # frame range flag
    for start, end in frame_range:
        job_arg += " -frameRange {0} {1}".format(start, end)

    # strip namespaces flag
    if strip_namespaces == 0:
        job_arg += " -stripNamespaces"
    if strip_namespaces > 0:
        job_arg += " -stripNamespaces {0}".format(strip_namespaces)

    # file flag
    # Alembic exporter does not like back slashes
    job_arg += " -file {0}".format(alembic_file.replace("\\", "/"))

    # Make sure Alembic plugin is loaded
    load_alembic_plugin()

    export_args = {
        "dontSkipUnwrittenFrames": dont_skip_unwritten_frames,
        "verbose": verbose,
        "preRollStartFrame": pre_roll_start_frame,
        "jobArg": job_arg
    }

    LOGGER.debug('\n> Exporting model Alembic with jog arguments:\n "%s"', export_args)
    abc_folder = os.path.dirname(alembic_file)

    if not os.path.exists(abc_folder):
        os.makedirs(abc_folder)

    try:
        maya.cmds.AbcExport(**export_args)
    except RuntimeError as exc:
        exceptions.capture_sentry_exception(exc)
        return False

    abc_exists = os.path.exists(alembic_file)
    if abc_exists:
        LOGGER.debug('Abc export completed')
    else:
        LOGGER.debug('Error while exporting Abc file')

    return abc_exists


def import_alembic(project, alembic_file, mode='import', nodes=None, parent=None, fix_path=False):
    """
    Imports Alembic into current DCC scene

    :param ArtellaProject project: Project this Alembic will belong to
    :param str alembic_file: file we want to load
    :param str mode: mode we want to use to import the Alembic File
    :param list(str) nodes: optional list of nodes to import
    :param parent:
    :param fix_path: bool, whether to fix path or not
    :return:
    """

    if not os.path.exists(alembic_file):
        LOGGER.error('Given Alembic File: {} does not exists!'.format(alembic_file))
        tp.Dcc.confirm_dialog(
            title='Error',
            message='Alembic File does not exists:\n{}'.format(alembic_file)
        )
        return None

    # Make sure Alembic plugin is loaded
    load_alembic_plugin()

    LOGGER.debug(
        'Import Alembic File (%s) with job arguments:\n\t(alembic_file) %s\n\t(nodes) %s', mode, alembic_file, nodes)

    res = None
    try:
        if fix_path:
            abc_file = project.fix_path(alembic_file)
        else:
            abc_file = alembic_file

        if tp.is_maya():
            if nodes:
                res = maya.cmds.AbcImport(abc_file, ct=' '.join(nodes))
            elif parent:
                res = maya.cmds.AbcImport(abc_file, mode=mode, rpr=parent)
            else:
                res = maya.cmds.AbcImport(abc_file, mode=mode)
        elif tp.is_houdini():
            if not parent:
                LOGGER.warning('Impossible to import Alembic File because not Alembic parent given!')
                return False
            parent.parm('fileName').set(abc_file)
            build_hierarch_param = parent.parm('buildHierarchy')
            if build_hierarch_param:
                build_hierarch_param.pressButton()
    except RuntimeError as exc:
        exceptions.capture_sentry_exception(exc)
        return res

    LOGGER.debug('Alembic File %s imported successfully!', os.path.basename(alembic_file))
    return res


def reference_alembic(project, alembic_file, namespace=None, fix_path=False):
    """
    References given alembic file in current DCC scene

    :param artellapipe.core.ArtellaProject project: Project this Alembic belongs to
    :param str alembic_file:
    :param str, optional namespace:
    :param bool, optional fix_path:
    :return:
    """

    if not tp.is_maya():
        LOGGER.warning(
            'DCC %s does not support Alembic Reference '
            'functionality yet!', tp.Dcc.get_name())
        return None

    # Make sure Alembic plugin is loaded
    load_alembic_plugin()

    if not os.path.exists(alembic_file):
        tp.Dcc.confirm_dialog(
            title='Error',
            message='Alembic File does not exists:\n{}'.format(alembic_file)
        )
        return None

    new_nodes = None
    try:
        if fix_path:
            abc_file = project.fix_path(alembic_file)
        else:
            abc_file = alembic_file

        if namespace:
            new_nodes = maya.cmds.file(abc_file, type='Alembic', reference=True, returnNewNodes=True)
        else:
            new_nodes = maya.cmds.file(abc_file, type='Alembic', reference=True, returnNewNodes=True)

    except RuntimeError as exc:
        exceptions.capture_exception(exc)
        return new_nodes

    LOGGER.debug('Alembic File %s referenced successfully!', os.path.basename(alembic_file))

    return new_nodes
