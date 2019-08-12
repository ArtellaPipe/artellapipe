#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different outliners for Solstice Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp

from artellapipe.tools.outliner.core import outlinertree
from artellapipe.tools.outliner.widgets import items


class BaseOutliner(outlinertree.OutlinerTree, object):
    """
    Base class to create outliners
    """

    OUTLINER_ITEM = items.OutlinerAssetItem

    def __init__(self, project, parent=None):
        super(BaseOutliner, self).__init__(project=project, parent=parent)

    @staticmethod
    def get_file_widget_by_category(category, parent=None):
        if category == 'model':
            file_widget = items.OutlinerModelItem(parent=parent)
        elif category == 'shading':
            file_widget = items.OutlinerShadingItem(parent=parent)
        elif category == 'groom':
            file_widget = items.OutlinerGroomItem(parent=parent)
        elif category == 'artella':
            file_widget = items.OutlinerArtellaItem(parent=parent)
        else:
            return None

        return file_widget

    def _init(self):
        assets = self._project.get_scene_assets(allowed_types=self.ALLOWED_TYPES)
        for asset in assets:
            asset_widget = self.OUTLINER_ITEM(asset)
            self.append_widget(asset_widget)
            self._widget_tree[asset_widget] = list()

        #     asset_widget.clicked.connect(self._on_item_clicked)
        #     asset_widget.viewToggled.connect(self._on_toggle_view)
        #     # self.callbacks.append(mayautils.MCallbackIdWrapper(asset_widget.add_asset_attributes_change_callback()))
        #
        #     asset_files = asset.get_asset_files()
        #     asset_files['artella'] = None
        #     for cat, file_path in asset_files.items():
        #         file_widget = self.get_file_widget_by_category(category=cat, parent=asset_widget)
        #         if file_widget is not None:
        #             asset_widget.add_child(file_widget, category=cat)
        #             self._widget_tree[asset_widget].append(file_widget)
        #             if cat == 'model':
        #                 file_widget.proxyHiresToggled.connect(self._on_toggle_proxy_hires)
        #             elif cat == 'shading':
        #                 pass
        #             elif cat == 'groom':
        #                 pass
        #             elif cat == 'artella':
        #                 pass

    def _on_toggle_view(self, widget, state):
        node_name = widget.asset.node
        if tp.Dcc.object_exists(node_name):
            main_control = widget.asset.get_main_control()
            if main_control:
                if not tp.Dcc.object_exists(main_control):
                    return
            # if not main_control or not cmds.objExists(main_control):
            #     if state:
            #
            #     return
            if state is True:
                cmds.showHidden(node_name)
            else:
                cmds.hide(node_name)

    def _on_toggle_proxy_hires(self, widget, item_index):
        node_name = widget.parent.asset.node
        if tp.Dcc.object_exists(node_name):
            if tp.Dcc.attribute_exists(node=node_name, attribute_name='type'):
                widget.parent.block_callbacks = True
                try:
                    tp.Dcc.set_integer_attribute_value(node=node_name, attribute_name='type', attribute_value=item_index)
                except Exception:
                    widget.parent.block_callbacks = False
                widget.parent.block_callbacks = False





