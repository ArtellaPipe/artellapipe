#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle shaders
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import traceback

from Qt.QtCore import *
from Qt.QtGui import *

import tpDccLib as tp
from tpPyUtils import decorators, path as path_utils

import artellapipe.register
from artellapipe.core import config
from artellapipe.utils import shader

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import decorators as maya_decorators
    from tpMayaLib.core import shader as maya_shader
    UNDO_DECORATOR = maya_decorators.undo_chunk
else:
    UNDO_DECORATOR = decorators.empty_decorator

LOGGER = logging.getLogger()


class ShadersManager(object):
    def __init__(self):
        super(ShadersManager, self).__init__()

        self._project = None
        self._config = None

    @property
    def config(self):
        return self._config

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project
        self._config = config.get_config(project, 'artellapipe-shaders')

    def get_shaders_paths(self):
        """
        Returns path where shaders are located in the project
        :return: str
        """

        shaders_paths = self.config.get('paths')
        return [path_utils.clean_path(
            os.path.join(artellapipe.AssetsMgr().get_assets_path(), p)) for p in shaders_paths]

    def get_extension(self):
        """
        Returns extension used by shaders
        :return: str
        """

        shaders_extension = self.config.get('extension')
        if not shaders_extension:
            LOGGER.warning('Current Project Shaders Extension: "{}" is not valid!'.format(shaders_extension))
            return None
        if not shaders_extension.startswith('.'):
            shaders_extension = '.{}'.format(shaders_extension)

        return shaders_extension

    def update_shaders(self):
        """
        Updates shaders from Artella
        """

        shaders_paths = self.get_shaders_paths()
        if not shaders_paths:
            return

        artellapipe.FilesMgr().sync_files(files=shaders_paths)

    def load_shader(self, shader_name):
        """
        Loads shader with given name in current DCC
        :param shader_name: str
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders loading is only supported in Maya!')
            return

        valid_shaders_paths = list()
        shader_library_paths = self.get_shaders_paths()
        for p in shader_library_paths:
            if not os.path.exists(p):
                continue
            valid_shaders_paths.append(p)

        if not valid_shaders_paths:
            LOGGER.debug(
                '{} Shaders Library folder is not synchronized in your PC. Synchronize it please!'.format(
                    self._project.name.title()))
            return False

        shaders_extension = self.get_extension()
        if not shaders_extension:
            return False

        for shaders_path in valid_shaders_paths:

            shader_path = path_utils.clean_path(
                os.path.join(shaders_path, shader_name + shaders_extension))
            if os.path.isfile(shader_path):
                if tp.Dcc.object_exists(shader_name):
                    LOGGER.warning('ShaderLibrary: Shader {} already exists! Shader skipped!'.format(shader_name))
                    return False
                else:
                    shader.ShadingNetwork.load_network(shader_file_path=shader_path)
                    return True
            else:
                LOGGER.warning('ShaderLibrary: Shader {0} does not exist! Shader skipped!'.format(shader_path))
                return False

        return True

    @UNDO_DECORATOR
    def load_scene_shaders(self, load=True, apply_shader=True, tag_nodes=None):
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
            tag_nodes = artellapipe.TagsMgr().get_tag_data_nodes(project=self._project, as_tag_nodes=True)
            tag_info_nodes = artellapipe.TagsMgr().get_tag_info_nodes(as_tag_nodes=True)
            tag_nodes.extend(tag_info_nodes)

        if not tag_nodes:
            LOGGER.error('No tag nodes found in the current scene. Aborting shaders loading ...')
            return None

        added_mats = list()

        for tag in tag_nodes:
            shaders = tag.get_shaders()
            if not shaders:
                LOGGER.error('No shaders found for asset: {}'.format(tag.get_asset().node))
                continue

            asset = tag.get_asset_node()

            hires_group = tag.get_hires_group()
            if not hires_group or not tp.Dcc.object_exists(hires_group):
                hires_group = tag.get_asset().node

            if not hires_group or not tp.Dcc.object_exists(hires_group):
                LOGGER.error('No Hires group found for asset: {}'.format(tag.get_asset().node))
                continue

            hires_meshes = [obj for obj in
                            maya.cmds.listRelatives(
                                hires_group, allDescendents=True, type='transform',
                                shapes=False, noIntermediate=True, fullPath=True) if
                            tp.Dcc.object_exists(obj) and maya.cmds.listRelatives(obj, shapes=True)]
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
                mesh_shapes = tp.Dcc.list_relatives(node=mesh, shapes=True, intermediate_shapes=False)
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
                    if tp.Dcc.object_exists(shading_grp):
                        continue

                    for mat in materials:
                        if not mat or mat in added_mats:
                            continue
                        added_mats.append(mat)

                        if load:
                            LOGGER.debug('Loading Shader: {}'.format(mat))
                            valid_shader = self.load_shader(shader_name=mat)
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

    def load_all_scene_shaders(self, load=True, apply_shader=True):
        """
        Loops through all tag data scene nodes and loads all necessary shaders into the current scene
        If a specific shader is already loaded, that shader is skip
        :return: list<str>, list of loaded shaders
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders loading is only supported in Maya!')
            return

        return self.load_scene_shaders(load=load, apply_shader=apply_shader)

    @UNDO_DECORATOR
    def unload_shaders(self, tag_nodes=None):
        """
        Unload shaders applied to assets loaded in current DCC scene or to given ones
        :param tag_nodes:
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders unloading is only supported in Maya!')
            return

        if not tag_nodes:
            tag_nodes = artellapipe.TagsMgr().get_tag_data_nodes(as_tag_nodes=True)
            tag_info_nodes = artellapipe.TagsMgr().get_tag_info_nodes(as_tag_nodes=True)
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

    def export_shader(self, shader_name, export_path=None, publish=False, comment=None, shader_swatch=None):
        """
        Exports shaders
        :param shader_name: str, name of the shader to export
        :param export_path: str, path where shader file will be exported into (optional)
        :param comment: str, publish comment
        :param shader_swatch: str, path where shader file will be exported into (optional)
        :param publish: bool
        :return:
        """

        if not export_path:
            shader_library_paths = self.get_shaders_paths()
            if shader_library_paths:
                export_path = shader_library_paths[0]
        if not export_path or not os.path.exists(export_path):
            LOGGER.warning(
                'Shader Export Path "{}" does not exists. Aborting shader "{}"  export!'.format(
                    export_path, shader_name))
            return None

        if not tp.Dcc.object_exists(shader_name):
            LOGGER.warning('Shader {0} does not exists in the scene! Aborting shader export!'.format(shader_name))
            return None

        exported_shader = None
        shader_swatch = shader_swatch

        if not shader_swatch and tp.is_maya():
            shader_swatch = maya_shader.get_shader_swatch(shader_name=shader_name)

        px = QPixmap(QSize(100, 100))
        shader_swatch.render(px)
        temp_file = os.path.join(export_path, 'tmp.png')
        px.save(temp_file)
        try:
            exported_shader = shader.ShadingNetwork.write_network(
                shaders_path=export_path, shaders=[shader_name], icon_path=temp_file, publish=publish, commment=comment)
        except Exception as exc:
            LOGGER.error('Error while exporting shader: {} | {}'.format(exc, traceback.format_exc()))
            os.remove(temp_file)

        return exported_shader

    def export_shaders(self, shaders_names, publish=False, comment=None):
        """
        Exports all given shader names from current scene
        :param shaders_names: list(str)
        :param publish: bool
        :param comment: str
        :return: list
        """

        exported_shaders = list()

        if not shaders_names:
            return exported_shaders

        for shader_name in shaders_names:
            exported_shader = self.export_shader(shader_name=shader_name, publish=publish, comment=comment)
            exported_shaders.append(exported_shader)

        return exported_shaders


@decorators.Singleton
class ArtellaShadersManagerSingleton(ShadersManager, object):
    def __init__(self):
        ShadersManager.__init__(self)


artellapipe.register.register_class('ShadersMgr', ArtellaShadersManagerSingleton)
