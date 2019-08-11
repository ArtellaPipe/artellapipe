#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains outliner item core widgets for Solstice
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import decorators

import tpDccLib as tp

import artellapipe

from solstice.pipeline.tools.outliner.core import outlineritems, buttons
from solstice.pipeline.tools.outliner.widgets import buttons as solstice_buttons

if tp.is_maya():
    from tpMayaLib.core import decorators as maya_decorators
    undo_decorator = maya_decorators.undo_chunk
else:
    undo_decorator = decorators.empty_decorator


class OutlinerAssetItem(outlineritems.OutlinerAssetItem, object):
    viewToggled = Signal(QObject, bool)
    viewSolo = Signal(QObject, bool)

    def __init__(self, asset, parent=None):
        super(OutlinerAssetItem, self).__init__(asset=asset, parent=parent)

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

    def create_menu(self, menu):
        replace_menu = QMenu('Replace by', self)
        menu.addMenu(replace_menu)
        replace_abc = replace_menu.addAction('Alembic')
        replace_rig = replace_menu.addAction('Rig')
        replace_standin = replace_menu.addAction('Standin')
        remove_act = menu.addAction('Delete')
        menu.addSeparator()
        sync_shaders_act = menu.addAction('Sync Shaders')
        unload_shaders_act = menu.addAction('Unload Shaders')

        replace_abc.triggered.connect(self._on_replace_alembic)
        replace_rig.triggered.connect(self._on_replace_rig)
        sync_shaders_act.triggered.connect(self._on_sync_shaders)
        unload_shaders_act.triggered.connect(self._on_unload_shaders)

    def is_rig(self):
        """
        Returns whether current asset is a rig or not
        :return: bool
        """

        valid_tag_data = False
        main_group_connections = tp.Dcc.list_source_connections(node=self.asset.node)
        for connection in main_group_connections:
            attrs = tp.Dcc.list_user_attributes(node=connection)
            if attrs and type(attrs) == list:
                for attr in attrs:
                    if attr == 'tag_type':
                        valid_tag_data = True
                        break

        return valid_tag_data

    def is_alembic(self):
        """
        Returns whether current asset is an alembic or not
        :return: bool
        """

        valid_tag_data = False
        main_group_connections = tp.Dcc.list_source_connections(node=self.asset.node)
        for connection in main_group_connections:
            attrs = tp.Dcc.list_user_attributes(node=connection)
            if attrs and type(attrs) == list:
                for attr in attrs:
                    if attr == 'tag_info':
                        valid_tag_data = True
                        break

        return valid_tag_data

    def is_standin(self):
        """
        Returns whether current asset is an standin or not
        :return: bool
        """

        pass

    @undo_decorator
    def _on_replace_alembic(self):
        abc_file = self.asset.get_alembic_files()
        is_referenced = tp.Dcc.node_is_referenced(self.asset.node)
        if is_referenced:
            if self.is_rig():
                main_group_connections = tp.Dcc.list_source_connections(node=self.asset.node)
                for connection in main_group_connections:
                    attrs = tp.Dcc.list_user_attributes(node=connection)
                    if attrs and type(attrs) == list:
                        if 'root_ctrl' not in attrs:
                            artellapipe.solstice.logger.warning('Asset Rig is not ready for replace functionality yet!')
                            return
                        print('come onnnn')

                # ref_node = sys.solstice.dcc.reference_node(self.asset.node)
                # if not ref_node:
                #     return
                # sys.solstice.dcc.unload_reference(ref_node)
            elif self.is_standin():
                pass
            else:
                artellapipe.solstice.logger.warning('Impossible to replace {} by Alembic!'.format(self.name))
        else:
            artellapipe.solstice.logger.warning('Imported asset cannot be replaced!')

        # if self.asset.node != hires_group:
        #     is_referenced = cmds.referenceQuery(asset.node, isNodeReferenced=True)
        #     if is_referenced:
        #         namespace = cmds.referenceQuery(asset.node, namespace=True)
        #         if not namespace or not namespace.startswith(':'):
        #             sys.solstice.logger.error('Node {} has not a valid namespace!. Please contact TD!'.format(asset.node))
        #             continue
        #         else:
        #             namespace = namespace[1:] + ':'

    def _on_replace_rig(self):
        is_referenced = tp.Dcc.node_is_referenced(self.asset.node)
        if not is_referenced:
            valid_refs = True
            children = tp.Dcc.node_children(self.asset.node, all_hierarchy=False, full_path=True)
            for child in children:
                is_child_ref = tp.Dcc.node_is_referenced(child)
                if not is_child_ref:
                    valid_refs = False
                    break
            if not valid_refs:
                artellapipe.solstice.logger.warning('Impossible to replace {} by rig file ...'.format(self.asset.node))
                return
            rig_ref = self.asset.reference_asset_file('rig')
            print(rig_ref)

    def _on_sync_shaders(self):
        self.asset.sync_shaders()

    def _on_unload_shaders(self):
        self.asset.unload_shaders()


class OutlinerModelItem(outlineritems.OutlinerFileItem, object):

    proxyHiresToggled = Signal(QObject, int)

    def __init__(self, parent=None):
        super(OutlinerModelItem, self).__init__(category='model', parent=parent)

    @staticmethod
    def get_category_pixmap():
        return artellapipe.solstice.resource.pixmap('cube', category='icons').scaled(18, 18, Qt.KeepAspectRatio)

    def custom_ui(self):
        super(OutlinerModelItem, self).custom_ui()

        self.model_buttons = solstice_buttons.ModelDisplayButtons()
        self.item_layout.addWidget(self.model_buttons, 0, 3, 1, 1)

    # def setup_signals(self):
    #     self.model_buttons.proxy_hires_cbx.currentIndexChanged.connect(partial(self.proxyHiresToggled.emit, self))


class OutlinerShadingItem(outlineritems.OutlinerFileItem, object):
    def __init__(self, parent=None):
        super(OutlinerShadingItem, self).__init__(category='shading', parent=parent)

    @staticmethod
    def get_category_pixmap():
        return artellapipe.solstice.resource.pixmap('shader', category='icons').scaled(18, 18, Qt.KeepAspectRatio)


class OutlinerGroomItem(outlineritems.OutlinerFileItem, object):
    def __init__(self, parent=None):
        super(OutlinerGroomItem, self).__init__(category='groom', parent=parent)


class OutlinerArtellaItem(outlineritems.OutlinerFileItem, object):
    def __init__(self, parent=None):
        super(OutlinerArtellaItem, self).__init__(category='artella', parent=parent)

    @staticmethod
    def get_category_pixmap():
        return artellapipe.solstice.resource.pixmap('artella', category='icons').scaled(18, 18, Qt.KeepAspectRatio)

