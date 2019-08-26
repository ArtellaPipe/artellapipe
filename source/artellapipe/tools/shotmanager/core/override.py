#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core override implementation for Artella Shot Assembler
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import ast
import json
import traceback

from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import dialog
from artellapipe.core import defines


class OverrideExecutionStep(object):
    POST = 0
    PRE = 1


class ArtellaBaseOverride(object):

    OVERRIDE_NAME = None
    OVERRIDE_ICON = None
    OVERRIDE_EXTENSION = None
    OVERRIDE_STEP = OverrideExecutionStep.POST

    def __init__(self, project, asset_node=None, data=None, file_path=None):
        self._project = project
        self._asset_node = asset_node
        self._data = data
        self._file_path = file_path

    @classmethod
    def create_from_data(cls, project, data, file_path=None):
        """
        Creates a new instance of the override by a given data
        :param project: ArtellaProject
        :param data: dict
        :param file_path: str
        :return: ArtellaBaseOverride
        """

        raise NotImplementedError('create_from_data not implemented in {}!'.format(cls.__name__))

    @classmethod
    def create_from_file(cls, project, file_path):
        """
        Creates a new instance of the override with the contents of the given file
        :param project: ArtellaProject
        :param file_path: str
        :return:ArtellaBaseOverride
        """

        file_extension = os.path.splitext(file_path)[-1]
        if not file_extension:
            artellapipe.logger.warning('Impossible to load Override File: {}'.format(file_path))
            return

        if file_extension != cls.OVERRIDE_EXTENSION:
            return None

        try:
            with open(file_path, 'r') as f:
                file_data = json.loads(f.read())
        except Exception as e:
            artellapipe.logger.error('Error while loading Override File: {} | {} | {}'.format(file_path, e, traceback.format_exc()))
            return

        new_override = cls.create_from_data(project=project, data=file_data, file_path=file_path)

        return new_override

    @classmethod
    def get_clean_name(cls):
        """
        Returns clean name of the current override
        :return: str
        """

        return str(cls.OVERRIDE_NAME).lower().replace(' ', '_')

    @classmethod
    def get_attribute_name(cls):
        """
        Returns the name of the attribute this modifier should have in node
        :return: str
        """

        return '{}__{}'.format(defines.ARTELLA_SHOT_OVERRIDES_ATTRIBUTE_PREFX, cls.get_clean_name())

    @property
    def file_path(self):
        """
        Returns file path of the current override
        :return: str
        """

        return self._file_path

    def get_data(self):
        """
        Returns current data stored in the override
        :return: dict
        """

        if self._data:
            return self._data

        if not tp.Dcc.object_exists(self._asset_node.node):
            artellapipe.logger.warning('Impossible to retrieve override from a non-existent node: {}!'.format(self._asset_node.node))
            return

        override_name = self.get_attribute_name()
        attr_value = tp.Dcc.get_attribute_value(node=self._asset_node.node, attribute_name=override_name)

        try:
            attr_dict = ast.literal_eval(attr_value)
        except Exception:
            artellapipe.logger.warning('Impossible to retrieve proper data from override: {} in node: {}'.format(self.OVERRIDE_NAME, self._asset_node.node))
            attr_dict = dict()

        return attr_dict

    def is_added(self):
        """
        Returns whether or not current modifier is already into asset node
        :return: bool
        """

        return self._asset_node.has_override(self)

    def add_to_node(self):
        """
        Adds override to current asset node
        :return: bool
        """

        if self.is_added():
            artellapipe.logger.warning('Override {} already exists on node {}! Aborting operation ...'.format(self.OVERRIDE_NAME, self._asset_node.node))
            return False

        override_name = self.get_attribute_name()
        tp.Dcc.add_string_attribute(node=self._asset_node.node, attribute_name=override_name)
        tp.Dcc.set_string_attribute_value(node=self._asset_node.node, attribute_name=override_name, attribute_value=str(self.default_value()))

        return True

    def remove_from_node(self):
        """
        Removes current override from current asset node
        :return: bool
        """

        if not self.is_added():
            artellapipe.logger.warning('Impossible to remove override {} because its not added to node: {}! Aborting operation ...'.format(self.OVERRIDE_NAME, self._asset_node.node))
            return False

        override_name = self.get_attribute_name()
        if not tp.Dcc.attribute_exists(node=self._asset_node.node, attribute_name=override_name):
            artellapipe.logger.warning('Override Attribute: {} not found in node: {}! Aborting operation ...'.format(override_name, self._asset_node.node))
            return False

        tp.Dcc.delete_attribute(node=self._asset_node.node, attribute_name=override_name)

        return True

    def show_editor(self):
        """
        Shows editor of current override
        """

        override_editor = ArtellaOverrideEditor(override=self)
        override_editor.exec_()

    def apply(self, *args, **kwargs):
        """
        Applies current override
        :param args: list
        :param kwargs: dict
        """

        raise NotImplementedError('apply function not implemented for: {}'.format(self.__class__.__name__))

    def default_value(self):
        """
        Returns the default value stored by the override
        :return: dict
        """

        return dict()

    def get_editor_widget(self):
        """
        Returns custom widget used by Override Editor to edit override attributes
        :return: QWidget
        """

        return None

    def update_override_data(self, data):
        """
        Function updates current scene override with the attributes of the current override
        :param data: dict
        :return: bool
        """

        if not data:
            return

        override_name = self.get_attribute_name()
        tp.Dcc.set_string_attribute_value(node=self._asset_node.node, attribute_name=override_name, attribute_value=str(data))

    def save(self, save_path=None):
        """
        Function that stores current override into disk
        :param save_path: str
        :return:
        """

        data_to_save = self._get_data_to_save()
        if not data_to_save:
            artellapipe.logger.warning('{} >> Override has no data to save for node: {}!'.format(self.OVERRIDE_NAME, self._asset_node.node))
            return

        if not save_path:
            save_path = tp.Dcc.select_folder_dialog(title='Select folder to save {} Override'.format(self.OVERRIDE_NAME), start_directory=self._project.get_path())
            if not save_path:
                return

        short_name = tp.Dcc.node_short_name(node=self._asset_node.node)
        out_file = os.path.join(save_path, '{}_{}{}'.format(short_name, self.OVERRIDE_NAME, self.OVERRIDE_EXTENSION))

        try:
            with open(out_file, 'w') as f:
                json.dump(data_to_save, f)
        except Exception as e:
            artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))

    def _get_data_to_save(self):
        """
        Returns data that should be stored
        :return: dict
        """

        return dict()


