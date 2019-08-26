#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different outliners for Artella Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *

import tpDccLib as tp

import artellapipe
from artellapipe.tools.outliner.core import outlinertree
from artellapipe.tools.outliner.widgets import items


class BaseOutliner(outlinertree.OutlinerTree, object):
    """
    Base class to create outliners
    """

    OUTLINER_ITEM = items.OutlinerAssetItem

    def __init__(self, project, parent=None):
        super(BaseOutliner, self).__init__(project=project, parent=parent)

    def _init(self):
        assets = self._project.get_scene_assets(allowed_types=self.ALLOWED_TYPES)
        for asset in assets:
            asset_widget = self.OUTLINER_ITEM(asset)
            asset_widget.overrideAdded.connect(self._on_override_added)
            asset_widget.overrideRemoved.connect(self._on_override_removed)
            asset_widget.removed.connect(self._on_asset_removed)
            self.append_widget(asset_widget)
            self._widget_tree[asset_widget] = list()

            asset_widget.clicked.connect(self._on_item_clicked)
            asset_widget.viewToggled.connect(self._on_toggle_view)

            overrides = asset.get_overrides()
            if overrides:
                for override in overrides:
                    self._add_override(override=override, parent=asset_widget)

        #     # self.callbacks.append(mayautils.MCallbackIdWrapper(asset_widget.add_asset_attributes_change_callback()))
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

    def _add_override(self, override, parent):
        """
        Internal function that appends given override widget into the parent asset item widget
        :param override: OverrideAssetItem
        :param parent: OutlinerAssetItem
        """

        override_widget = items.OutlinerOverrideItem(override=override, parent=parent)
        override_widget.removed.connect(partial(self._on_override_removed, override, parent))
        parent.add_child(override_widget, name=override.OVERRIDE_NAME)

    def _on_item_clicked(self, widget, event):
        if widget is None:
            artellapipe.logger.warning('Selected Asset is not valid!')
            return

        asset_name = widget.asset_node.name
        item_state = widget.is_selected
        if tp.Dcc.object_exists(asset_name):
            is_modified = event.modifiers() == Qt.ControlModifier
            if not is_modified:
                tp.Dcc.clear_selection()

            for asset_widget, file_items in self._widget_tree.items():
                if asset_widget != widget:
                    if is_modified:
                        if not asset_widget.is_selected:
                            asset_widget.deselect()
                    else:
                        asset_widget.deselect()
                else:
                    if is_modified and widget.is_selected:
                        asset_widget.select()
                        tp.Dcc.select_object(asset_widget.asset_node.name, add=True)

                    # else:
                    #     print('deslecting ...')
                    #     asset_widget.deselect()
                    #     tp.Dcc.clear_selection()
                        # tp.Dcc.deselect_object(asset_widget.asset_node.name)

            widget.set_select(item_state)
            if not is_modified:
                tp.Dcc.select_object(asset_name)
        else:
            self._on_refresh_outliner()

    def _on_toggle_view(self, widget):
        node_name = widget.asset_node.node
        if tp.Dcc.object_exists(node_name):
            # main_control = widget.asset_node.get_main_control()
            # if main_control:
            #     if not tp.Dcc.object_exists(main_control):
            #         return
            # if not main_control or not cmds.objExists(main_control):
            #     if state:
            #
            #     return

            if tp.Dcc.node_is_visible(node_name):
                tp.Dcc.hide_object(node_name)
                widget.display_buttons.hide()
            else:
                tp.Dcc.show_object(node_name)
                widget.display_buttons.show()

    def _on_override_added(self, override, parent):
        self._add_override(override=override, parent=parent)
        parent.expand()
        
    def _on_override_removed(self, override, parent):
        parent.remove_child(override.OVERRIDE_NAME)

    def _on_asset_removed(self, widget):
        self.remove_widget(widget)


