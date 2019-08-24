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
import traceback

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpPyUtils import python

import tpDccLib as tp

import tpQtLib
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import window, progressbar
from artellapipe.tools.shotmanager.widgets import shothierarchy, shotproperties, shotassetslist, shotoverrides
from artellapipe.tools.shotmanager.utils import json_include


class ShotFile(object):
    def __init__(self, project, file_path):
        super(ShotFile, self).__init__()

        self._project = project
        self._file_path = file_path

    def load(self):
        """
        Loads Shot File
        """

        file_dir = os.path.dirname(self._file_path)
        file_name = os.path.basename(self._file_path)

        out_str = json_include.build_json_include(file_dir, file_name)
        out_dict = ast.literal_eval(out_str)

        return out_dict

    def save(self, asset_files):
        """
        Saves shot
        :return: bool
        """

        asset_files = python.force_list(asset_files)

        shot_data = {
            'data_version': self._project.DataVersions.SHOT,
            'assembler_version': ShotAssembler.VERSION,
            'files': {}
        }

        for asset_file in asset_files:
            asset_file_path = asset_file.asset_file
            if not os.path.isfile(asset_file_path):
                artellapipe.logger.warning('Asset File {} does not exists!'.format(asset_file_path))
                continue
            rel_path = os.path.relpath(asset_file_path, os.path.dirname(self._file_path))
            project_path = os.path.relpath(asset_file_path, self._project.get_path())
            shot_data['files'][project_path] = dict()
            shot_data['files'][project_path]['...'] = '<{}>'.format(rel_path)

        try:
            with open(self._file_path, 'w') as f:
                json.dump(shot_data, f)
        except Exception as e:
            artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))


class ShotAssembler(window.ArtellaWindow, object):

    VERSION = '0.0.1'
    LOGO_NAME = 'shotassembler_logo'

    SHOT_FILE_CLASS = ShotFile

    def __init__(self, project):

        self._assets = dict()
        self._shot = None

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

        self._shots_props = shotproperties.ShotProps()
        self._shot_hierarchy = shothierarchy.ShotHierarchy()
        self._shot_assets = shotassetslist.ShotAssets(project=self._project)
        self._shot_overrides = shotoverrides.ShotOverrides()

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

    def get_registered_file_types(self):
        """
        Returns a list of registered file types classes
        :return: list
        """

        if 'file_types' not in sys.modules[__name__].__dict__:
            return dict()

        return sys.modules[__name__].__dict__['file_types']

    def get_registered_overrides(self):
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

        file_types = self.get_registered_file_types()
        overrides = self.get_registered_overrides()

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
        load_icon = artellapipe.resource.icon('open')
        save_icon = artellapipe.resource.icon('save')
        file_menu = menubar.addMenu('File')
        load_action = QAction(load_icon, 'Load', menubar_widget)
        save_action = QAction(save_icon, 'Save', menubar_widget)
        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        menubar_layout.addWidget(menubar)
        self.main_layout.addWidget(menubar_widget)

        load_action.triggered.connect(self._on_load_shot)
        save_action.triggered.connect(self._on_save_shot)

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

    def _on_load_shot(self):
        """
        Internal callback function that is called when Load Shot action is clicked
        """

        pattern = 'Shot Files (*{})'.format(self._project.shot_extension)
        shot_file = tp.Dcc.select_file_dialog(title='Select Shot to Load', start_directory=self._project.get_path(), pattern=pattern)
        if not shot_file:
            return

        shot_data = self.SHOT_FILE_CLASS(project=self._project, file_path=shot_file).load()
        if not shot_data:
            artellapipe.logger.warning('Shot File has no data: {}!'.format(shot_file))
            return

        shot_files = shot_data.get('files', None)
        if not shot_files:
            artellapipe.logger.warning('Shot File has no files: {}!'.format(shot_file))
            return

        shot_data_version = shot_data['data_version']
        assembler_version = shot_data['assembler_version']
        if shot_data_version != self._project.DataVersions.SHOT:
            artellapipe.logger.warning('Shot File {} is not compatible with current format. Please contact TD!'.format(shot_file))
            return
        if assembler_version != self.VERSION:
            artellapipe.logger.warning('Shot File {} was exported with an older/newer version. Please contact TD!'.format(shot_file))
            return

        self._shot_assets.load_shot_files(shot_files)

    def _on_save_shot(self):
        """
        Internal callback function that is called when Open Shot action is clicked
        """

        pattern = 'Shot Files (*{})'.format(self._project.shot_extension)
        shot_file = tp.Dcc.save_file_dialog(title='Save Shot', start_directory=self._project.get_path(), pattern=pattern)
        if not shot_file:
            return

        asset_files = self._shot_assets.all_assets()
        if not asset_files:
            artellapipe.logger.warning('No Asset Paths to export for Shot. Shot export aborted!')
            return

        return self.SHOT_FILE_CLASS(project=self._project, file_path=shot_file).save(asset_files=asset_files)

    def _on_update_hierarchy(self):
        """
        Internal callback function that is called when assets hierarchy needs to be updated
        """

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

        tp.Dcc.new_file()

        self._progress.set_minimum(0)
        self._progress.set_maximum(len(all_hierarchy))
        self._progress.setVisible(True)
        self._progress.set_text('Generating Shot ...')
        self.repaint()

        for i, node_asset in enumerate(all_hierarchy):
            self._progress.set_value(i)
            self._progress.set_text('Loading Asset: {}'.format(node_asset.asset_file))
            self.repaint()
            node_asset.load()

        tp.Dcc.clear_selection()

        tp.Dcc.fit_view(animation=True)

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

    sys.modules[__name__].__dict__['overrides'][cls.OVERRIDE_NAME] = cls


def run(project):
    win = ShotAssembler(project=project)
    win.show()

    return win

