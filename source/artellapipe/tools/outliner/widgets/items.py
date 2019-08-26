#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains outliner item core widgets for Artella Outliner
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import decorators

import tpDccLib as tp

from tpQtLib.widgets import splitters

import artellapipe

from artellapipe.tools.outliner.core import outlineritems, buttons
from artellapipe.tools.shotmanager.core import shotassembler

if tp.is_maya():
    from tpMayaLib.core import decorators as maya_decorators
    undo_decorator = maya_decorators.undo_chunk
else:
    undo_decorator = decorators.empty_decorator


class OutlinerAssetItem(outlineritems.OutlinerItem, object):

    DISPLAY_BUTTONS = buttons.AssetDisplayButtons

    viewToggled = Signal(object)
    viewSolo = Signal(object, bool)
    removed = Signal(object)
    overrideAdded = Signal(object, object)
    overrideRemoved = Signal(object, object)

    def __init__(self, asset_node, parent=None):
        super(OutlinerAssetItem, self).__init__(asset_node=asset_node, parent=parent)

    def get_display_widget(self):
        return buttons.AssetDisplayButtons()

    def setup_signals(self):
        super(OutlinerAssetItem, self).setup_signals()

        if self._display_buttons:
            self._display_buttons.view_btn.clicked.connect(partial(self.viewToggled.emit, self))

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
        #                 artellapipe.logger.warning('Impossible to update type attribute because model wigdet is available!')
        #                 return
        #             model_widget.model_buttons.proxy_hires_cbx.setCurrentIndex(plug.asInt())

    def _create_replace_actions(self, replace_menu):
        # replace_abc = replace_menu.addAction('Alembic')
        # replace_rig = replace_menu.addAction('Rig')
        # replace_standin = replace_menu.addAction('Standin')
        # replace_abc.triggered.connect(self._on_replace_alembic)
        # replace_rig.triggered.connect(self._on_replace_rig)

        return False

    def _create_add_override_menu(self, menu):
        """
        Internal function that creates the add override menu
        :param menu: QMenu
        :return: bool
        """

        registered_overrides = shotassembler.ShotAssembler.registered_overrides()
        if not registered_overrides:
            return False

        for override_name, override in registered_overrides.items():
            override_action = QAction(override.OVERRIDE_ICON, override.OVERRIDE_NAME, menu)
            if self._asset_node.has_override(override):
                override_action.setEnabled(False)
                override_action.setText('{} | Already added!'.format(override_action.text()))
            override_action.triggered.connect(partial(self._on_add_override, override))
            menu.addAction(override_action)

        return True

    def _create_remove_override_menu(self, menu):
        """
        Internal that creates the remove overrides menu
        :param menu: QMenu
        :return: bool
        """

        node_overrides = self._asset_node.get_overrides()
        if not node_overrides:
            return False

        for override in node_overrides:
            override_action = QAction(override.OVERRIDE_ICON, override.OVERRIDE_NAME, menu)
            override_action.triggered.connect(partial(self._on_remove_override, override))
            menu.addAction(override_action)

        return True

    def _create_save_override_menu(self, menu):
        """
        Internal function that reates the save overrides menu
        :param menu: QMenu
        :return: bool
        """

        node_overrides = self._asset_node.get_overrides()
        if not node_overrides:
            return False

        added_overrides = list()
        for override in node_overrides:
            override_action = QAction(override.OVERRIDE_ICON, override.OVERRIDE_NAME, menu)
            override_action.triggered.connect(partial(self._on_save_override, override))
            added_overrides.append(override_action)
            menu.addAction(override_action)

        if len(added_overrides) > 0:
            menu.addSeparator()
            save_all_overrides_action = QAction(artellapipe.resource.icon('save'), 'All', menu)
            save_all_overrides_action.triggered.connect(self._on_save_all_overrides)
            menu.addAction(save_all_overrides_action)

        return True

    def _create_menu(self, menu):

        replace_icon = artellapipe.resource.icon('replace')
        delete_icon = artellapipe.resource.icon('delete')
        override_add_icon = artellapipe.resource.icon('override_add')
        override_delete_icon = artellapipe.resource.icon('override_delete')
        override_export_icon = artellapipe.resource.icon('save')
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

        add_override_menu = QMenu('Add Override', menu)
        add_override_menu.setIcon(override_add_icon)
        valid_override = self._create_add_override_menu(add_override_menu)
        if valid_override:
            menu.addMenu(add_override_menu)

        remove_override_menu = QMenu('Remove Override', menu)
        remove_override_menu.setIcon(override_delete_icon)
        has_overrides = self._create_remove_override_menu(remove_override_menu)
        if has_overrides:
            menu.addMenu(remove_override_menu)

        save_override_menu = QMenu('Save Overrides', menu)
        save_override_menu.setIcon(override_export_icon)
        export_overrides = self._create_save_override_menu(save_override_menu)
        if export_overrides:
            menu.addMenu(save_override_menu)

        if valid_override or has_overrides or export_overrides:
            menu.addSeparator()

        load_shaders_action = QAction(load_shaders_icon, 'Load Shaders', menu)
        unload_shaders_action = QAction(unload_shaders_icon, 'Unload Shaders', menu)
        menu.addAction(load_shaders_action)
        menu.addAction(unload_shaders_action)

        remove_action.triggered.connect(self._on_remove)
        load_shaders_action.triggered.connect(self._on_load_shaders)
        unload_shaders_action.triggered.connect(self._on_unload_shaders)

    def _on_add_override(self, new_override):
        """
        Internal callback function that is called when Add Override context button is pressed
        :param new_override: ArtellaBaseOverride
        """

        valid_override = self._asset_node.add_override(new_override)
        if valid_override:
            self.overrideAdded.emit(valid_override, self)

    def _on_remove_override(self, override_to_remove):
        """
        Internal callback function that is called when Remove Override context button is pressed
        :param override_to_remove: ArtellaBaseOverride
        """

        removed_override = self._asset_node.remove_override(override_to_remove)
        if removed_override:
            self.overrideRemoved.emit(removed_override, self)

    def _on_save_override(self, override_to_save):
        """
        Internal callback function that is called when Save Override context button is pressed
        :param override_to_save: ArtellaBaseOverride
        """

        self._asset_node.save_override(override_to_save)

    def _on_save_all_overrides(self):
        """
        Internal callback function that is called when Save All Overrides context action is triggered
        """

        self._asset_node.save_all_overrides()

    def _on_remove(self):
        """
        Internal callback function that is called when Delete context action is triggered
        """

        valid_remove = self._asset_node.remove()
        if valid_remove:
            self.removed.emit(self)

    def _on_load_shaders(self):
        """
        Internal callback function that is called when Load Shaders context action is triggered
        """

        self._asset_node.load_shaders()

    def _on_unload_shaders(self):
        """
        Internal callback function that is called when Unload Shaders context action is triggered
        """

        self._asset_node.unload_shaders()


