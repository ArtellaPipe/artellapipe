#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions to work with Shaders
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import json
import logging.config

from tpPyUtils import decorators, path as path_utils

import tpDccLib as tp

from tpQtLib.core import image

from artellapipe.utils import tag as taggerutils

IGNORED_SHADERS = list()
IGNORE_ATTRS = list()
if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import shader as maya_shaders
    from tpMayaLib.core import transform as maya_transform
    from tpMayaLib.core import decorators as maya_decorators

    UNDO_DECORATOR = maya_decorators.undo_chunk
    IGNORE_SHADERS = ['particleCloud1', 'shaderGlow1', 'defaultColorMgtGlobals', 'lambert1']
    IGNORE_ATTRS = ['computedFileTextureNamePattern']
else:
    UNDO_DECORATOR = decorators.empty_decorator

LOGGER = logging.getLogger()


class ShadingNetwork(object):
    """
    Class that defines a shading network
    """

    def __init__(self, shader_extension):
        super(ShadingNetwork, self).__init__()

        shader_extension = str(shader_extension)
        if not shader_extension.startswith('.'):
            shader_extension = '.{}'.format(shader_extension)

        self._shader_extension = shader_extension

    @staticmethod
    def write(shader_dict, file_dir):
        """
        Writes given shader dict to the given JSON file
        :param shader_dict: dict
        :param file_dir: str
        """

        with open(file_dir, 'w') as open_file:
            json.dump(shader_dict, open_file, indent=4, sort_keys=True)

    @staticmethod
    def read(file_dir):
        """
        Reads shader info from given JSON file
        :param file_dir: str
        :return: dict
        """

        with open(file_dir, 'r') as open_file:
            shader_dict = json.load(open_file)
        return shader_dict

    # (too_many_arguments) pylint: disable=R0913
    @classmethod
    def write_network(cls, shader_extension, shaders_path, shaders=None,
                      icon_path=None, publish=False):
        """
        Writes shader network info to the given path
        :param shaders_path: str, path where we want to store the shader
        :param shaders: list<str>, list of shaders we want to store
        :param icon_path: str, icon we want to show in the shader viewer
        :return: list<str>, list of exported shaders
        """
        if not os.path.exists(shaders_path):
            LOGGER.debug('ShaderLibrary: Shaders Path %s is not valid! Aborting export!', shaders_path)

        if shaders is None:
            shaders = maya.cmds.ls(materials=True)

        exported_shaders = list()
        for shader in shaders:
            if shader not in IGNORE_SHADERS:
                # Get dict with all the info of the shader
                shader_network = cls.get_shading_network(shader)

                # Store shader icon in base64 format
                shader_network['icon'] = image.image_to_base64(icon_path)

                # Export the shader in the given path and with the proper format
                out_file = os.path.join(shaders_path, shader + shader_extension)
                LOGGER.debug('Generating Shader %s in %s', (shader, out_file))

                # if os.path.isfile(out_file):
                #     temp_file, temp_filename = tempfile.mkstemp()
                #     cls.write(shader_network, temp_filename)
                #     if filecmp.cmp(out_file, temp_filename):
                #         logger.debug(
                #         'Shader file already exists and have same size. No new shader file will be generated!')
                #         result = qtutils.show_question(None, 'New Shader File Version',
                #         'Shader File {} already exists with same file size!
                #         Do you want to upload it to Artella anyways?'.format(shader))
                #         if result == QMessageBox.No:
                #             upload_new_version = False
                #     else:
                #         logger.debug('Writing shader file: {}'.format(out_file))
                #         cls.write(shader_network, out_file)
                # else:
                artellalib.lock_file(out_file, force=True)
                LOGGER.debug('Writing shader file: {}'.format(out_file))
                cls.write(shader_network, out_file)

                if publish:
                    LOGGER.debug('Creating new shader version in Artella: {}'.format(out_file))
                    artellalib.upload_new_asset_version(out_file, comment='New Shader {} version'.format(shader),
                                                        skip_saving=True)
                artellalib.unlock_file(out_file)

                exported_shaders.append(out_file)

        return exported_shaders

    @classmethod
    def load_network(cls, shader_file_path, existing_material=None):
        """
        Loads given shader file and creates a proper shader
        :param shader_file_path: str, JSON shader file
        :param existing_material:
        """

        # Get JSON dict from JSON shader file
        network_dict = cls.read(shader_file_path)
        for key in network_dict:
            if key == 'icon':
                continue
            as_type = network_dict[key]['asType']
            node_type = network_dict[key]['type']
            if existing_material is not None and as_type == 'asShader':
                maya_transform.delete_all_incoming_nodes(node_name=existing_material)
                continue
            elif as_type == 'asShader':
                node = cls.create_shader_node(node_type=node_type,
                                              as_type=as_type, name=key)
                node_sg = maya.cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=key + 'SG')

                if node_type == 'displacementShader':
                    maya.cmds.connectAttr(node + '.displacement', node_sg + '.displacementShader', force=True)
                else:
                    maya.cmds.connectAttr(node + '.outColor', node_sg + '.surfaceShader', force=True)
            else:
                cls.create_shader_node(node_type=node_type, as_type=as_type, name=key)

        for key in network_dict:
            if key == 'icon':
                continue
            as_type = network_dict[key]['asType']
            if existing_material is not None and as_type == 'asShader':
                cls._set_attrs(existing_material, network_dict[key])
            else:
                cls._set_attrs(key, network_dict[key])

        for key in network_dict:
            if key == 'icon':
                continue
            as_type = network_dict[key]['asType']
            if existing_material is not None and as_type == 'asShader':
                continue
            else:
                shader_name = os.path.splitext(os.path.basename(shader_file_path))[0]

                # if key == shader_name and not maya.cmds.objExists(shader_name):
                if key == shader_name:
                    name = key
                else:
                    name = key + '_'
                # name = re.sub('(?<=[A-z])[0-9]+', '', name)
                try:
                    maya.cmds.rename(key, name)
                except Exception:
                    LOGGER.debug('ShaderLibrary: Impossible to rename {0} to {1}'.format(key, name))

    @classmethod
    def create_shader_node(cls, node_type, as_type, name):
        """

        :param node_type:
        :param as_type:
        :param name:
        :return:
        """

        shader_node = None
        if as_type == 'asShader':
            shader_node = maya.cmds.shadingNode(node_type, asShader=True, name=name)
        elif as_type == 'asUtility':
            shader_node = maya.cmds.shadingNode(node_type, asUtility=True, name=name)
        elif as_type == 'asTexture':
            shader_node = maya.cmds.shadingNode(node_type, asTexture=True, name=name)
        return shader_node

    @classmethod
    def get_shading_network(cls, shader_node, prefix=None):
        """

        :param shader_node:
        :param prefix:
        :return:
        """

        if prefix is not None:
            prefix_name = shader_node + '_' + prefix
        else:
            prefix_name = shader_node
        shader_network = dict()
        shader_network[prefix_name] = cls._attrs_to_dict(shader_node, prefix)
        connected_nodes = maya.cmds.listConnections(shader_node, source=True, destination=False)
        if connected_nodes:
            for n in connected_nodes:
                shader_network.update(cls.get_shading_network(n, prefix))
            return shader_network
        else:
            return shader_network

    @classmethod
    def _attrs_to_dict(cls, shader_node, prefix=None):
        """
        Function that get all necessary attributes from shading node and stores
        them in dict

        :param shader_node: str
        :param prefix: str
        :return: dict
        """

        attrs = {
            'asType': None, 'type': None, 'attr': dict(), 'connection': dict()}
        shader_attrs = maya.cmds.listAttr(shader_node, multi=True)

        # Shader object type
        attrs['type'] = maya.cmds.objectType(shader_node)

        # Shading node type
        attrs['asType'] = maya_shaders.get_shading_node_type(shader_node)
        for attr in shader_attrs:
            if not maya.cmds.connectionInfo('{0}.{1}'.format(shader_node, attr), isDestination=True):
                try:
                    value = maya.cmds.getAttr(
                        '{0}.{1}'.format(shader_node, attr))
                    if value is not None:
                        if isinstance(value, list):
                            attrs['attr'][attr] = value[0]
                        else:
                            attrs['attr'][attr] = value
                except Exception:
                    LOGGER.debug('ShaderLibrary: Attribute {0} skipped'.format(attr))
                    continue
            else:
                connected_node, connection = maya.cmds.connectionInfo(
                    '{0}.{1}'.format(shader_node, attr), sourceFromDestination=True).split('.')

                if prefix:
                    new_connection_name = '{}_{}.{}'.format(connected_node, prefix, connection)
                else:
                    new_connection_name = '{}.{}'.format(
                        connected_node, connection)

                attrs['connection'][attr] = new_connection_name
        return attrs

    @classmethod
    def _set_attrs(cls, shader_node, attrs):
        for attr in attrs['connection']:
            con_node, con_attr = attrs['connection'][attr].split('.')
            try:
                maya.cmds.connectAttr(
                    '{}.{}'.format(con_node, con_attr), '{}.{}'.format(shader_node, attr), force=True)
            except Exception:
                continue

        if 'notes' not in attrs['attr'] and maya.cmds.objExists(shader_node) \
                and maya.cmds.attributeQuery('notes', node=shader_node, exists=True):
            maya.cmds.setAttr('{0}.{1}'.format(
                shader_node, 'notes'), '', type='string')
        for attr in attrs['attr']:
            attr_type = None
            if attr in IGNORE_ATTRS:
                continue
            if attr in attrs['connection']:
                continue
            if isinstance(attrs['attr'][attr], list):
                if len(attrs['attr'][attr]) == 3:
                    attr_type = 'double3'
                elif len(attrs['attr'][attr]) == 2:
                    attr_type = 'double2'
                attribute = attrs['attr'][attr]
                try:
                    maya.cmds.setAttr('{0}.{1}'.format(
                        shader_node, attr), type=attr_type, *attribute)
                except Exception as exc:
                    LOGGER.debug(
                        'ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue
            elif isinstance(attrs['attr'][attr], basestring):
                if attr == 'notes' and not maya.cmds.attributeQuery(
                        'notes', node=shader_node, exists=True):
                    maya.cmds.addAttr(
                        shader_node, longName='notes', dataType='string')
                try:
                    maya.cmds.setAttr(
                        '{}.{}'.format(shader_node, attr),
                        attrs['attr'][attr], type='string')
                except Exception as exc:
                    LOGGER.debug(
                        'ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue
            else:
                try:
                    maya.cmds.setAttr(
                        '{}.{}'.format(shader_node, attr), attrs['attr'][attr])
                except Exception as exc:
                    LOGGER.debug(
                        'ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue


def load_shader(project, shader_name):
    """
    Loads shader with given name in current DCC
    :param project: ArtellaProject
    :param shader_name: str
    """

    if not tp.is_maya():
        LOGGER.warning('Shaders loading is only supported in Maya!')
        return

    shader_library_path = project.get_shaders_path()
    if not os.path.exists(shader_library_path):
        LOGGER.debug(
            '{} Shaders Library folder is not synchronized in your PC. '
            'Syncronize it please!'.format(project.name.title()))
        return False

    shaders_extension = str(project.shaders_extension)
    if not shaders_extension.startswith('.'):
        shaders_extension = '.{}'.format(shaders_extension)

    shader_path = path_utils.clean_path(
        os.path.join(shader_library_path, shader_name + shaders_extension))
    if os.path.isfile(shader_path):
        if maya.cmds.objExists(shader_name):
            LOGGER.warning(
                'ShaderLibrary: Shader {} already exists! Shader skipped!'.format(shader_name))
            return False
        else:
            ShadingNetwork.load_network(shader_file_path=shader_path)
    else:
        LOGGER.warning(
            'ShaderLibrary: Shader {0} does not exist! Shader skipped!'.format(shader_path))
        return False

    return True


@UNDO_DECORATOR
def load_scene_shaders(project, load=True, apply_shader=True, tag_nodes=None):
    """
    Loops through all tag data scene nodes and loads all necessary shaders into
    the current scene
    If a specific shader is already loaded, that shader is skip
    :return: list<str>, list of loaded shaders
    """

    if not tp.is_maya():
        LOGGER.warning('Shaders loading is only supported in Maya!')
        return

    if apply_shader:
        all_panels = maya.cmds.getPanel(type='modelPanel')
        for p in all_panels:
            maya.cmds.modelEditor(p, edit=True, displayTextures=False)

    applied_data = list()
    updated_textures = list()

    if not tag_nodes:
        tag_nodes = taggerutils.get_tag_data_nodes(project=project, as_tag_nodes=True)
        tag_info_nodes = project.get_tag_info_nodes(as_tag_nodes=True)
        tag_nodes.extend(tag_info_nodes)

    if not tag_nodes:
        LOGGER.error('No tag nodes found in the current scene. '
                     'Aborting shaders loading ...')
        return None

    added_mats = list()

    for tag in tag_nodes:
        shaders = tag.get_shaders()
        if not shaders:
            LOGGER.error('No shaders found for asset: {}'.format(tag.get_asset().node))
            continue

        asset = tag.get_asset_node()

        hires_group = tag.get_hires_group()
        if not hires_group or not maya.cmds.objExists(hires_group):
            hires_group = tag.get_asset().node

        if not hires_group or not maya.cmds.objExists(hires_group):
            LOGGER.error(
                'No Hires group found for asset: {}'.format(
                    tag.get_asset().node))
            continue

        hires_meshes = [obj for obj in
                        maya.cmds.listRelatives(
                            hires_group, allDescendents=True, type='transform',
                            shapes=False, noIntermediate=True, fullPath=True) if
                        maya.cmds.objExists(obj) and maya.cmds.listRelatives(obj, shapes=True)]
        if not hires_meshes or len(hires_meshes) <= 0:
            LOGGER.error(
                'No Hires meshes found for asset: {}'.format(
                    tag.get_asset().node))
            continue

        if asset.node != hires_group:
            is_referenced = maya.cmds.referenceQuery(asset.node, isNodeReferenced=True)
            if is_referenced:
                namespace = maya.cmds.referenceQuery(asset.node, namespace=True)
                if not namespace or not namespace.startswith(':'):
                    LOGGER.error('Node {} has not a valid namespace!. Please contact TD!'.format(asset.node))
                    continue
                else:
                    namespace = namespace[1:] + ':'

        valid_meshes = list()
        for mesh in hires_meshes:
            is_referenced = maya.cmds.referenceQuery(mesh, isNodeReferenced=True)
            if is_referenced:
                namespace = maya.cmds.referenceQuery(mesh, namespace=True)
                if not namespace or not namespace.startswith(':'):
                    continue
                else:
                    namespace = namespace[1:] + ':'
            else:
                namespace = ''

            mesh_no_namespace = mesh.replace(namespace, '')
            asset_group = mesh_no_namespace.split('|')[1]

            hires_grp_no_namespace = hires_group.replace(namespace, '')
            hires_split = mesh_no_namespace.split(hires_grp_no_namespace)

            group_mesh_name = hires_split[-1]
            group_mesh_name = '|{0}{1}'.format(asset_group, group_mesh_name)

            for shader_mesh in shaders.keys():
                if shader_mesh == group_mesh_name:
                    valid_meshes.append(mesh)
                    break

            for shader_mesh in shaders.keys():
                shader_short = tp.Dcc.node_short_name(shader_mesh)
                group_short = tp.Dcc.node_short_name(group_mesh_name)
                if shader_short == group_short:
                    if mesh not in valid_meshes:
                        valid_meshes.append(mesh)
                        break

        if len(valid_meshes) <= 0:
            LOGGER.error('No valid meshes found on asset. Please contact TD!'.format(tag.get_asset()))
            continue

        meshes_shading_groups = list()
        for mesh in valid_meshes:
            mesh_shapes = maya.cmds.listRelatives(mesh, shapes=True, noIntermediate=True)
            if not mesh_shapes or len(mesh_shapes) <= 0:
                LOGGER.error('Mesh {} has not valid shapes!'.format(mesh))
                continue
            for shape in mesh_shapes:
                shape_name = shape.split(':')[-1]
                if shape_name.endswith('Deformed'):
                    shape_name = shape_name.replace('Deformed', '')
                for shader_mesh, shader_data in shaders.items():
                    for shader_shape, shader_group in shader_data.items():
                        shader_shape_name = shader_shape.split('|')[-1]
                        if shape_name == shader_shape_name:
                            meshes_shading_groups.append([mesh, shader_group])
        if len(meshes_shading_groups) <= 0:
            LOGGER.error('No valid shading groups found on asset. Please contact TD!'.format(tag.get_asset()))
            continue

        for mesh_info in meshes_shading_groups:
            mesh = mesh_info[0]
            shading_info = mesh_info[1]
            for shading_grp, materials in shading_info.items():
                if not materials or len(materials) <= 0:
                    LOGGER.error('No valid materials found on mesh {0} of asset {1}'.format(mesh, tag.get_asset()))
                    continue

                # If shading group already exists we do not create the material
                if maya.cmds.objExists(shading_grp):
                    continue

                for mat in materials:
                    if not mat or mat in added_mats:
                        continue
                    added_mats.append(mat)

                    if load:
                        LOGGER.debug('Loading Shader: {}'.format(mat))
                        valid_shader = load_shader(project=project, shader_name=mat)
                        if not valid_shader:
                            LOGGER.error('Error while loading shader {}'.format(mat))

            # After materials are created we try to apply to the meshes
            try:
                for shading_grp, materials in shading_info.items():
                    if not tp.Dcc.object_exists(shading_grp):
                        for mat in materials:
                            if not materials or len(materials) <= 0:
                                continue
                            LOGGER.error(
                                'Shading group {}  loaded from shader info does not exists!'.format(shading_grp))
                            shading_grp = mat + 'SG'
                            LOGGER.error(
                                'Applying shading group based on nomenclature: {}'.format(shading_grp))
                            if tp.Dcc.object_exists(shading_grp):
                                LOGGER.error(
                                    'Impossible to set shading group {0} to mesh {1}'.format(shading_grp, mesh))
                                break

                    if apply_shader:
                        maya.cmds.sets(mesh, edit=True, forceElement=shading_grp)
                        maya.cmds.ogs(reset=True)
                        file_nodes = maya.cmds.ls(type='file')
                        for f in file_nodes:
                            if f not in updated_textures:
                                updated_textures.append(f)
                                maya.cmds.ogs(regenerateUVTilePreview=f)
                        LOGGER.debug('Shading set {0} applied to mesh {1}'.format(shading_grp, mesh))
                    applied_data.append([mesh, shading_grp])

            except Exception as e:
                LOGGER.error('Impossible to set shading group {0} to mesh {1}'.format(shading_grp, mesh))
                LOGGER.error(str(e))

    return applied_data


def load_all_scene_shaders(project, load=True, apply_shader=True):
    """
    Loops through all tag data scene nodes and loads all necessary shaders into the current scene
    If a specific shader is already loaded, that shader is skip
    :return: list<str>, list of loaded shaders
    """

    if not tp.is_maya():
        LOGGER.warning('Shaders loading is only supported in Maya!')
        return

    return load_scene_shaders(project=project, load=load, apply_shader=apply_shader)


@UNDO_DECORATOR
def unload_shaders(project, tag_nodes=None):
    """
    Unload shaders applied to assets loaded in current DCC scene or to given ones
    :param tag_nodes:
    """

    if not tp.is_maya():
        LOGGER.warning('Shaders unloading is only supported in Maya!')
        return

    if not tag_nodes:
        tag_nodes = taggerutils.get_tag_data_nodes(project=project, as_tag_nodes=True)
        tag_info_nodes = project.get_tag_info_nodes(as_tag_nodes=True)
        tag_nodes.extend(tag_info_nodes)

    found_nodes = list()
    found_nodes.extend(tag_nodes)

    for tag in found_nodes:
        shaders = tag.get_shaders()
        if not shaders:
            LOGGER.error('No shaders found for asset: {}'.format(tag.get_asset().node))
            continue

        for shader_geo, shader_shapes in shaders.items():
            for shader_shp, shader_data in shader_shapes.items():
                for shader_sg, shader_names in shader_data.items():
                    found_meshes = list()
                    if not tp.Dcc.object_exists(shader_sg):
                        continue
                    cns = maya.cmds.listConnections(shader_sg)
                    for cnt in cns:
                        cnt_type = maya.cmds.nodeType(cnt, i=True)
                        if 'dagNode' in cnt_type:
                            found_meshes.append(cnt)
                    for mesh in found_meshes:
                        maya.cmds.sets(mesh, edit=True, forceElement='initialShadingGroup')

                    for shd in shader_names:
                        if tp.Dcc.object_exists(shd) and shd not in ['lambert1', 'particleCloud1']:
                            tp.Dcc.delete_object(shd)
                    if shader_sg not in ['initialShadingGroup', 'initialParticleSE']:
                        tp.Dcc.delete_object(shader_sg)
