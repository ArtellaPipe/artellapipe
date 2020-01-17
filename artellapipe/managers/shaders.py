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

import tpDccLib as tp
from tpPyUtils import decorators, python, path as path_utils

import artellapipe.register
from artellapipe.core import defines, config

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import decorators as maya_decorators
    from tpMayaLib.core import attribute as maya_attribute
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

    def get_scene_operator(self, create=True):
        """
        Returns scene shaders operator node
        :return: str
        """

        scene_operator = 'assets_operator'
        if create:
            if not tp.Dcc.object_exists(scene_operator):
                scene_operator = maya.cmds.createNode('aiMerge', name='assets_operator')
                tp.Dcc.connect_attribute(scene_operator, 'message', 'defaultArnoldRenderOptions', 'operator',
                                         force=True)

        return scene_operator

    def remove_scene_operator(self):
        """
        Removes scene shader operator node if it has no more connections
        """

        scene_operator = self.get_scene_operator(create=False)
        if not scene_operator or not tp.Dcc.object_exists(scene_operator):
            return

        inputs = tp.Dcc.list_source_connections(scene_operator)
        if inputs:
            LOGGER.warning(
                'Impossible to remove scene operator: "{}" because it has input connections!'.format(scene_operator))
            return

        tp.Dcc.delete_object(scene_operator)

        return True

    def get_shaders_file_type(self):
        """
        Returns file type used to define shaders
        """

        return self.config.get('file_type', default='shader')

    def get_shader_path_file_type(self):
        """
        Returns file type used to define shaders path
        :return: str
        """

        return self.config.get('shader_path_file_type', default='shaders')

    def get_shaders_extensions(self):
        """
        Returns extension used for shaders in current project
        :return: str
        """

        shaders_file_type = self.get_shaders_file_type()
        extensions = artellapipe.FilesMgr().get_file_type_extensions(shaders_file_type)
        if not extensions:
            LOGGER.warning('Impossible to refresh shaders because shader file type is not defined in current project!')
            return None

        return extensions

    def get_shader_file_class(self):
        """
        Returns shader file class associated to this asset
        :return: class
        """

        shaders_file_type = self.get_shaders_file_type()
        if not shaders_file_type:
            LOGGER.warning('No Asset Shaders file type available!')
            return None

        asset_shader_file_class = artellapipe.FilesMgr().get_file_class(shaders_file_type)
        if not asset_shader_file_class:
            LOGGER.warning('No Shader File Class found! Aborting shader loading ...')
            return None

        return asset_shader_file_class

    def get_shaders_paths(self):
        """
        Returns path where shaders are located in the project
        :return: str
        """

        shaders_paths = self.config.get('paths')
        return [path_utils.clean_path(
            os.path.join(artellapipe.AssetsMgr().get_assets_path(), p)) for p in shaders_paths]

    def get_shader_file(self, shader_name, shader_path=None, asset=None):
        """
        Returns shader file with given name (if exists)
        :param shader_name: str
        :param shader_path: str
        :param asset: str
        :return:
        """

        if not shader_path:
            shaders_paths = self.get_shaders_paths()
            if not shaders_paths:
                LOGGER.warning('Impossible to return shader file path because no shaders path are defined')
                return
        else:
            shaders_paths = python.force_list(shader_path)

        shaders_file_type = self.config.get('file_type', None)
        if not shaders_file_type:
            LOGGER.warning('Impossible to return shader file path because shader file type is not defined!')
            return

        shader_file_class = artellapipe.FilesMgr().get_file_class(shaders_file_type)
        if not shader_file_class:
            LOGGER.warning(
                'Impossible to get shader path: {} | {} | {}'.format(shader_name, shaders_paths, shaders_file_type))
            return

        if asset:
            extra_dict = {
                'shader_name': shader_name
            }
            asset_shader_file_path = asset.get_file(
                shaders_file_type, status=defines.ArtellaFileStatus.WORKING, extra_dict=extra_dict
            )
            if not asset_shader_file_path:
                LOGGER.warning('No Shaders Path available for asset: "{}"'.format(asset.get_name()))
                return None

            shader_file = shader_file_class(self._project, shader_name, file_path=shader_path)
            return shader_file

        else:
            for shader_path in shaders_paths:
                shader_file = shader_file_class(self._project, shader_name, file_path=shader_path)
                shader_file_paths = shader_file.get_file_paths()
                if shader_path:
                    return shader_file
                else:
                    for shader_file_path in shader_file_paths:
                        if os.path.isfile(shader_file_path):
                            return shader_file

        return None

    def get_shader_path(self, shader_name):
        """
        Returns shader path with given name (if exists)
        :param shader_name: str
        :return: str
        """

        shader_file = self.get_shader_file(shader_name)
        if not shader_file:
            LOGGER.warning('Impossible to get shader path for shader "{}"'.format(shader_name))
            return

        shader_file_paths = shader_file.get_file_paths()
        for shader_file_path in shader_file_paths:
            if os.path.isfile(shader_file_path):
                return shader_file_path

        return None

    def update_shaders(self, shaders_paths=None):
        """
        Updates shaders from Artella
        """

        if shaders_paths:
            shaders_paths = python.force_list(shaders_paths)
        else:
            shaders_paths = self.get_shaders_paths()

        if not shaders_paths:
            return

        artellapipe.FilesMgr().sync_files(files=shaders_paths)

    def load_shader(self, shader_name, shader_path=None, apply=True):
        """
        Loads shader with given name in current DCC
        :param shader_name: str
        :param apply: bool
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders loading is only supported in Maya!')
            return

        if apply:
            all_panels = maya.cmds.getPanel(type='modelPanel')
            for p in all_panels:
                maya.cmds.modelEditor(p, edit=True, displayTextures=False)

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

        shader_file = self.get_shader_file(shader_name, shader_path=shader_path)
        if not shader_file:
            LOGGER.warning('Impossible to load shader "{}"!'.format(shader_name))
            return

        shader_file.import_file()

        return True

    def load_asset_shaders(self, asset, apply_shaders=True, status=defines.ArtellaFileStatus.PUBLISHED):
        """
        Loads all the shaders of the given asset
        :param asset:
        :param apply_shaders: bool
        :param status:
        """

        asset_shaders_file = asset.get_asset_shaders_file(status=status)
        if not asset_shaders_file:
            LOGGER.warning('No asset shader file found!')
            return False

        shader_names = asset_shaders_file.get_shaders()
        if not shader_names:
            LOGGER.warning('No shaders to load found!')

        if apply:
            scene_operator = self.get_scene_operator()
            if not tp.Dcc.object_exists(scene_operator):
                LOGGER.warning('No Scene Operator found in current scene!')
                return False

        asset_shading_geo_mapping = asset_shaders_file.get_shading_geometry_mapping()
        shaded_shapes = asset_shading_geo_mapping.keys()
        updated_shapes = dict()
        for shape in shaded_shapes:
            if shape in updated_shapes:
                LOGGER.warning(
                    'Shape "{}" already checked. Multiple shapes with same name in Asset Shaders File. '
                    'Reexport shader again!'.format(shape))
                continue
            if tp.Dcc.object_exists(shape):
                updated_shapes[shape] = shape
            else:
                shape_ns = tp.Dcc.node_namespace(shape, check_node=False)
                if shape_ns:
                    LOGGER.warning(
                        'Shape "{}" already has a namespace defined in Asset Shaders File. '
                        'Reexport shader without namespace!'.format(shape))
                    continue
                new_shape = shape.split('|')[-1]
                new_shape = '{}:{}'.format(asset.id, new_shape)
                updated_shapes[shape] = new_shape

        for shader_name in shader_names:
            valid_load = self.load_shader(shader_name, apply=apply)
            if not valid_load:
                LOGGER.warning('Something went wrong when loading Shader "{}"'.format(shader_name))
                continue

        if apply_shaders:
            next_asset_index = maya_attribute.next_available_multi_index(
                '{}.inputs'.format(scene_operator), use_connected_only=False)
            asset_operator_node = maya.cmds.createNode('aiMerge', name='{}_operator'.format(asset.id))
            tp.Dcc.connect_attribute(
                source_node=asset_operator_node, source_attribute='out',
                target_node=scene_operator, target_attribute='inputs[{}]'.format(next_asset_index)
            )
            for i, (original_shape, updated_shape) in enumerate(updated_shapes.items()):
                shaders_to_apply = asset_shading_geo_mapping[original_shape]
                asset_shape_node = maya.cmds.createNode('aiSetParameter', name='{}_set'.format(updated_shape))
                shape_name = updated_shape.split(':')[-1]
                tp.Dcc.set_string_attribute_value(asset_shape_node, 'selection', '{}*{}'.format(asset.id, shape_name))
                tp.Dcc.connect_attribute(
                    source_node=asset_shape_node, source_attribute='out',
                    target_node=asset_operator_node, target_attribute='inputs[{}]'.format(i))
                for j, shader_to_apply in enumerate(shaders_to_apply):
                    tp.Dcc.set_string_attribute_value(
                        asset_shape_node, 'assignment[{}]'.format(j), "shader = '{}'".format(shader_to_apply))

        return True

    def unload_asset_shaders(self, asset, status=defines.ArtellaFileStatus.PUBLISHED):
        """
        Unload shaders of given asset
        :param asset:
        :param status:
        :param with_undo:
        :return:
        """

        asset_shaders_file = asset.get_asset_shaders_file(status=status)
        if not asset_shaders_file:
            LOGGER.warning('No asset shader file found!')
            return False

        shader_names = asset_shaders_file.get_shaders()
        if not shader_names:
            LOGGER.warning('No shaders found for asset: {} | {}!'.format(asset.id, asset.name))
            return False

        asset_shading_shader_mapping = asset_shaders_file.get_shading_group_shader_mapping()
        for shader_grp, shaders_list in asset_shading_shader_mapping.items():
            if shader_grp in ['initialShadingGroup', 'initialParticleSE']:
                continue
            if not tp.Dcc.object_exists(shader_grp):
                LOGGER.warning(
                    'Shading Group "{}" does not exist in current scene. '
                    'Following shaders will not be deleted: "{}"'.format(shader_grp, shaders_list))
                continue
            cns = maya.cmds.listConnections(shader_grp)
            found_meshes = list()
            for cnt in cns:
                cnt_type = maya.cmds.nodeType(cnt, i=True)
                if 'dagNode' in cnt_type:
                    found_meshes.append(cnt)
            if found_meshes:
                LOGGER.warning(
                    'Impossible to clean Shading Group "{}" because it has meshes connected to it: "{}"'.format(
                        found_meshes))
                continue
            shaders_to_delete = list()
            for shader_name in shaders_list:
                if shader_name not in shader_names or shader_name in ['lambert1', 'particleCloud1']:
                    LOGGER.warning('Impossible to clean Shader: "{}"'.format(shader_name))
                    continue
                shaders_to_delete.append(shader_name)

            for shader_name in shaders_to_delete:
                tp.Dcc.delete_object(shader_name)
            tp.Dcc.delete_object(shader_grp)

        asset_operator = '{}_operator'.format(asset.id)
        if tp.Dcc.object_exists(asset_operator):
            LOGGER.info('Removing Asset Operator: {}'.format(asset_operator))
            shape_sets = tp.Dcc.list_source_connections(asset_operator) or list()
            for shape_set in shape_sets:
                if tp.Dcc.object_exists(shape_set):
                    LOGGER.info('Removing Asset Operator "{}" Shape Set: "{}"'.format(asset_operator, shape_set))
                    tp.Dcc.delete_object(shape_set)
            tp.Dcc.delete_object(asset_operator)

    @UNDO_DECORATOR
    def load_scene_shaders(self, status=defines.ArtellaFileStatus.PUBLISHED, apply_shaders=True):
        """
        Loads all shaders of the current assets in the scene
        :param status:
        :param apply_shaders: bool
        :return:
        """

        scene_assets = artellapipe.AssetsMgr().get_scene_assets()
        if not scene_assets:
            LOGGER.warning('Impossible to load shaders because there are no assets in current scene!')
        for asset in scene_assets:

            asset.load_shaders(status=status, apply_shaders=apply_shaders)

    @UNDO_DECORATOR
    def unload_shaders(self, assets=None, status=defines.ArtellaFileStatus.PUBLISHED):
        """
        Unload shaders applied to assets loaded in current DCC scene or to given ones
        :param assets:
        :param status:
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders unloading is only supported in Maya!')
            return

        if assets is None:
            assets = artellapipe.AssetsMgr().get_scene_assets()
        if not assets:
            LOGGER.warning('Impossible to unload shaders because no shaders found in current scene!')

        for asset in assets:
            self.unload_asset_shaders(asset=asset, status=status)

        return True

    def get_asset_shaders(self, asset, return_only_shaders=True, skip_standard_shaders=True):
        """
        Returns list of shaders applied to the given asset
        :param asset: list of dict
        """

        if not asset:
            return

        asset_shaders = dict()
        only_shaders = list()

        renderable_shapes = artellapipe.AssetsMgr().get_asset_renderable_shapes(asset)
        if not renderable_shapes:
            LOGGER.warning('No renderable shapes found in asset: "{}"'.format(asset.get_name()))
            return asset_shaders

        default_scene_shaders = tp.Dcc.default_shaders() or list()

        for shape in renderable_shapes:
            if shape not in asset_shaders:
                asset_shaders[shape] = dict()
            shading_groups = tp.Dcc.list_connections_of_type(shape, connection_type='shadingEngine')
            if not shading_groups:
                shading_groups = ['initialShadingGroup']
            for shading_grp in shading_groups:
                shading_grp_mat = tp.Dcc.list_materials(nodes=tp.Dcc.list_node_connections(shading_grp))
                if skip_standard_shaders:
                    for mat in shading_grp_mat:
                        if mat in default_scene_shaders:
                            continue

                for mat in shading_grp_mat:
                    if mat not in only_shaders:
                        only_shaders.append(mat)
                asset_shaders[shape][shading_grp] = shading_grp_mat

        if not asset_shaders:
            LOGGER.warning('No shaders found in current Asset: {}'.format(asset.get_name()))
            return None

        if return_only_shaders:
            return only_shaders

        return asset_shaders

    def get_asset_shaders_to_export(self, asset, return_only_shaders=True, skip_standard_shaders=True):
        """
        Returns a list shaders that should be exported
        :param asset:
        :param return_only_shaders:
        :param skip_standard_shaders:
        :return:
        """

        shading_file_type = artellapipe.AssetsMgr().get_shading_file_type()
        file_path = asset.get_file(file_type=shading_file_type, status=defines.ArtellaFileStatus.WORKING, fix_path=True)
        valid_open = asset.open_file(file_type=shading_file_type, status=defines.ArtellaFileStatus.WORKING)
        if not valid_open:
            LOGGER.warning('Impossible to open Asset Shading File: {}'.format(file_path))
            return None

        asset_shaders = self.get_asset_shaders(
            asset=asset, return_only_shaders=return_only_shaders, skip_standard_shaders=skip_standard_shaders)

        if not asset_shaders:
            LOGGER.warning('No shaders found in current Asset Shading File: {}'.format(file_path))
            return None

        return asset_shaders

    def export_asset_shaders_mapping(self, asset, publish=False, comment=None, new_version=False):
        """
        Exports shaders mapping of the given asset
        :param asset: ArtellaAsset
        :param publish: bool
        :param comment: str
        :param new_version: bool
        :return: bool
        """

        if not asset:
            return False

        shaders_mapping_file_type = artellapipe.AssetsMgr().get_shaders_mapping_file_type()
        file_path = asset.get_file(
            file_type=shaders_mapping_file_type, status=defines.ArtellaFileStatus.WORKING, fix_path=True)
        if not file_path:
            return False

        shaders_mapping_file_class = artellapipe.FilesMgr().get_file_class(shaders_mapping_file_type)
        if not shaders_mapping_file_class:
            return False

        shaders_mapping_file = shaders_mapping_file_class(asset, file_path=file_path)
        shaders_mapping_file.export_file()

        if new_version:
            if os.path.isfile(file_path):
                artellapipe.FilesMgr().lock_file(file_path)
                valid_upload = artellapipe.FilesMgr().upload_working_version(
                    file_path=file_path, skip_saving=True, comment=comment
                )
                if valid_upload:
                    artellapipe.FilesMgr().unlock_file(file_path, warn_user=False)

        if publish:
            raise NotImplementedError('Export Shader Mapping Publish functionality is not implemented yet!')

    def export_asset_shaders(
            self, asset, publish=False, comment=None, new_version=False, shader_swatch=None, shaders_to_export=None):
        """
        Exports all shaders of the given asset
        :param asset: ArtellaAsset
        :param publish: bool
        :param comment: str, publish comment
        :param new_version: bool
        :param shaders_to_export: list(str)
        :return: bool
        """

        if not asset:
            return False

        if shaders_to_export is None:
            shaders_to_export = list()
        else:
            shaders_to_export = python.force_list(shaders_to_export)

        asset_shaders = self.get_asset_shaders_to_export(asset=asset)
        if not asset_shaders:
            return False

        if shaders_to_export:
            valid_shaders = list()
            for shader_to_export in shaders_to_export:
                if shader_to_export not in asset_shaders:
                    continue
                valid_shaders.append(shader_to_export)
        else:
            valid_shaders = asset_shaders
        if not valid_shaders:
            LOGGER.warning('No valid assets to export for asset: {}!'.format(asset.get_name()))
            return

        shaders_path = asset.get_shaders_path()
        if not os.path.isdir(shaders_path):
            os.makedirs(shaders_path)

        return self.export_shaders(
            shaders_names=valid_shaders, export_path=shaders_path, publish=publish,
            comment=comment, new_version=new_version, asset=asset, shader_swatch=shader_swatch)

    def export_shader(
            self, shader_name, export_path=None, publish=False, comment=None, new_version=False,
            shader_swatch=None, asset=None):
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
        else:
            if not os.path.exists(export_path):
                os.makedirs(export_path)

        if not tp.Dcc.object_exists(shader_name):
            LOGGER.warning('Shader {0} does not exists in the scene! Aborting shader export!'.format(shader_name))
            return None

        shader_file = self.get_shader_file(shader_name, shader_path=export_path, asset=asset)
        if not shader_file:
            LOGGER.warning('Impossible to export shader "{}"!'.format(shader_name))
            return None

        exported_shader = shader_file.export_file(shader_swatch=shader_swatch)
        if not exported_shader:
            LOGGER.warning('Impossible to export shader "{}"'.format(shader_name))
            return None

        if new_version:
            for file_path in exported_shader:
                if os.path.isfile(file_path):
                    artellapipe.FilesMgr().lock_file(file_path)
                    valid_upload = artellapipe.FilesMgr().upload_working_version(
                        file_path=file_path, skip_saving=True, comment=comment
                    )
                    if valid_upload:
                        artellapipe.FilesMgr().unlock_file(file_path, warn_user=False)

        if publish:
            raise NotImplementedError('Export Shader Publish functionality is not implemented yet!')

        return exported_shader

    def export_shaders(
            self, shaders_names, export_path=None, publish=False, comment=None, new_version=False,
            asset=None, shader_swatch=None):
        """
        Exports all given shader names from current scene
        :param shaders_names: list(str)
        :param export_path: STR
        :param publish: bool
        :param comment: str
        :param new_version: bool
        :param asset: ArtellaAsset
        :return: list
        """

        exported_shaders = list()

        if not shaders_names:
            return exported_shaders

        for shader_name in shaders_names:
            exported_shader = self.export_shader(
                shader_name=shader_name, export_path=export_path, publish=publish, comment=comment,
                new_version=new_version, asset=asset, shader_swatch=shader_swatch)
            exported_shaders.append(exported_shader)

        return exported_shaders


@decorators.Singleton
class ArtellaShadersManagerSingleton(ShadersManager, object):
    def __init__(self):
        ShadersManager.__init__(self)


artellapipe.register.register_class('ShadersMgr', ArtellaShadersManagerSingleton)
