#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains outliner item core widgets for Solstice
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import decorators

import tpDccLib as tp

import artellapipe

from artellapipe.tools.outliner.core import outlineritems, buttons

if tp.is_maya():
    from tpMayaLib.core import decorators as maya_decorators
    undo_decorator = maya_decorators.undo_chunk
else:
    undo_decorator = decorators.empty_decorator


class OutlinerAssetItem(outlineritems.OutlinerAssetItem, object):

    DISPLAY_BUTTONS = buttons.AssetDisplayButtons

    viewToggled = Signal(QObject, bool)
    viewSolo = Signal(QObject, bool)

    def __init__(self, asset_node, parent=None):
        super(OutlinerAssetItem, self).__init__(asset_node=asset_node, parent=parent)

    def get_display_widget(self):
        return buttons.AssetDisplayButtons()

    def add_asset_attributes_change_callback(self):
        pass
        # obj = self.asset.get_mobject()
        # vis_callback = OpenMaya.MNodeMessage.addAttributeChangedCallback(obj, partial(self._update_asset_attributes))
        # return vis_callback

    def _update_asset_attributes(self, msg, plug, otherplug, *client_data):
        pass

        # if self.block_callbacks is False:
        #     if msg & OpenMaya.MNodeMessage.kAttributeSet:
        #         if 'visibility' in plug.name():
        #             self.asset_buttons.view_btn.setChecked(plug.asBool())
        #         elif 'type' in plug.name():
        #             model_widget = self.get_file_widget(category='model')
        #             if model_widget is None:
        #                 sys.solstice.logger.warning('Impossible to update type attribute because model wigdet is available!')
        #                 return
        #             model_widget.model_buttons.proxy_hires_cbx.setCurrentIndex(plug.asInt())

    def _create_replace_actions(self, replace_menu):
        # replace_abc = replace_menu.addAction('Alembic')
        # replace_rig = replace_menu.addAction('Rig')
        # replace_standin = replace_menu.addAction('Standin')
        # replace_abc.triggered.connect(self._on_replace_alembic)
        # replace_rig.triggered.connect(self._on_replace_rig)

        return False

    def _create_menu(self, menu):

        replace_icon = artellapipe.resource.icon('replace')
        delete_icon = artellapipe.resource.icon('delete')
        load_shaders_icon = artellapipe.resource.icon('shading_load')
        unload_shaders_icon = artellapipe.resource.icon('shading_unload')

        replace_menu = QMenu('Replace by', self)
        replace_menu.setIcon(replace_icon)
        show_replace_menu = self._create_replace_actions(replace_menu)
        if show_replace_menu:
            menu.addMenu(replace_menu)

        remove_action = QAction(delete_icon, 'Delete', menu)
        menu.addAction(remove_action)
        menu.addSeparator()

        load_shaders_action = QAction(load_shaders_icon, 'Load Shaders', menu)
        unload_shaders_action = QAction(unload_shaders_icon, 'Unload Shaders', menu)
        menu.addAction(load_shaders_action)
        menu.addAction(unload_shaders_action)

        load_shaders_action.triggered.connect(self._on_sync_shaders)
        unload_shaders_action.triggered.connect(self._on_unload_shaders)

    def _on_sync_shaders(self):
        self._asset_node.sync_shaders()

    def _on_unload_shaders(self):
        self._asset_node.unload_shaders()
