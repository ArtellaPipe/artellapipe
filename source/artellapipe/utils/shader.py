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

from tpPyUtils import  path as path_utils

import tpDccLib as tp

from tpQtLib.core import image

import artellapipe
from artellapipe.core import artellalib

IGNORED_SHADERS = list()
IGNORE_ATTRS = list()

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import shader as maya_shaders
    from tpMayaLib.core import transform as maya_transform
    IGNORE_SHADERS = ['particleCloud1', 'shaderGlow1', 'defaultColorMgtGlobals', 'lambert1']
    IGNORE_ATTRS = ['computedFileTextureNamePattern']


class ShadingNetwork(object):
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

        with open(file_dir, 'w') as f:
            json.dump(shader_dict, f, indent=4, sort_keys=True)

    @staticmethod
    def read(file_dir):
        """
        Reads shader info from given JSON file
        :param file_dir: str
        :return: dict
        """

        with open(file_dir, 'r') as f:
            shader_dict = json.load(f)
        return shader_dict

    @classmethod
    def write_network(cls, shader_extension, shaders_path, shaders=None, icon_path=None, publish=False):
        """
        Writes shader network info to the given path
        :param shaders_path: str, path where we want to store the shader
        :param shaders: list<str>, list of shaders we want to store
        :param icon_path: str, icon we want to show in the shader viewer
        :return: list<str>, list of exported shaders
        """
        if not os.path.exists(shaders_path):
            artellapipe.logger.debug('ShaderLibrary: Shaders Path {0} is not valid! Aborting export!'.format(shaders_path))

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
                artellapipe.logger.debug('Generating Shader {0} in {1}'.format(shader, out_file))

                # if os.path.isfile(out_file):
                #     temp_file, temp_filename = tempfile.mkstemp()
                #     cls.write(shader_network, temp_filename)
                #     if filecmp.cmp(out_file, temp_filename):
                #         sys.solstice.logger.debug('Shader file already exists and have same size. No new shader file will be generated!')
                #         result = solstice_qt_utils.show_question(None, 'New Shader File Version', 'Shader File {} already exists with same file size! Do you want to upload it to Artella anyways?'.format(shader))
                #         if result == QMessageBox.No:
                #             upload_new_version = False
                #     else:
                #         sys.solstice.logger.debug('Writing shader file: {}'.format(out_file))
                #         cls.write(shader_network, out_file)
                # else:
                artellalib.lock_file(out_file, force=True)
                artellapipe.logger.debug('Writing shader file: {}'.format(out_file))
                cls.write(shader_network, out_file)

                if publish:
                    artellapipe.logger.debug('Creating new shader version in Artella: {}'.format(out_file))
                    artellalib.upload_new_asset_version(out_file, comment='New Shader {} version'.format(shader), skip_saving=True)
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
                maya_transform.delete_all_incoming_nodes(node=existing_material)
                continue
            elif as_type == 'asShader':
                node = cls.create_shader_node(node_type=node_type, as_type=as_type, name=key)
                node_sg = maya.cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=key+'SG')

                if node_type == 'displacementShader':
                    maya.cmds.connectAttr(node+'.displacement', node_sg+'.displacementShader', force=True)
                else:
                    maya.cmds.connectAttr(node+'.outColor', node_sg+'.surfaceShader', force=True)
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
                    name = key+'_'
                # name = re.sub('(?<=[A-z])[0-9]+', '', name)
                try:
                    maya.cmds.rename(key, name)
                except Exception:
                    artellapipe.logger.debug('ShaderLibrary: Impossible to rename {0} to {1}'.format(key, name))

    @classmethod
    def create_shader_node(cls, node_type, as_type, name):
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
        Function that get all necessary attributes from shading node and stores them in dict
        :param shader_node: str
        :param prefix: str
        :return: dict
        """

        attrs = {'asType': None, 'type': None, 'attr': dict(), 'connection': dict()}
        shader_attrs = maya.cmds.listAttr(shader_node, multi=True)

        # Shader object type
        attrs['type'] = maya.cmds.objectType(shader_node)

        # Shading node type
        attrs['asType'] = maya_shaders.get_shading_node_type(shader_node)
        for attr in shader_attrs:
            if not maya.cmds.connectionInfo('{0}.{1}'.format(shader_node, attr), isDestination=True):
                try:
                    value = maya.cmds.getAttr('{0}.{1}'.format(shader_node, attr))
                    if value is not None:
                        if isinstance(value, list):
                            attrs['attr'][attr] = value[0]
                        else:
                            attrs['attr'][attr] = value
                except Exception:
                    artellapipe.logger.debug('ShaderLibrary: Attribute {0} skipped'.format(attr))
                    continue
            else:
                connected_node, connection = maya.cmds.connectionInfo('{0}.{1}'.format(shader_node, attr), sourceFromDestination=True).split('.')

                if prefix:
                    new_connection_name = connected_node + '_' + prefix + '.' + connection
                else:
                    new_connection_name = connected_node + '.' + connection

                attrs['connection'][attr] = new_connection_name
        return attrs

    @classmethod
    def _set_attrs(cls, shader_node, attrs):
        for attr in attrs['connection']:
            con_node, con_attr = attrs['connection'][attr].split('.')
            try:
                maya.cmds.connectAttr('{0}.{1}'.format(con_node, con_attr), '{0}.{1}'.format(shader_node, attr), force=True)
            except Exception:
                # sys.solstice.logger.debug('ShaderLibrary: Attribute Connection {0} skipped!'.format(attr))
                continue

        if 'notes' not in attrs['attr'] and maya.cmds.objExists(shader_node) and maya.cmds.attributeQuery('notes', node=shader_node, exists=True):
            maya.cmds.setAttr('{0}.{1}'.format(shader_node, 'notes'), '', type='string')
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
                    maya.cmds.setAttr('{0}.{1}'.format(shader_node, attr), type=attr_type, *attribute)
                except Exception:
                    artellapipe.logger.debug('ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue
            elif isinstance(attrs['attr'][attr], basestring):
                if attr == 'notes' and not maya.cmds.attributeQuery('notes', node=shader_node, exists=True):
                    maya.cmds.addAttr(shader_node, longName='notes', dataType='string')
                try:
                    maya.cmds.setAttr('{}.{}'.format(shader_node, attr), attrs['attr'][attr], type='string')
                except Exception:
                    artellapipe.logger.debug('ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue
            else:
                try:
                    maya.cmds.setAttr('{}.{}'.format(shader_node, attr), attrs['attr'][attr])
                except:
                    artellapipe.logger.debug('ShaderLibrary: setAttr {0} skipped!'.format(attr))
                    continue


def load_shader(project, shader_name):
    """
    Loads shader with given name in current DCC
    :param shader_name: str
    """

    shader_library_path = project.get_shaders_path()
    if not os.path.exists(shader_library_path):
        artellapipe.logger.debug('Solstice Shaders Library folder is not synchronized in your PC. Syncronize it please!')
        return False

    shaders_extension = str(project.shaders_extension)
    if not shaders_extension.startswith('.'):
        shaders_extension = '.{}'.format(shaders_extension)

    shader_path = path_utils.clean_path(os.path.join(shader_library_path, shader_name + shaders_extension))
    if os.path.isfile(shader_path):
        if maya.cmds.objExists(shader_name):
            artellapipe.logger.warning('ShaderLibrary: Shader {} already exists! Shader skipped!'.format(shader_name))
            return False
        else:
            ShadingNetwork.load_network(shader_file_path=shader_path)
    else:
        artellapipe.logger.warning('ShaderLibrary: Shader {0} does not exist! Shader skipped!'.format(shader_path))
        return False

    return True