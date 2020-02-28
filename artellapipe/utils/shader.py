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

import tpDcc as tp
from tpDcc.libs.qt.core import image

import artellapipe
from artellapipe.libs.artella.core import artellalib


IGNORED_SHADERS = list()
IGNORE_ATTRS = list()
if tp.is_maya():
    import tpDcc.dccs.maya as maya
    from tpDcc.dccs.maya.core import shader as maya_shaders
    from tpDcc.dccs.maya.core import transform as maya_transform

    IGNORE_SHADERS = ['particleCloud1', 'shaderGlow1', 'defaultColorMgtGlobals', 'lambert1']
    IGNORE_ATTRS = ['computedFileTextureNamePattern']

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

    @classmethod
    def write_network(cls, shader_extension, shaders_path, shaders=None, icon_path=None, publish=False, comment=None):
        """
        Writes shader network info to the given path
        :param shader_extension: str
        :param shaders_path: str, path where we want to store the shader
        :param shaders: list<str>, list of shaders we want to store
        :param icon_path: str, icon we want to show in the shader viewer
        :param publish: bool
        :param comment: str
        :return: list<str>, list of exported shaders
        """

        if not shader_extension:
            LOGGER.warning('Impossible to export shading because extension was not defined')
            return
        if not shader_extension.startswith('.'):
            shader_extension = '.{}'.format(shader_extension)

        if not os.path.exists(shaders_path):
            LOGGER.warning('ShaderLibrary: Shaders Path %s is not valid! Aborting export!', shaders_path)
            return

        if shaders is None:
            shaders = tp.Dcc.list_materials()

        exported_shaders = list()
        for shader in shaders:
            if shader not in IGNORE_SHADERS:
                shading_group = cls.get_shading_group(shader_node=shader)
                if not shading_group:
                    LOGGER.warning('No shading group linked to shader: "{}"'.format(shader))
                    continue

                # Get dict with all the info of the shader
                shader_network = cls.get_shading_network(shading_group)

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
                    if not comment:
                        comment = 'New Shader {} version'.format(shader)
                    artellalib.upload_new_asset_version(out_file, comment=comment, skip_saving=True)
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
                if node_type == 'displacementShader':
                    pass
                    # tp.Dcc.connect_attribute(source_node=node, source_attribute='displacement',
                    #                          target_node=node_sg, target_attribute='displacementShader', force=True)
                else:
                    node_sg = maya.cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=key + 'SG')
                    tp.Dcc.connect_attribute(source_node=node, source_attribute='outColor',
                                             target_node=node_sg, target_attribute='surfaceShader', force=True)
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
            # else:
            #     shader_name = os.path.splitext(os.path.basename(shader_file_path))[0]

                # if key == shader_name and not maya.cmds.objExists(shader_name):
                # if key == shader_name:
                #     name = key
                # else:
                #     name = key + '_'
                # name = re.sub('(?<=[A-z])[0-9]+', '', name)
                # try:
                #     tp.Dcc.rename_node(key, name)
                # except Exception:
                #     LOGGER.debug('ShaderLibrary: Impossible to rename {0} to {1}'.format(key, name))

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
    def get_shading_group(cls, shader_node, prefix=None):
        """

        :param shader_node:
        :param prefix:
        :return:
        """

        if prefix is not None:
            prefix_name = shader_node + '_' + prefix
        else:
            prefix_name = shader_node

        shading_groups_found = list()
        out_connections = tp.Dcc.list_destination_connections(node=prefix_name) or list()
        for n in out_connections:
            if not n or not tp.Dcc.object_exists(n) or not tp.Dcc.node_type(n) == 'shadingEngine':
                continue
            shading_groups_found.append(n)

        if not shading_groups_found:
            return None

        if len(shading_groups_found) > 1:
            same_sg = True
            current_sg = None
            for sg in shading_groups_found:
                if not current_sg:
                    current_sg = sg
                else:
                    if sg != current_sg:
                        same_sg = False
                        break
            if not same_sg:
                LOGGER.warning(
                    'Multiple Shading Groups found for "{}": "{}". First one will be used exported ...'.format(
                        prefix_name, shading_groups_found))

        return shading_groups_found[0]

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
        connected_nodes = tp.Dcc.list_source_connections(node=shader_node) or list()

        # shading_group = cls.get_shading_group(shader_node=shader_node, prefix=prefix)
        # if shading_group:
        #     shader_network['shading_group'] = dict()
        #     shader_network['shading_group'][shading_group] = cls._attrs_to_dict(shading_group, prefix)
        #     shading_group_connections = tp.Dcc.list_source_connections(node=shading_group) or list()
        #     shader_network['shading_group']
        #     for n in shading_group_connections:
        #         if not n or not tp.Dcc.object_exists(n) or n == shader_node or tp.Dcc.node_type(n) == 'transform':
        #             continue
        #         shader_network['shading_group'][shading_group].update(cls.get_shading_network(n, prefix))
        #         return shader_network

        if not connected_nodes:
            return shader_network

        for n in connected_nodes:
            shader_network.update(cls.get_shading_network(n, prefix))

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
        shader_attrs = tp.Dcc.list_attributes(node=shader_node, multi=True)

        # Shader object type
        attrs['type'] = tp.Dcc.object_type(shader_node)

        # Shading node type
        attrs['asType'] = maya_shaders.get_shading_node_type(shader_node)
        for attr in shader_attrs:
            if not maya.cmds.connectionInfo('{0}.{1}'.format(shader_node, attr), isDestination=True):
                try:
                    value = tp.Dcc.get_attribute_value(node=shader_node, attribute_name=attr)
                    if value is not None:

                        if attr == 'fileTextureName':
                            value = artellapipe.FilesMgr().resolve_path(value)

                        if isinstance(value, list):
                            attrs['attr'][attr] = value[0]
                        else:
                            attrs['attr'][attr] = value
                except Exception:
                    LOGGER.debug('ShaderLibrary: Attribute {0} skipped'.format(attr))
                    continue
            else:
                cconnection_info = maya.cmds.connectionInfo(
                    '{0}.{1}'.format(shader_node, attr), sourceFromDestination=True).split('.')
                connected_node = cconnection_info[0]
                connection = cconnection_info[1]

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
                tp.Dcc.connect_attribute(source_node=con_node, source_attribute=con_attr,
                                         target_node=shader_node, target_attribute=attr, force=True)
            except Exception:
                continue

        if 'notes' not in attrs['attr'] and tp.Dcc.object_exists(
                shader_node) and tp.Dcc.attribute_exists(node=shader_node, attribute_name='notes'):
            tp.Dcc.set_string_attribute_value(node=shader_node, attribute_name='notes', attribute_value='')
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
                if attr == 'notes' and not tp.Dcc.attribute_exists(node=shader_node, attribute_name='notes'):
                    tp.Dcc.add_string_attribute(node=shader_node, attribute_name='notes')
                try:
                    value = attrs['attr'][attr]

                    if attr == 'fileTextureName' and value:
                        env_var = '${}/'.format(artellapipe.project.env_var)
                        if not value.startswith(env_var):
                            production_folder_name = artellapipe.project.get_production_folder()
                            split_path = value.split(production_folder_name)
                            if split_path:
                                new_path = production_folder_name + split_path[-1]
                                path_to_fix = artellapipe.FilesMgr().prefix_path_with_artella_env_path(new_path)
                                value = artellapipe.FilesMgr().resolve_path(path_to_fix)
                    tp.Dcc.set_string_attribute_value(
                        node=shader_node, attribute_name=attr, attribute_value=value)
                except Exception as exc:
                    LOGGER.debug(
                        'ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue
            else:
                try:
                    tp.Dcc.set_attribute_value(
                        node=shader_node, attribute_name=attr, attribute_value=attrs['attr'][attr])
                except Exception as exc:
                    LOGGER.debug(
                        'ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue
