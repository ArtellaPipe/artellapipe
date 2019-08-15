import pyblish.api

import artellapipe


class CollectAssetsPlugin(pyblish.api.ContextPlugin):

    label = 'Collect assets'
    order = pyblish.api.CollectorOrder
    hosts = ['maya']

    def process(self, context):

        project = None
        for name, value in artellapipe.__dict__.items():
            if name == 'project':
                project = value
                break

        context.data['project'] = project

        assert project, 'Project not found'

        asset_nodes = project.get_scene_assets()
        for asset_node in asset_nodes:
            tag_node = asset_node.get_tag_node()
            if not tag_node:
                continue

            tag_types = tag_node.get_types()
            if not tag_types:
                continue
            tag_types_split = tag_types.split()
            if not tag_types_split:
                continue

            for tag_type in tag_types_split:
                instance = context.create_instance(asset_node.name)
                instance.data['node'] = asset_node
                instance.data['family'] = tag_type
