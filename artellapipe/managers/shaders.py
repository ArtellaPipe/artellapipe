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

import tpDcc as tp
from tpDcc.libs.python import decorators, python, path as path_utils

import artellapipe
from artellapipe.core import defines

if tp.is_maya():
    import tpDcc.dccs.maya as maya
    from tpDcc.dccs.maya.core import decorators as maya_decorators
    UNDO_DECORATOR = maya_decorators.undo_chunk
else:
    UNDO_DECORATOR = decorators.empty_decorator

LOGGER = logging.getLogger('artellapipe')


class ShadersManager(object):

    _config = None

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tp.ConfigsMgr().get_config(
                config_name='artellapipe-shaders',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    def get_shaders_path_file_type(self):
        """
        Returns file type used to define shaders
        :return: str
        """

        return self.config.get('path_file_type', default='shaders')

    def get_shaders_asset_file_type(self):
        """
        Returns file type used to define asset shaders
        :return: str
        """

        return self.config.get('file_type', default='shader')

    def get_shaders_extensions(self):
        """
        Returns extension used for shaders in current project
        :return: str
        """

        shaders_file_type = self.get_shaders_asset_file_type()
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

    def get_asset_shader_file_class(self):
        """
        Returns asset shader file class associated to this asset
        :return: class
        """
        asset_shaders_file_type = self.get_shaders_asset_file_type()
        if not asset_shaders_file_type:
            LOGGER.warning('No Asset Shaders file type available!')
            return None

        asset_shader_file_class = artellapipe.FilesMgr().get_file_class(asset_shaders_file_type)
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

        if not asset:
            if not shader_path:
                shaders_paths = self.get_shaders_paths()
                if not shaders_paths:
                    LOGGER.warning('Impossible to return shader file path because no shaders path are defined')
                    return
            else:
                shaders_paths = python.force_list(shader_path)
        else:
            shaders_paths = list()

        if asset:
            shaders_asset_file_type = self.get_shaders_asset_file_type()
            if not shaders_asset_file_type:
                LOGGER.warning('Impossible to return shader asset file path because shader file type is not defined!')
                return

            shader_asset_file_class = artellapipe.FilesMgr().get_file_class(shaders_asset_file_type)
            if not shader_asset_file_class:
                LOGGER.warning(
                    'Impossible to get shader path: {} | {} | {}'.format(
                        shader_name, shaders_paths, shaders_asset_file_type))
                return

            shader_file = shader_asset_file_class(shader_name=shader_name, asset=asset)
            return shader_file

        else:
            raise NotImplementedError('Library Shader File is not implemented!')
            # shaders_file_type = self.get_shaders_file_type()
            # if not shaders_file_type:
            #     LOGGER.warning('Impossible to return shader file path because shader file type is not defined!')
            #     return
            #
            # shader_file_class = artellapipe.FilesMgr().get_file_class(shaders_file_type)
            # if not shader_file_class:
            #     LOGGER.warning(
            #         'Impossible to get shader path: {} | {} | {}'.format(
            #         shader_name, shaders_paths, shaders_file_type))
            #     return
            #
            # for shader_path in shaders_paths:
            #     shader_file = shader_file_class(artellapipe.project, shader_name, file_path=shader_path)
            #     shader_file_paths = shader_file.get_file_paths()
            #     if shader_path:
            #         return shader_file
            #     else:
            #         for shader_file_path in shader_file_paths:
            #             if os.path.isfile(shader_file_path):
            #                 return shader_file

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

    def load_shader(self,
                    shader_name, shader_path=None, asset=None, apply=True, status=defines.ArtellaFileStatus.WORKING):
        """
        Loads shader with given name in current DCC
        :param shader_name: str
        :param apply: bool
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders loading is only supported in Maya!')
            return

        from tpDcc.dccs.maya.core import shader as maya_shader

        if shader_name in maya_shader.get_default_shaders():
            return True

        if apply:
            all_panels = maya.cmds.getPanel(type='modelPanel')
            for p in all_panels:
                maya.cmds.modelEditor(p, edit=True, displayTextures=False)

        shader_file = self.get_shader_file(shader_name, asset=asset)
        if shader_file:
            shader_file.import_file(status=status)
        else:
            valid_shaders_paths = list()
            shader_library_paths = self.get_shaders_paths()
            for p in shader_library_paths:
                if not os.path.exists(p):
                    continue
                valid_shaders_paths.append(p)
            if not valid_shaders_paths:
                LOGGER.debug(
                    '{} Shaders Library folder is not synchronized in your PC. Synchronize it please!'.format(
                        artellapipe.project.name.title()))
                return False
            shader_file = self.get_shader_file(shader_name, shader_path=shader_path)
            if not shader_file:
                LOGGER.warning('Impossible to load shader "{}"!'.format(shader_name))
                return
            else:
                shader_file.import_file()

        return True

    def load_asset_shaders(self, asset_node, apply_shaders=True, status=defines.ArtellaFileStatus.PUBLISHED):
        """
        Loads all the shaders of the given asset
        :param asset_node:
        :param apply_shaders: bool
        :param status:
        """

        if not tp.is_maya():
            LOGGER.warning('Load Asset Shaders functionality is only available in Maya')
            return False

        shaders_mapping_file = asset_node.get_asset_shaders_mapping_file()
        if not shaders_mapping_file:
            LOGGER.warning('No asset shader mapping file found!')
            return False

        shader_names = shaders_mapping_file.get_shaders(status=status)
        if not shader_names:
            LOGGER.warning('No shaders to load found! ({})'.format(status))
            return False

        if apply:
            scene_operator = artellapipe.Arnold().get_scene_operator()
            if not tp.Dcc.object_exists(scene_operator):
                LOGGER.warning('No Scene Operator found in current scene!')
                return False

        asset_shading_geo_mapping = shaders_mapping_file.get_shading_geometry_mapping()
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
                new_shape = '{}:{}'.format(asset_node.id, new_shape)
                updated_shapes[shape] = new_shape

        for shader_name in shader_names:
            if not tp.Dcc.object_exists(shader_name):
                valid_load = self.load_shader(shader_name, asset=asset_node.asset, apply=apply, status=status)
                if not valid_load:
                    LOGGER.warning('Something went wrong when loading Shader "{}"'.format(shader_name))
                    continue

        if apply_shaders:
            asset_operator_node = asset_node.get_asset_operator()
            if not asset_operator_node or not tp.Dcc.object_exists(asset_operator_node):
                asset_operator_node = asset_node.create_operator_node()

            if not asset_operator_node:
                return False

            for i, (original_shape, updated_shape) in enumerate(updated_shapes.items()):
                shaders_to_apply = asset_shading_geo_mapping[original_shape]
                asset_shape_operator = asset_node.get_shape_operator(updated_shape)
                if not asset_shape_operator:
                    asset_shape_operator = asset_node.create_shape_operator(updated_shape)
                    if not asset_shape_operator:
                        LOGGER.warning(
                            'Impossible to create Asset Shape Operator for "{} | {}"'.format(
                                asset_node.id, updated_shape))
                        return False

                for j, shader_to_apply in enumerate(shaders_to_apply):
                    if not tp.Dcc.object_exists(shader_to_apply):
                        continue
                    shader_type = tp.Dcc.node_type(shader_to_apply)
                    if shader_type == 'displacementShader':
                        asset_node.add_shape_operator_assignment(
                            shape_name=updated_shape, assignment_value="displacement = '{}'".format(shader_to_apply))
                    else:
                        asset_node.add_shape_operator_assignment(
                            shape_name=updated_shape, assignment_value="shader = '{}'".format(shader_to_apply))

        return True

    def unload_asset_shaders(self, asset_node):
        """
        Unload shaders of given asset
        :param asset_node:
        :param status:
        :return:
        """

        if not tp.is_maya():
            LOGGER.warning('Unload Asset Shaders functionality is only available in Maya')
            return False

        from tpDcc.dccs.maya.core import attribute

        shaders_mapping_file = asset_node.get_asset_shaders_mapping_file()
        if not shaders_mapping_file:
            LOGGER.warning('No asset shader mapping file found!')
            return False

        shader_names = shaders_mapping_file.get_shaders(force=True, status=defines.ArtellaFileStatus.PUBLISHED)
        working_shader_names = shaders_mapping_file.get_shaders(force=True, status=defines.ArtellaFileStatus.WORKING)
        for working_shader_name in working_shader_names:
            if working_shader_name not in shader_names:
                shader_names.append(working_shader_name)
        if not shader_names:
            LOGGER.warning('No shaders to unload found!')
            return False

        # We clean shape operators
        # asset_operator = '{}_operator'.format(asset.id)
        # if tp.Dcc.object_exists(asset_operator):
        #     LOGGER.info('Removing Asset Operator: {}'.format(asset_operator))
        #     shape_sets = tp.Dcc.list_source_connections(asset_operator) or list()
        #     for shape_set in shape_sets:
        #         if tp.Dcc.object_exists(shape_set):
        #             LOGGER.info('Removing Asset Operator "{}" Shape Set: "{}"'.format(asset_operator, shape_set))
        #             tp.Dcc.delete_object(shape_set)
        #     tp.Dcc.delete_object(asset_operator)

        found_shaders = list()
        arnold_set_parameters = tp.Dcc.list_nodes(node_type='aiSetParameter')
        asset_shading_shader_mapping = shaders_mapping_file.get_shading_group_shader_mapping()
        for shader_grp, shaders_list in asset_shading_shader_mapping.items():
            # We check if shaders are being applied in other assets. If so, we skip the deletion of the shaders
            for shader_name in shaders_list:
                for set_node in arnold_set_parameters:
                    indices = attribute.multi_index_list('{}.assignment'.format(set_node)) or list()
                    for index in indices:
                        assign_value = tp.Dcc.get_attribute_value(set_node, 'assignment[{}]'.format(index))
                        if assign_value and shader_name in assign_value:
                            if not tp.Dcc.attribute_exists(set_node, 'asset_id'):
                                continue
                            set_asset_id = tp.Dcc.get_attribute_value(set_node, 'asset_id')
                            if set_asset_id != asset_node.id:
                                continue
                            if not tp.Dcc.attribute_exists(set_node, 'asset_shape'):
                                continue
                            asset_shape = tp.Dcc.get_attribute_value(set_node, 'asset_shape')
                            valid_remove = asset_node.remove_shape_operator_assignment(
                                assign_value, shape_name=asset_shape)
                            if valid_remove:
                                removed_shader = assign_value.split(' = ')[-1].replace("'", '')
                                if removed_shader not in found_shaders:
                                    found_shaders.append(removed_shader)
                    set_empty = True
                    indices = attribute.multi_index_list('{}.assignment'.format(set_node)) or list()
                    for index in indices:
                        assign_value = tp.Dcc.get_attribute_value(set_node, 'assignment[{}]'.format(index))
                        if assign_value != '' and assign_value is not None:
                            set_empty = False
                    if set_empty:
                        tp.Dcc.delete_object(set_node)

            shaders_to_remove = found_shaders[:]
            arnold_set_parameters = tp.Dcc.list_nodes(node_type='aiSetParameter')
            for set_node in arnold_set_parameters:
                indices = attribute.multi_index_list('{}.assignment'.format(set_node)) or list()
                for index in indices:
                    assign_value = tp.Dcc.get_attribute_value(set_node, 'assignment[{}]'.format(index))
                    for found_shader in found_shaders:
                        if found_shader in assign_value:
                            shaders_to_remove.pop(shaders_to_remove.index(found_shader))

            for shader_to_remove in shaders_to_remove:
                tp.Dcc.delete_object(shader_to_remove)

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
    def unload_shaders(self, asset_nodes=None):
        """
        Unload shaders applied to assets loaded in current DCC scene or to given ones
        :param assets:
        """

        if not tp.is_maya():
            LOGGER.warning('Shaders unloading is only supported in Maya!')
            return

        if asset_nodes is None:
            asset_nodes = artellapipe.AssetsMgr().get_scene_assets()
        if not asset_nodes:
            LOGGER.warning('Impossible to unload shaders because no shaders found in current scene!')

        for asset in asset_nodes:
            self.unload_asset_shaders(asset_node=asset)

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

        renderable_shapes = artellapipe.AssetsMgr().get_asset_renderable_shapes(asset, full_path=False)
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

    def export_asset_shaders_mapping(self, asset, comment=None, new_version=False):
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

    def export_asset_shaders(
            self, asset, comment=None, new_version=False, shader_swatch=None, shaders_to_export=None):
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

        shaders_path = asset.get_shaders_path(status=defines.ArtellaFileStatus.WORKING)
        if not shaders_path:
            return

        if not os.path.isdir(shaders_path):
            os.makedirs(shaders_path)

        return self.export_shaders(
            shaders_names=valid_shaders, export_path=shaders_path, comment=comment,
            new_version=new_version, asset=asset, shader_swatch=shader_swatch)

    def export_shader(
            self, shader_name, export_path=None, comment=None, new_version=False, shader_swatch=None, asset=None):
        """
        Exports shaders
        :param shader_name: str, name of the shader to export
        :param export_path: str, path where shader file will be exported into (optional)
        :param comment: str, publish comment
        :param shader_swatch: str, path where shader file will be exported into (optional)
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

        exported_shader = shader_file.export_file(shader_swatch=shader_swatch, status=defines.ArtellaFileStatus.WORKING)
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

        return exported_shader

    def export_shaders(
            self, shaders_names, export_path=None, comment=None, new_version=False, asset=None, shader_swatch=None):
        """
        Exports all given shader names from current scene
        :param shaders_names: list(str)
        :param export_path: STR
        :param publish: bool
        :param comment: str
        :param new_version: bool
        :param asset: ArtellaAsset
        :param shader_swatch:
        :return: list
        """

        exported_shaders = list()

        if not shaders_names:
            return exported_shaders

        for shader_name in shaders_names:
            exported_shader = self.export_shader(
                shader_name=shader_name, export_path=export_path, comment=comment,
                new_version=new_version, asset=asset, shader_swatch=shader_swatch)
            exported_shaders.append(exported_shader)

        return exported_shaders