class OutlinerOverrideItem(outlineritems.OutlinerTreeItemWidget, object):

    removed = Signal()

    def __init__(self, override, parent=None):

        self._override = override

        super(OutlinerOverrideItem, self).__init__(name=override.OVERRIDE_NAME, parent=parent)

    def ui(self):
        super(OutlinerOverrideItem, self).ui()

        self.setMouseTracking(True)

        self._item_widget.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        self.setStyleSheet('background-color: rgb(45,45,45);')

        icon_lbl = QLabel()
        icon_lbl.setMaximumWidth(18)
        icon_lbl.setPixmap(self._override.OVERRIDE_ICON.pixmap(self._override.OVERRIDE_ICON.actualSize(QSize(20, 20))))
        self._target_lbl = QLabel(self._name.title())
        self._editor_btn = QPushButton('Editor')
        self._editor_btn.setFlat(True)
        self._editor_btn.setIcon(artellapipe.resource.icon('editor'))
        self._save_btn = QPushButton()
        self._save_btn.setFlat(True)
        self._save_btn.setIcon(artellapipe.resource.icon('save'))
        self._delete_btn = QPushButton()
        self._delete_btn.setFlat(True)
        self._delete_btn.setIcon(artellapipe.resource.icon('delete'))

        self._item_layout.addWidget(icon_lbl, 0, 1, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 2, 1, 1)
        self._item_layout.addWidget(self._target_lbl, 0, 3, 1, 1)
        self._item_layout.addWidget(splitters.get_horizontal_separator_widget(), 0, 4, 1, 1)
        self._item_layout.addWidget(self._editor_btn, 0, 5, 1, 1)
        self._item_layout.setColumnStretch(6, 7)
        self._item_layout.addWidget(self._save_btn, 0, 8, 1, 1)
        self._item_layout.addWidget(self._delete_btn, 0, 9, 1, 1)

    def setup_signals(self):
        self._editor_btn.clicked.connect(self._on_open_override_editor)
        self._save_btn.clicked.connect(self._on_save_override)
        self._delete_btn.clicked.connect(self._on_remove_override)

    def _on_open_override_editor(self):
        """
        Internal callback function that is called when Editor button is pressed
        """

        self._override.show_editor()

    def _on_save_override(self):
        """
        Internal callback function that is called when Save button is pressed
        """

        return self._override.save()

    def _on_remove_override(self):
        """
        Internal callback function that is called when Remove button is pressed
        """

        valid_remove = self._override.remove_from_node()
        if valid_remove:
            self.removed.emit()

        return self._override