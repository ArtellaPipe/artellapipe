#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Standin Exporter
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import sys
from functools import  partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import button
from artellapipe.tools.standinmanager import standinmanager

if tp.is_maya():
    import tpMayaLib as maya


class StandinExporter(base.BaseWidget, object):
    def __init__(self, project, parent=None):

        self._project = project

        super(StandinExporter, self).__init__(parent=parent)

    def ui(self):
        super(StandinExporter, self).ui()

        buttons_layout = QGridLayout()
        self.main_layout.addLayout(buttons_layout)

        icon_double_left = artellapipe.resource.icon('double_left')
        icon_double_left_hover = artellapipe.resource.icon('double_left_hover')

        name_lbl = QLabel('Standin Name: ')
        self.name_line = QLineEdit()
        self.name_line_btn = button.IconButton(icon=icon_double_left, icon_hover=icon_double_left_hover)
        buttons_layout.addWidget(name_lbl, 1, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self.name_line, 1, 1)
        buttons_layout.addWidget(self.name_line_btn, 1, 2)

        frame_range_lbl = QLabel('Frame Range: ')
        self.start = QSpinBox()
        self.start.setRange(-sys.maxint, sys.maxint)
        self.start.setFixedHeight(20)
        self.start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.end = QSpinBox()
        self.end.setRange(-sys.maxint, sys.maxint)
        self.end.setFixedHeight(20)
        self.end.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame_range_widget = QWidget()
        frame_range_layout = QHBoxLayout()
        frame_range_layout.setContentsMargins(2, 2, 2, 2)
        frame_range_layout.setSpacing(2)
        frame_range_widget.setLayout(frame_range_layout)
        for widget in [frame_range_lbl, self.start, self.end]:
            frame_range_layout.addWidget(widget)
        buttons_layout.addWidget(frame_range_lbl, 3, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(frame_range_widget, 3, 1)

        folder_icon = artellapipe.resource.icon('folder')
        export_path_layout = QHBoxLayout()
        export_path_layout.setContentsMargins(2, 2, 2, 2)
        export_path_layout.setSpacing(2)
        export_path_widget = QWidget()
        export_path_widget.setLayout(export_path_layout)
        export_path_lbl = QLabel('Export Path: ')
        self.export_path_line = QLineEdit()
        self.export_path_line.setReadOnly(True)
        self.export_path_line.setText(self._project.get_path())
        self.export_path_btn = QPushButton()
        self.export_path_btn.setIcon(folder_icon)
        self.export_path_btn.setIconSize(QSize(18, 18))
        self.export_path_btn.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0); border: 0px solid rgba(255,255,255,0);")
        export_path_layout.addWidget(self.export_path_line)
        export_path_layout.addWidget(self.export_path_btn)
        buttons_layout.addWidget(export_path_lbl, 4, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(export_path_widget, 4, 1)

        auto_sync_shaders_lbl = QLabel('Auto Sync Shaders?: ')
        self.auto_sync_shaders = QCheckBox()
        self.auto_sync_shaders.setChecked(True)
        buttons_layout.addWidget(auto_sync_shaders_lbl, 5, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self.auto_sync_shaders, 5, 1)

        self.main_layout.addLayout(splitters.SplitterLayout())

        export_layout = QHBoxLayout()
        self.export_btn = QPushButton('Export')
        self.export_btn.setEnabled(False)
        export_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        export_layout.addWidget(self.export_btn)
        export_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.main_layout.addLayout(export_layout)

        self.name_line.textChanged.connect(self.refresh)
        self.export_path_btn.clicked.connect(self._on_set_export_path)
        self.export_btn.clicked.connect(self._on_export)
        self.name_line_btn.clicked.connect(partial(self._get_selected, self.name_line))

        self.refresh()

    def refresh(self):
        self._refresh_standin_name()
        self._refresh_frame_ranges()

        if self.export_path_line.text() and os.path.isdir(self.export_path_line.text()):
            self.export_btn.setEnabled(True)
        else:
            self.export_btn.setEnabled(False)

    def export_standin(self, export_path, standin_name, start_frame=1, end_frame=1):
        if not export_path or not os.path.isdir(export_path):
            artellapipe.logger.warning('Impossible to export Standin in invalid path: {}'.format(export_path))
            return None

        self.name_line.setText(standin_name)
        self.start.setValue(start_frame)
        self.end.setValue(end_frame)
        self.export_path_line.setText(export_path)
        self._on_export()

    def _refresh_standin_name(self):
        """
        Internal function that updates Alembic name
        """

        if self.name_line.text() != '':
            return

        sel = maya.cmds.ls(sl=True)
        if sel:
            sel = sel[0]
            is_referenced = maya.cmds.referenceQuery(sel, isNodeReferenced=True)
            if is_referenced:
                sel_namespace = maya.cmds.referenceQuery(sel, namespace=True)
                if not sel_namespace or not sel_namespace.startswith(':'):
                    pass
                else:
                    sel_namespace = sel_namespace[1:] + ':'
                    sel = sel.replace(sel_namespace, '')

            self.name_line.setText(sel)

    def _refresh_frame_ranges(self):
        """
        Internal function that updates the frame ranges values
        """

        start_frame = maya.cmds.playbackOptions(q=True, min=True)
        end_frame=maya.cmds.playbackOptions(q=True, max=True)
        self.start.setValue(int(start_frame))
        self.end.setValue(int(end_frame))

    def _get_selected(self, line_widget):
        sel = maya.cmds.ls(sl=True, l=True)
        if not sel:
            artellapipe.logger.warning('Please select a object first!')
            return
        if len(sel) > 1:
            artellapipe.logger.warning('You have selected more than one object. First item in the selection will be used ...')
        sel = sel[0]
        if sel.startswith('|'):
            sel = sel[1:]

        uuid = maya.cmds.ls(sel, uuid=True)
        self._target = uuid
        short = maya.cmds.ls(sel)[0]

        line_widget.clear()
        line_widget.setText(short)

        self.refresh()

        return sel

    def _on_set_export_path(self):
        """
        Internal function that is calledd when the user selects the folder icon
        Allows the user to select a path to export Alembic group contents
        """

        assets_path = self._project.get_assets_path()
        start_dir = self._project.get_assets_path()

        if self.name_line.text():
            for asset_type in self._project.asset_types:
                asset_type = asset_type.replace(' ', '')
                asset_path = os.path.join(assets_path, asset_type, self.name_line.text(), '__working__', 'model')
                if os.path.exists(assets_path):
                    start_dir = os.path.dirname(asset_path)
                    break

        res = maya.cmds.fileDialog2(fm=3, dir=start_dir, cap='Select Alembic Export Folder')
        if not res:
            return

        export_folder = res[0]
        self.export_path_line.setText(export_folder)

    def _on_export(self):
        out_folder = self.export_path_line.text()
        if not os.path.exists(out_folder):
            maya.cmds.confirmDialog(
                t='Error during Standin Exportation',
                m='Output Path does not exists: {}. Select a valid one!'.format(out_folder)
            )
            return

        standin_file = os.path.join(out_folder, self.name_line.text()+'.ass')
        bbox_file = os.path.join(out_folder, self.name_line.text()+'.asstoc')
        # arnold_files = [standin_file, bbox_file]
        arnold_files = [standin_file]

        if not self.auto_sync_shaders.isChecked():
            res = maya.cmds.confirmDialog(
                t='Exporting Standin',
                m='Make sure that your asset has proper shaders applied to it! Do you want to continue?',
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No',
                dismissString='No',
                icon='warning'
            )
            if res != 'Yes':
                artellapipe.logger.debug('Aborting Standin Export operation ...')
                return

        res = maya.cmds.confirmDialog(
            t='Exporting Standin File: {}'.format(out_folder),
            m='Are you sure you want to export standin files?\n\n' + '\n'.join([os.path.basename(f) for f in arnold_files]),
            button=['Yes', 'No'],
            defaultButton='Yes',
            cancelButton='No',
            dismissString='No'
        )

        if res != 'Yes':
            artellapipe.logger.debug('Aborting Standin Export operation ...')
            return

        if os.path.isfile(standin_file):
            res = maya.cmds.confirmDialog(
                t='Alembic File already exits!',
                m='Are you sure you want to overwrite exising Alembic file?\n\n{}'.format(standin_file),
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No',
                dismissString='No'
            )
            if res != 'Yes':
                artellapipe.logger.debug('Aborting Alembic Export operation ...')
                return

        sel = maya.cmds.ls(sl=True)

        if self.auto_sync_shaders.isChecked():
            print('This functionality is not working yet ....')
            # shaderlibrary.ShaderLibrary.load_all_scene_shaders()

        start_frame = self.start.value()
        end_frame = self.end.value()
        if end_frame < start_frame:
            end_frame = start_frame
        if start_frame == end_frame:
            if sel:
                maya.cmds.arnoldExportAss(
                    filename=standin_file,
                    s=True,
                    shadowLinks=1,
                    mask=2303,
                    ll=1,
                    boundingBox=True
                )
            else:
                maya.cmds.arnoldExportAss(
                    self.name_line.text(),
                    filename=standin_file,
                    shadowLinks=1,
                    mask=2303,
                    ll=1,
                    boundingBox=True
                )
        else:
            if sel:
                maya.cmds.arnoldExportAss(
                    filename=standin_file,
                    s=True,
                    shadowLinks=1,
                    mask=2303,
                    ll=1,
                    boundingBox=True,
                    startFrame=start_frame,
                    endFrame=end_frame,
                    frameStep=1.0
                )
            else:
                maya.cmds.arnoldExportAss(
                    self.name_line.text(),
                    filename=standin_file,
                    shadowLinks=1,
                    mask=2303,
                    ll=1,
                    boundingBox=True,
                    startFrame=start_frame,
                    endFrame=end_frame,
                    frameStep=1.0
                )
            maya.cmds.currentTime(start_frame, edit=True)


standinmanager.register_exporter(StandinExporter)
