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

from solstice.pipeline.tools.outliner.core import outlinertree
from solstice.pipeline.tools.outliner.widgets import items


class SolsticeBaseOutliner(outlinertree.BaseOutliner, object):
    def __init__(self, parent=None):
        super(SolsticeBaseOutliner, self).__init__(parent=parent)

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

    def init_ui(self):
        allowed_types = self.allowed_types()
        assets = sp.get_assets(allowed_types=allowed_types)
        for asset in assets:
            asset_widget = items.OutlinerAssetItem(asset)
            self.append_widget(asset_widget)
            self.widget_tree[asset_widget] = list()

            asset_widget.clicked.connect(self._on_item_clicked)
            asset_widget.viewToggled.connect(self._on_toggle_view)
            # self.callbacks.append(mayautils.MCallbackIdWrapper(asset_widget.add_asset_attributes_change_callback()))

            asset_files = asset.get_asset_files()
            asset_files['artella'] = None
            for cat, file_path in asset_files.items():
                file_widget = self.get_file_widget_by_category(category=cat, parent=asset_widget)
                if file_widget is not None:
                    asset_widget.add_child(file_widget, category=cat)
                    self.widget_tree[asset_widget].append(file_widget)
                    if cat == 'model':
                        file_widget.proxyHiresToggled.connect(self._on_toggle_proxy_hires)
                    elif cat == 'shading':
                        pass
                    elif cat == 'groom':
                        pass
                    elif cat == 'artella':
                        pass

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


class SolsticeAssetsOutliner(SolsticeBaseOutliner, object):

    def __init__(self, parent=None):
        super(SolsticeAssetsOutliner, self).__init__(parent=parent)

    def allowed_types(self):
        return ['prop']

    def add_callbacks(self):
        pass
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MEventMessage.addEventCallback('SelectionChanged', self._on_selection_changed)))
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MEventMessage.addEventCallback('NameChanged', self._on_refresh_outliner)))
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MEventMessage.addEventCallback('SceneOpened', self._on_refresh_outliner)))
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MEventMessage.addEventCallback('SceneImported', self._on_refresh_outliner)))
        # # self.callbacks.append(solstice_maya_utils.MCallbackIdWrapper(OpenMaya.MEventMessage.addEventCallback('Undo', self._on_refresh_outliner)))
        # # self.callbacks.append(solstice_maya_utils.MCallbackIdWrapper(OpenMaya.MEventMessage.addEventCallback('Redo', self._on_refresh_outliner)))
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterNew, self._on_refresh_outliner)))
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterOpen, self._on_refresh_outliner)))
        # self.callbacks.append(mayautils.MCallbackIdWrapper(OpenMaya.MDGMessage.addNodeRemovedCallback(self._on_refresh_outliner)))

class SolsticeCharactersOutliner(SolsticeBaseOutliner, object):
    def __init__(self, parent=None):
        super(SolsticeCharactersOutliner, self).__init__(parent=parent)

    def allowed_types(self):
        return ['character']


class SolsticeLightsOutliner(SolsticeBaseOutliner, object):
    def __init__(self, parent=None):
        super(SolsticeLightsOutliner, self).__init__(parent=parent)


class SolsticeCamerasOutliner(SolsticeBaseOutliner, object):
    def __init__(self, parent=None):
        super(SolsticeCamerasOutliner, self).__init__(parent=parent)


class SolsticeFXOutliner(SolsticeBaseOutliner, object):
    def __init__(self, parent=None):
        super(SolsticeFXOutliner, self).__init__(parent=parent)
