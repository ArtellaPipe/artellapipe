#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export shot files to be used in the shot builder tool
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import sys
import ast
import json
import tempfile
import traceback

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpPyUtils import python

import tpDccLib as tp

import tpQtLib
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import window, progressbar
from artellapipe.utils import shader
from artellapipe.tools.shotmanager.core import override
from artellapipe.tools.shotmanager.widgets import shothierarchy, shotproperties, shotassetslist, shotoverrides
from artellapipe.tools.shotmanager.utils import json_include


class ShotFile(object):
    def __init__(self, project, file_path, root=None):
        super(ShotFile, self).__init__()

        self._project = project
        self._file_path = file_path
        self._root = root

    def build_shot(self, skip_root=False):
        """
        Builds shot with current data
        """

        file_dir = os.path.dirname(self._file_path)
        file_name = os.path.basename(self._file_path)

        try:
            with open(self._file_path, 'r') as f:
                shot_data = json.loads(f.read())
        except Exception as e:
            artellapipe.logger.error('Error while loading Shot File: {} | {} | {}'.format(self._file_path, e, traceback.format_exc()))
            return dict()
        root_shot = shot_data.get('root', None)
        if root_shot and not skip_root and root_shot != os.path.basename(self._file_path):
            root_shot_file = os.path.join(self._project.get_path(), root_shot)
            if not os.path.isfile(root_shot_file):
                artellapipe.logger.warning('Root Shot File does not exists: "{}"!'.format(root_shot_file))
                return dict()
            root_data = ShotFile(project=self._project, file_path=root_shot_file).load()
            if not root_data:
                artellapipe.logger.warning('Root Shot File "{}" has not data!'.format(root_shot_file))
                return dict()
            root_files = root_data.get('files', dict())
            root_overrides = root_data.get('overrides', dict())

            for root_file_name in root_files.keys():
                if root_file_name not in shot_data['files']:
                    shot_data['files'][root_file_name] = root_data['files'][root_file_name]
            for root_override_name in root_overrides.keys():
                if root_override_name not in shot_data['overrides']:
                    shot_data['overrides'][root_override_name] = root_data['overrides'][root_override_name]

            temp_name = '__TEMP__{}'.format(file_name)
            temp_file = os.path.join(file_dir, temp_name)
            with open(temp_file, 'w') as f:
                json.dump(shot_data, f)
            out_str = json_include.build_json_include(file_dir, temp_name)
            out_dict = ast.literal_eval(out_str)
            try:
                os.remove(temp_file)
            except Exception:
                pass
        else:
            out_str = json_include.build_json_include(file_dir, file_name)
            out_dict = ast.literal_eval(out_str)

        return out_dict

    def load(self):
        """
        Loads Shot File
        """

        build_data = self.build_shot()

        return build_data

    def save(self, asset_files, override_files):
        """
        Saves shot file
        :param asset_files: list
        :param override_files: list
        :return: bool
        """

        asset_files = python.force_list(asset_files)
        override_files = python.force_list(override_files)

        shot_data = {
            'data_version': self._project.DataVersions.SHOT,
            'assembler_version': ShotAssembler.VERSION,
            'root': '',
            'files': {},
            'overrides': {}
        }


        # Store Asset Files
        for asset_file in asset_files:
            asset_file_path = asset_file.asset_file
            if not os.path.isfile(asset_file_path):
                artellapipe.logger.warning('Asset File {} does not exists!'.format(asset_file_path))
                continue
            rel_path = os.path.relpath(asset_file_path, os.path.dirname(self._file_path))

            project_path = os.path.relpath(asset_file_path, self._project.get_path())
            shot_data['files'][project_path] = dict()
            shot_data['files'][project_path]['...'] = '<{}>'.format(rel_path)

        # Store Override Files
        for override_file in override_files:
            override_file_path = override_file.file_path
            if not override_file_path or not os.path.isfile(override_file_path):
                artellapipe.logger.warning('Override File {} does not exists!'.format(override_file_path))
                continue
            rel_path = os.path.relpath(override_file_path, os.path.dirname(self._file_path))
            override_name = os.path.basename(os.path.relpath(override_file_path, self._project.get_path()))
            if override_name in shot_data['overrides']:
                artellapipe.logger.warning('Override {} is already stored. Skipping ...!'.format(override_name))
            shot_data['overrides'][override_name] = dict()
            shot_data['overrides'][override_name]['...'] = '<{}>'.format(rel_path)

        # We update data taking into account root shot data
        if self._root:
            root_rel_path = os.path.relpath(self._root, os.path.dirname(self._file_path))
            shot_data['root'] = root_rel_path

            # if not os.path.isfile(self._root):
            #     artellapipe.logger.warning('Root Shot File does not exists: "{}"!'.format(self._root))
            #     return dict()
            # root_data = ShotFile(project=self._project, file_path=self._root).load()
            # if not root_data:
            #     artellapipe.logger.warning('Root Shot File "{}" has not data!'.format(self._root))
            #     return dict()
            #
            # root_files = root_data.get('files', dict())
            # root_overrides = root_data.get('overrides', dict())
            #
            # print('Root Files: {}'.format(root_files))
            # print('Root Overrides: {}'.format(root_overrides))

        try:
            with open(self._file_path, 'w') as f:
                json.dump(shot_data, f)
        except Exception as e:
            artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))

    def get_files(self):
        """
        Returns file stored in Shot File
        :return: list
        """

        shot_data = self.build_shot(skip_root=True)

        return shot_data['files']

    def get_overrides(self):
        """
        Returns overrides stored in Shot File
        :return: list
        """

        shot_data = self.build_shot(skip_root=True)

        return shot_data['overrides']