class ArtellaOverrideWidget(base.BaseWidget, object):
    def __init__(self, override, parent=None):

        self._override = override

        super(ArtellaOverrideWidget, self).__init__(parent=parent)

    def get_data(self):
        """
        Returns data that should be stored in override
        :return: dict
        """

        raise NotImplementedError('get_data function not implemented in {} override widget!'.format(self.__class__.__name__))


class ArtellaOverrideEditor(dialog.ArtellaDialog, object):
    def __init__(self, override, parent=None):

        self._override = override

        super(ArtellaOverrideEditor, self).__init__(
            name='OverrideEditor',
            title='Artella - Override Editor',
            parent=parent
        )

        self.setWindowIcon(self._override.OVERRIDE_ICON)
        self.setWindowTitle(self._override.OVERRIDE_NAME)

    def ui(self):
        super(ArtellaOverrideEditor, self).ui()

        self._override_widget = self._override.get_editor_widget()
        if self._override_widget:
            self.main_layout.addWidget(self._override_widget)
            save_btn = QPushButton('Save')
            save_btn.setIcon(artellapipe.resource.icon('save'))
            self.main_layout.addLayout(splitters.SplitterLayout())
            self.main_layout.addWidget(save_btn)
            save_btn.clicked.connect(self._on_save_override)
        else:
            close_btn = QPushButton('Close')
            close_btn.setIcon(artellapipe.resource.icon('delete'))
            self.main_layout.addWidget(close_btn)
            close_btn.clicked.connect(self.fade_close)

    def _on_save_override(self):
        """
        Internal callback function that is called when Save button is clicked
        :return: bool
        """

        if not self._override_widget:
            return

        data = self._override_widget.get_data()
        self._override.update_override_data(data)
        self.fade_close()
