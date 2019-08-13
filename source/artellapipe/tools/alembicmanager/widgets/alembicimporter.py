#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Alembic Importer for Solstice
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import json
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from artellapipe.utils import alembic
from tpQtLib.widgets import splitters

import artellapipe

from artellapipe.tools.alembicmanager.core import defines

if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import scene as maya_scene
elif tp.is_houdini():
    import hou


class AlembicImporter(base.BaseWidget, object):

    showOk = Signal(str)

    def __init__(self, project, parent=None):

        self._project = project
        
        super(AlembicImporter, self).__init__(parent=parent)

    def ui(self):
        super(AlembicImporter, self).ui()

        buttons_layout = QGridLayout()
        self.main_layout.addLayout(buttons_layout)

        shot_name_lbl = QLabel('Shot Name: ')
        self._shot_line = QLineEdit()
        buttons_layout.addWidget(shot_name_lbl, 1, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._shot_line, 1, 1)
        shot_name_lbl.setVisible(False)
        self._shot_line.setVisible(False)

        folder_icon = artellapipe.resource.icon('folder')
        alembic_path_layout = QHBoxLayout()
        alembic_path_layout.setContentsMargins(2, 2, 2, 2)
        alembic_path_layout.setSpacing(2)
        alembic_path_widget = QWidget()
        alembic_path_widget.setLayout(alembic_path_layout)
        alembic_path_lbl = QLabel('Alembic File: ')
        self._alembic_path_line = QLineEdit()
        self._alembic_path_line.setReadOnly(True)
        self._alembic_path_btn = QPushButton()
        self._alembic_path_btn.setIcon(folder_icon)
        self._alembic_path_btn.setIconSize(QSize(18, 18))
        self._alembic_path_btn.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0); border: 0px solid rgba(255,255,255,0);")
        alembic_path_layout.addWidget(self._alembic_path_line)
        alembic_path_layout.addWidget(self._alembic_path_btn)
        buttons_layout.addWidget(alembic_path_lbl, 2, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(alembic_path_widget, 2, 1)

        import_mode_layout = QHBoxLayout()
        import_mode_layout.setContentsMargins(2, 2, 2, 2)
        import_mode_layout.setSpacing(2)
        import_mode_widget = QWidget()
        import_mode_widget.setLayout(import_mode_layout)
        import_mode_lbl = QLabel('Import mode: ')
        self._create_radio = QRadioButton('Create')
        self._add_radio = QRadioButton('Add')
        self._merge_radio = QRadioButton('Merge')
        self._create_radio.setChecked(True)
        import_mode_layout.addWidget(self._create_radio)
        import_mode_layout.addWidget(self._add_radio)
        import_mode_layout.addWidget(self._merge_radio)
        buttons_layout.addWidget(import_mode_lbl, 3, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(import_mode_widget, 3, 1)
        import_mode_lbl.setVisible(False)
        import_mode_widget.setVisible(False)

        auto_display_lbl = QLabel('Auto Display Smooth?: ')
        self._auto_smooth_display = QCheckBox()
        self._auto_smooth_display.setChecked(True)
        buttons_layout.addWidget(auto_display_lbl, 4, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._auto_smooth_display, 4, 1)

        if tp.is_houdini():
            hou_archive_abc_node_lbl = QLabel('Import Alembic as Archive?')
            self._hou_archive_abc_node_cbx = QCheckBox()
            buttons_layout.addWidget(hou_archive_abc_node_lbl, 5, 0, 1, 1, Qt.AlignRight)
            buttons_layout.addWidget(self._hou_archive_abc_node_cbx, 5, 1)

        self.main_layout.addLayout(splitters.SplitterLayout())

        self.merge_abc_widget = QWidget()
        self.merge_abc_widget.setVisible(False)
        merge_abc_layout = QVBoxLayout()
        merge_abc_layout.setContentsMargins(2, 2, 2, 2)
        merge_abc_layout.setSpacing(2)
        self.merge_abc_widget.setLayout(merge_abc_layout)
        self.main_layout.addWidget(self.merge_abc_widget)

        merge_abc_layout.addWidget(splitters.Splitter('Select Alembic Group to merge into'))

        alembic_set_lbl = QLabel('Alembic Groups')
        self.alembic_groups_combo = QComboBox()
        self.alembic_groups_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        abc_layout = QHBoxLayout()
        abc_layout.setContentsMargins(2, 2, 2, 2)
        abc_layout.setSpacing(2)
        abc_layout.addWidget(alembic_set_lbl)
        abc_layout.addWidget(self.alembic_groups_combo)
        merge_abc_layout.addLayout(abc_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)
        self._import_btn = QPushButton('Import')
        self._import_btn.setIcon(artellapipe.resource.icon('import'))
        self._import_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._reference_btn = QPushButton('Reference')
        self._reference_btn.setIcon(artellapipe.resource.icon('reference'))
        self._reference_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        buttons_layout.addWidget(self._import_btn)
        buttons_layout.addWidget(self._reference_btn)

        if tp.is_houdini():
            self._reference_btn.setEnabled(False)

    def setup_signals(self):
        self._create_radio.clicked.connect(self._on_mode_changed)
        self._add_radio.clicked.connect(self._on_mode_changed)
        self._merge_radio.clicked.connect(self._on_mode_changed)
        self._alembic_path_btn.clicked.connect(self._on_browse_alembic)
        self._import_btn.clicked.connect(self._on_import_alembic)
        self._reference_btn.clicked.connect(partial(self._on_import_alembic, True))

        self._on_mode_changed()

    def refresh(self):
        """
        Function that update necessary info of the tool
        """

        self._refresh_alembic_groups()
        self._refresh_shot_name()

    def _refresh_alembic_groups(self):
        """
        Internal function that updates the list of alembic groups
        """

        filtered_sets = filter(lambda x: x.endswith(defines.ALEMBIC_GROUP_SUFFIX), tp.Dcc.list_nodes(node_type='objectSet'))
        filtered_sets.insert(0, '')
        self.alembic_groups_combo.blockSignals(True)
        try:
            self.alembic_groups_combo.clear()
            self.alembic_groups_combo.addItems(filtered_sets)
        except Exception:
            pass
        self.alembic_groups_combo.blockSignals(False)

    def _refresh_shot_name(self):
        """
        Internal function that updates the shot name QLineEdit text
        """

        shot_name = 'Undefined'
        current_scene = tp.Dcc.scene_path()
        if current_scene:
            current_scene = os.path.basename(current_scene)

        shot_regex = self._project.get_shot_name_regex()
        m = shot_regex.match(current_scene)
        if m:
            shot_name = m.group(1)

        self._shot_line.setText(shot_name)

    def _on_mode_changed(self):
        self.merge_abc_widget.setVisible(self._merge_radio.isChecked())

    def _on_browse_alembic(self):

        shot_name = self._shot_line.text()
        abc_folder = os.path.normpath(os.path.join(self._project.get_path(), shot_name)) if shot_name != 'unresolved' else self._project.get_path()

        pattern = 'Alembic Files (*.abc)'
        if tp.is_houdini():
            pattern = '*.abc'
        abc_file = tp.Dcc.select_file_dialog(title='Select Alembic to Import', start_directory=abc_folder, pattern=pattern)
        if abc_file:
            self._alembic_path_line.setText(abc_file)

    @classmethod
    def import_alembic(cls, project, alembic_path, parent=None, unresolve_path=False):
        if not alembic_path or not os.path.isfile(alembic_path):
            artellapipe.logger.warning('Alembic file {} does not exits!'.format(alembic_path))
            return None

        tag_json_file = os.path.join(os.path.dirname(alembic_path), os.path.basename(alembic_path).replace('.abc', '_abc.info'))
        valid_tag_info = True
        if os.path.isfile(tag_json_file):
            with open(tag_json_file, 'r') as f:
                tag_info = json.loads(f.read())
            if not tag_info:
                artellapipe.logger.warning('No Alembic Info loaded!')
                valid_tag_info = False
        else:
            artellapipe.logger.warning('No Alembic Info file found! Take into account that imported Alembic is not supported by our current pipeline!')
            valid_tag_info = False

        if tp.Dcc.is_houdini():
            import hou
            n = hou.node('obj')
            parent = n.createNode('alembicarchive')
        if parent and valid_tag_info:
            cls._add_tag_info_data(tag_info=tag_info, attr_node=parent)

        res = alembic.import_alembic(project, alembic_path, mode='import', nodes=None, parent=parent, unresolve_path=unresolve_path)

        return res

    @staticmethod
    def reference_alembic(project, alembic_path, namespace=None, unresolve_path=False):

        if not tp.is_maya():
            artellapipe.logger.warning('DCC {} does not supports the reference of Alembic groups!'.format(tp.Dcc.get_name()))
            return None

        if not alembic_path or not os.path.isfile(alembic_path):
            artellapipe.logger.warning('Alembic file {} does not exits!'.format(alembic_path))
            return None

        abc_name = os.path.basename(alembic_path).split('.')[0]
        tag_json_file = os.path.join(os.path.dirname(alembic_path), os.path.basename(alembic_path).replace('.abc', '_abc.info'))
        if not os.path.isfile(tag_json_file):
            artellapipe.logger.warning('No Alembic Info file found!')
            return

        with open(tag_json_file, 'r') as f:
            tag_info = json.loads(f.read())
        if not tag_info:
            artellapipe.logger.warning('No Alembic Info loaded!')
            return

        root = tp.Dcc.create_empty_group(name=abc_name)
        AlembicImporter._add_tag_info_data(tag_info, root)
        sel = [root]
        sel = sel or None

        track_nodes = maya_scene.TrackNodes()
        track_nodes.load()

        if not namespace:
            namespace = abc_name

        valid_reference = alembic.reference_alembic(project=project, alembic_file=alembic_path, namespace=namespace, unresolve_path=unresolve_path)
        if not valid_reference:
            artellapipe.logger.warning('Error while reference Alembic file: {}'.format(alembic_path))
            return
        res = track_nodes.get_delta()
        for obj in res:
            if not tp.Dcc.object_exists(obj):
                continue
            if not tp.Dcc.node_type(obj) == 'transform':
                continue
            obj_parent = tp.Dcc.node_parent(obj)
            if obj_parent:
                continue
            tp.Dcc.set_parent(obj, sel[0])

    def _on_import_alembic(self, as_reference=False):
        abc_file = self._alembic_path_line.text()
        if not abc_file or not os.path.isfile(abc_file):
            tp.Dcc.confirm_dialog(title='Error', message='No Alembic File is selected or file is not currently available in disk')
            return None

        sel_set = self.alembic_groups_combo.currentText()
        if self._merge_radio.isChecked() and not sel_set:
            tp.Dcc.confirm_dialog(title='Error', message='No Alembic Group selected. Please create the Alembic Group first and retry')
            return None

        nodes = None
        if tp.is_maya() and sel_set:
            nodes = sorted(maya.cmds.sets(sel_set, query=True, no=True))

        abc_name = os.path.basename(abc_file).split('.')[0]
        tag_json_file = os.path.join(os.path.dirname(abc_file), os.path.basename(abc_file).replace('.abc', '_abc.info'))
        valid_tag_info = True
        if os.path.isfile(tag_json_file):
            with open(tag_json_file, 'r') as f:
                tag_info = json.loads(f.read())
            if not tag_info:
                artellapipe.logger.warning('No Alembic Info loaded!')
                valid_tag_info = False
        else:
            artellapipe.logger.warning('No Alembic Info file found!')
            valid_tag_info = False

        # if not valid_tag_info:
        #     return

        sel = None
        root_to_add = None
        if self._create_radio.isChecked():
            if tp.is_maya():
                root = tp.Dcc.create_empty_group(name=abc_name)
                root_to_add = root
            elif tp.is_houdini():
                n = hou.node('obj')
                if self._hou_archive_abc_node_cbx.isChecked():
                    root = n.createNode('alembicarchive', node_name=abc_name)
                else:
                    geo = n.createNode('geo', node_name=abc_name)
                    root = geo.createNode('alembic', node_name=abc_name)
                root_to_add = root
            # if valid_tag_info:
            #     self._add_tag_info_data(tag_info, root)
            sel = [root]
        else:
            sel = tp.Dcc.selected_nodes(full_path=True)
            if not sel:
                if valid_tag_info:
                    sel = tp.Dcc.create_empty_group(name=abc_name)
                    root_to_add = sel
                    # if valid_tag_info:
                    #     self._add_tag_info_data(tag_info, sel)

        sel = sel or None

        if tp.is_maya():
            track_nodes = maya_scene.TrackNodes()
            track_nodes.load()

        all_nodes = None

        if as_reference:
            if tp.is_maya():
                res = alembic.reference_alembic(project=self._project, alembic_file=abc_file, namespace=abc_name)
                if not res:
                    artellapipe.logger.warning('Error while reference Alembic file: {}'.format(abc_file))
                    return
                all_nodes = track_nodes.get_delta()
                for obj in all_nodes:
                    if not tp.Dcc.object_exists(obj):
                        continue
                    if not tp.Dcc.node_type(obj) == 'transform':
                        continue
                    obj_parent = tp.Dcc.node_parent(obj)
                    if obj_parent:
                        continue
                    tp.Dcc.set_parent(node=obj, parent=sel[0])
            else:
                artellapipe.logger.warning('Alembic Reference is only supported in Maya!')
                return None
        else:
            if valid_tag_info:
                res = alembic.import_alembic(project=self._project, alembic_file=abc_file, mode='import', nodes=nodes, parent=sel[0])
            else:
                if tp.is_houdini():
                    res = alembic.import_alembic(project=self._project, alembic_file=abc_file, mode='import', parent=root_to_add)
                else:
                    res = alembic.import_alembic(project=self._project, alembic_file=abc_file, mode='import')
            res = [res]

            if tp.is_maya():
                all_nodes = track_nodes.get_delta()

        added_tag = False
        for key in tag_info.keys():
            if all_nodes:
                for obj in all_nodes:
                    short_obj = tp.Dcc.node_short_name(obj)
                    if key == short_obj:
                        self._add_tag_info_data(tag_info[key], obj)
                        added_tag = True
                    # elif '{}_hires_grp'.format(key) == short_obj:
                    #     self._add_tag_info_data(tag_info[key], obj)
                    #     added_tag = True

        if not added_tag and root_to_add:
            self._add_tag_info_data(tag_info, root_to_add)

        if self._auto_smooth_display.isChecked():
            if all_nodes:
                for obj in all_nodes:
                    if obj and tp.Dcc.object_exists(obj):
                        if tp.Dcc.node_type(obj) == 'shape':
                            if tp.Dcc.attribute_exists(node=obj, attribute_name='aiSubdivType'):
                                tp.Dcc.set_integer_attribute_value(node=obj, attribute_name='aiSubdivType', attribute_value=1)
                        elif tp.Dcc.node_type(obj) == 'transform':
                            shapes = tp.Dcc.list_shapes(node=obj, full_path=True)
                            if not shapes:
                                continue
                            for s in shapes:
                                if tp.Dcc.attribute_exists(node=s, attribute_name='aiSubdivType'):
                                    tp.Dcc.set_integer_attribute_value(node=s, attribute_name='aiSubdivType', attribute_value=1)

        if res:
            if as_reference:
                self.showOk.emit('Alembic file referenced successfully!')
            else:
                self.showOk.emit('Alembic file imported successfully!')

        return all_nodes

    @staticmethod
    def _add_tag_info_data(tag_info, attr_node):
        if tp.is_maya():
            if not tp.Dcc.attribute_exists(node=attr_node, attribute_name='tag_info'):
                tp.Dcc.add_string_attribute(node=attr_node, attribute_name='tag_info', keyable=True)
            tp.Dcc.set_string_attribute_value(node=attr_node, attribute_name='tag_info', attribute_value=str(tag_info))
        elif tp.is_houdini():
            import hou
            parm_group = attr_node.parmTemplateGroup()
            parm_folder = hou.FolderParmTemplate('folder', 'Solstice Info')
            parm_folder.addParmTemplate(hou.StringParmTemplate('tag_info', 'Tag Info', 1))
            parm_group.append(parm_folder)
            attr_node.setParmTemplateGroup(parm_group)
            attr_node.parm('tag_info').set(str(tag_info))