class ShotAssembler(window.ArtellaWindow, object):

    VERSION = '0.0.1'
    LOGO_NAME = 'shotassembler_logo'

    SHOT_FILE_CLASS = ShotFile

    def __init__(self, project):

        self._assets = dict()
        self._shot_file = None
        self._root_shot = None

        super(ShotAssembler, self).__init__(
            project=project,
            name='ShotAssembler',
            title='Shot Assembler',
            size=(900, 850)
        )

        self._init()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(ShotAssembler, self).ui()

        self._setup_menubar()

        self._dock_window = tpQtLib.DockWindow(use_scrollbar=True)
        self._dock_window.centralWidget().show()

        self._shots_props = shotproperties.ShotProps(project=self._project)
        self._shot_hierarchy = shothierarchy.ShotHierarchy()
        self._shot_assets = shotassetslist.ShotAssets(project=self._project)
        self._shot_overrides = shotoverrides.ShotOverrides(project=self._project)

        self._generate_btn = QPushButton('GENERATE SHOT')
        self._generate_btn.setIcon(artellapipe.resource.icon('magic'))
        self._generate_btn.setMinimumHeight(30)
        self._generate_btn.setMinimumWidth(80)

        self.main_layout.addWidget(self._shots_props)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._dock_window)
        self._dock_window.main_layout.addWidget(self._shot_hierarchy)
        self._shot_assets_dock = self._dock_window.add_dock(widget=self._shot_assets, name='Assets', pos=Qt.LeftDockWidgetArea)
        self._shot_overrides_dock = self._dock_window.add_dock(widget=self._shot_overrides, name='Overrides', tabify=False, pos=Qt.RightDockWidgetArea)
        self._shot_overrides_dock.setEnabled(False)
        self.main_layout.addLayout(splitters.SplitterLayout())
        self.main_layout.addWidget(self._generate_btn)

        self._progress = progressbar.ArtellaProgressBar(project=self._project)
        self._progress.setVisible(False)
        self.main_layout.addWidget(self._progress)

    def setup_signals(self):
        self._shot_assets.updateHierarchy.connect(self._on_update_hierarchy)
        self._generate_btn.clicked.connect(self._on_generate_shot)

    @staticmethod
    def registered_file_types():
        """
        Returns a list of registered file types classes
        :return: list
        """

        if 'file_types' not in sys.modules[__name__].__dict__:
            return dict()

        return sys.modules[__name__].__dict__['file_types']

    @staticmethod
    def registered_overrides():
        """
        Returns a list of registered overrides
        :return: list
        """

        if 'overrides' not in sys.modules[__name__].__dict__:
            return dict()

        return sys.modules[__name__].__dict__['overrides']

    def _init(self):
        """
        Initializes Shot Assembler widgets
        """

        self._update_assets()

        file_types = self.registered_file_types()
        overrides = self.registered_overrides()

        if file_types:
            self._shot_assets.set_file_types(file_types)
        if overrides:
            self._shot_overrides.set_overrides(overrides)

    def _update_assets(self):
        """
        Internal function that updates the cache of current assets
        """

        all_assets = self._project.find_all_assets()
        for asset in all_assets:
            asset_name = asset.get_name()
            if asset_name in self._assets:
                artellapipe.logger.warning('Asset {} is duplicated!'.format(asset_name))
                continue
            self._assets[asset_name] = asset

    def _setup_menubar(self):
        """
        Internal callback function that setups menu bar
        :return: QMenuBar
        """

        menubar_widget = QWidget()
        menubar_layout = QVBoxLayout()
        menubar_layout.setContentsMargins(0, 0, 0, 0)
        menubar_layout.setSpacing(0)
        menubar_widget.setLayout(menubar_layout)
        menubar = QMenuBar()
        new_file_icon = artellapipe.resource.icon('new_file')
        load_icon = artellapipe.resource.icon('open')
        save_icon = artellapipe.resource.icon('save')
        save_override_icon = artellapipe.resource.icon('save_as')
        file_menu = menubar.addMenu('File')
        new_file_action = QAction(new_file_icon, 'New', menubar_widget)
        load_action = QAction(load_icon, 'Load', menubar_widget)
        save_action = QAction(save_icon, 'Save', menubar_widget)
        save_override = QAction(save_override_icon, 'Save as Override', menubar_widget)
        file_menu.addAction(new_file_action)
        file_menu.addSeparator()
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_override)
        menubar_layout.addWidget(menubar)
        self.main_layout.addWidget(menubar_widget)

        new_file_action.triggered.connect(self._on_new_file)
        load_action.triggered.connect(self._on_load_shot)
        save_action.triggered.connect(self._on_save_shot)
        save_override.triggered.connect(self._on_save_shot_override)

        return menubar

    def add_asset(self, asset):
        """
        Function that adds new asset into the list
        :param asset:
        """

        asset_data = asset.get_data()
        if not asset_data:
            artellapipe.logger.warning('Asset "{}" has not valid data! Skipping ...'.format(asset))
            return

        asset_nodes = asset.get_nodes()
        for asset_node in asset_nodes:
            self._shot_hierarchy.add_asset(asset_node)

    def _new_file(self):
        """
        Internal function that creates a new shot file
        """

        self._shot_assets.clear_assets()
        self._shot_hierarchy.clear_hierarchy()
        self._shot_overrides.clear_overrides()

    def _on_new_file(self):
        """
        Internal callback function that is called when New File action is triggered
        :return:
        """

        self._new_file()

    def _on_load_shot(self):
        """
        Internal callback function that is called when Load Shot action is triggered
        """

        pattern = 'Shot Files (*{})'.format(self._project.shot_extension)
        shot_file = tp.Dcc.select_file_dialog(title='Select Shot to Load', start_directory=self._project.get_path(), pattern=pattern)
        if not shot_file:
            return

        shot_data = self.SHOT_FILE_CLASS(project=self._project, file_path=shot_file).load()
        if not shot_data:
            artellapipe.logger.warning('Shot File has no data: {}!'.format(shot_file))
            return

        self._new_file()

        shot_root = shot_data.get('root', None)

        shot_files = shot_data.get('files', None)
        if not shot_files and not shot_root:
            artellapipe.logger.warning('Shot File has no files: {}!'.format(shot_file))
            return

        override_files = shot_data.get('overrides', None)

        shot_data_version = shot_data['data_version']
        assembler_version = shot_data['assembler_version']
        if shot_data_version != self._project.DataVersions.SHOT:
            artellapipe.logger.warning('Shot File {} is not compatible with current format. Please contact TD!'.format(shot_file))
            return
        if assembler_version != self.VERSION:
            artellapipe.logger.warning('Shot File {} was exported with an older/newer version. Please contact TD!'.format(shot_file))
            return

        assets_added = self._shot_assets.load_shot_files(shot_files)
        if assets_added:
            self._shot_overrides_dock.setEnabled(True)

        if override_files:
            overrides_added = self._shot_overrides.load_override_files(override_files)

        self._shot_file = shot_file
        self._root_shot = shot_root

    def _on_save_shot(self):
        """
        Internal callback function that is called when Save Shot action is triggered
        """

        if self._shot_file and self._shot_file.endswith(self._project.shot_extension):
            shot_file = self._shot_file
        else:
            pattern = 'Shot Files (*{})'.format(self._project.shot_extension)
            shot_file = tp.Dcc.save_file_dialog(title='Save Shot', start_directory=self._project.get_path(), pattern=pattern)
            if not shot_file:
                return

        asset_files = self._shot_assets.all_assets()
        if not asset_files:
            artellapipe.logger.warning('No Asset Paths to export for Shot. Shot export aborted!')
            return

        override_files = self._shot_overrides.get_loaded_overrides()

        shot_file_inst = None
        if self._root_shot:
            root_shot_file = os.path.join(self._project.get_path(), self._root_shot)
            if root_shot_file != shot_file:
                shot_file_inst = self.SHOT_FILE_CLASS(project=self._project, file_path=shot_file, root=root_shot_file)
        if not shot_file_inst:
            shot_file_inst = self.SHOT_FILE_CLASS(project=self._project, file_path=shot_file)

        return shot_file_inst.save(asset_files=asset_files, override_files=override_files)

    def _on_save_shot_override(self):
        """
        Internal callback function that is called when Save Shot Override action is triggered
        """

        if not self._shot_file:
            artellapipe.logger.warning('No Root Shot found! Load a Shot first and try again ...')
            return

        pattern = 'Shot Files (*{})'.format(self._project.shot_extension)
        shot_file = tp.Dcc.save_file_dialog(title='Save Shot', start_directory=self._project.get_path(), pattern=pattern)
        if not shot_file:
            return

        asset_files = self._shot_assets.all_assets()
        if not asset_files:
            artellapipe.logger.warning('No Asset Paths to export for Shot. Shot export aborted!')
            return

        loaded_overrides = self._shot_overrides.get_loaded_overrides()

        shot_root_inst = self.SHOT_FILE_CLASS(project=self._progress, file_path=self._shot_file)
        files = shot_root_inst.get_files()
        overrides = shot_root_inst.get_overrides()

        new_asset_files = list()
        for asset_file in asset_files:
            for file_name, file_data in files.items():
                file_path = os.path.join(self._project.get_path(), file_name)
                if file_path == asset_file.asset_file:
                    continue
                new_asset_files.append(file_path)

        new_override_files = list()
        loaded_override_files = [os.path.join(self._project.get_path(), ov) for ov in overrides.keys()]

        for override_file in loaded_overrides:
            if override_file.file_path in loaded_override_files:
                continue
            else:
                new_override_files.append(override_file)

        shot_file_inst = self.SHOT_FILE_CLASS(project=self._project, file_path=shot_file, root=self._shot_file)
        return shot_file_inst.save(asset_files=new_asset_files, override_files=new_override_files)

    def _on_update_hierarchy(self):
        """
        Internal callback function that is called when assets hierarchy needs to be updated
        """

        self._shot_hierarchy.clear_hierarchy()

        for asset in self._shot_assets.all_assets():
            asset_path = asset.asset_file
            if not os.path.isfile(asset_path):
                artellapipe.logger.warning('Impossible to load asset asset file: {}'.format(asset_path))
                continue

            self.add_asset(asset)

    def _on_generate_shot(self):
        """
        Internal callback function that is called when Generate Shot button is pressed
        """

        if not tp.is_maya():
            artellapipe.logger.warning('Shot Generation is only available in Maya!')
            return

        all_hierarchy = self._shot_hierarchy.all_hierarchy()
        if not all_hierarchy:
            artellapipe.logger.warning('No items added to ShotAssembler list!')
            return

        pre_overrides = list()
        post_overrides = list()
        for shot_override in self._shot_overrides.get_loaded_overrides():
            if shot_override.OVERRIDE_STEP == override.OverrideExecutionStep.POST:
                post_overrides.append(shot_override)
            else:
                pre_overrides.append(pre_overrides)

        tp.Dcc.new_file()

        self._progress.set_minimum(0)
        self._progress.set_maximum(len(all_hierarchy) + len(pre_overrides) + len(post_overrides) + 3)
        self._progress.set_value(0)
        self._progress.setVisible(True)
        self._progress.set_text('Generating Shot ...')
        self.repaint()

        self._progress.set_value(self._progress.value() + 1)
        self._progress.set_text('Applying Pre Load Overrides ...')
        self.repaint()

        for pre_override in pre_overrides:
            self._progress.set_value(self._progress.value() + 1)
            self._progress.set_text('Applying Pre Load Override: {}'.format(pre_override.OVERRIDE_NAME))
            self.repaint()
            pre_override.apply(all_hierarchy)

        for i, node_asset in enumerate(all_hierarchy):
            self._progress.set_value(self._progress.value() + 1)
            self._progress.set_text('Loading Asset: {}'.format(node_asset.asset_file))
            self.repaint()
            node_asset.load()

        self._progress.set_value(self._progress.value() + 1)
        self._progress.set_text('Applying Post Load Overrides ...')
        self.repaint()

        for post_override in post_overrides:
            self._progress.set_value(self._progress.value() + 1)
            self._progress.set_text('Applying Post Load Override: {}'.format(post_override.OVERRIDE_NAME))
            self.repaint()
            post_override.apply()

        tp.Dcc.clear_selection()

        tp.Dcc.fit_view(animation=True)

        self._progress.set_value(self._progress.value() + 1)
        self._progress.set_text('Loading Shaders ...')
        self.repaint()

        # shader.load_all_scene_shaders(project=self._project)

        self._progress.set_value(0)
        self._progress.set_text('')
        self._progress.setVisible(False)


def register_file_type(cls):
    """
    This function registers given exporter class
    :param cls: class, Alembic importer class we want to register
    """

    if 'file_types' not in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__['file_types'] = dict()

    sys.modules[__name__].__dict__['file_types'][cls.FILE_TYPE] = cls


def register_override(cls):
    """
    This function registers given exporter class
    :param cls: class, Alembic importer class we want to register
    """

    if 'overrides' not in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__['overrides'] = dict()

    sys.modules[__name__].__dict__['overrides'][cls.get_clean_name()] = cls


def run(project):
    win = ShotAssembler(project=project)
    win.show()

    return win

