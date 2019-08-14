#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Alembic Exporter
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import sys
import json

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpPyUtils import path as path_utils, folder as folder_utils

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters, stack

import artellapipe
from artellapipe.core import artellalib
from artellapipe.utils import alembic
from artellapipe.gui import waiter, spinner
from artellapipe.tools.tagger.core import taggerutils
from artellapipe.tools.alembicmanager import alembicmanager
from artellapipe.tools.alembicmanager.core import defines
from artellapipe.tools.alembicmanager.widgets import alembicgroup


class AlembicExporter(base.BaseWidget, object):

    showOk = Signal(str)
    showWarning = Signal(str)

    def __init__(self, project, parent=None):

        self._project = project

        super(AlembicExporter, self).__init__(parent=parent)

    def ui(self):
        super(AlembicExporter, self).ui()

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        exporter_widget = QWidget()
        exporter_layout = QVBoxLayout()
        exporter_layout.setContentsMargins(0, 0, 0, 0)
        exporter_layout.setSpacing(0)
        exporter_widget.setLayout(exporter_layout)
        self._stack.addWidget(exporter_widget)

        self._waiter = waiter.ArtellaWaiter(spinner_type=spinner.SpinnerType.Thumb)
        self._stack.addWidget(self._waiter)

        buttons_layout = QGridLayout()
        exporter_layout.addLayout(buttons_layout)
        export_tag_lbl = QLabel('Alembic Group: ')
        self._alembic_groups_combo = QComboBox()
        self._alembic_groups_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        buttons_layout.addWidget(export_tag_lbl, 0, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._alembic_groups_combo, 0, 1)

        name_lbl = QLabel('Alembic Name: ')
        self._name_line = QLineEdit()
        buttons_layout.addWidget(name_lbl, 1, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._name_line, 1, 1)

        shot_name_lbl = QLabel('Shot Name: ')
        self._shot_line = QLineEdit()
        buttons_layout.addWidget(shot_name_lbl, 2, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._shot_line, 2, 1)

        frame_range_lbl = QLabel('Frame Range: ')
        self._start = QSpinBox()
        self._start.setRange(-sys.maxint, sys.maxint)
        self._start.setFixedHeight(20)
        self._start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._end = QSpinBox()
        self._end.setRange(-sys.maxint, sys.maxint)
        self._end.setFixedHeight(20)
        self._end.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame_range_widget = QWidget()
        frame_range_layout = QHBoxLayout()
        frame_range_layout.setContentsMargins(2, 2, 2, 2)
        frame_range_layout.setSpacing(2)
        frame_range_widget.setLayout(frame_range_layout)
        for widget in [frame_range_lbl, self._start, self._end]:
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
        self._export_path_line = QLineEdit()
        self._export_path_line.setReadOnly(True)
        self._export_path_line.setText(self._project.get_path())
        self._export_path_btn = QPushButton()
        self._export_path_btn.setIcon(folder_icon)
        self._export_path_btn.setIconSize(QSize(18, 18))
        self._export_path_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0); border: 0px solid rgba(255,255,255,0);")
        export_path_layout.addWidget(self._export_path_line)
        export_path_layout.addWidget(self._export_path_btn)
        buttons_layout.addWidget(export_path_lbl, 4, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(export_path_widget, 4, 1)

        self._open_folder_after_export_cbx = QCheckBox('Open Folder After Export?')
        self._open_folder_after_export_cbx.setChecked(True)
        buttons_layout.addWidget(self._open_folder_after_export_cbx, 5, 1)

        exporter_layout.addLayout(splitters.SplitterLayout())

        export_layout = QHBoxLayout()
        self._export_btn = QPushButton('Export')
        self._export_btn.setIcon(artellapipe.resource.icon('export'))
        self._export_btn.setEnabled(False)
        export_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        export_layout.addWidget(self._export_btn)
        export_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        exporter_layout.addLayout(export_layout)

        exporter_layout.addLayout(splitters.SplitterLayout())

        self._tree_model = AlembicExporterGroupsModel(self)
        self._abc_tree = QTreeView()
        self._abc_tree.setModel(self._tree_model)
        exporter_layout.addWidget(self._abc_tree)

    def setup_signals(self):
        self._export_path_btn.clicked.connect(self._on_set_export_path)
        self._export_btn.clicked.connect(self._on_export)
        self._shot_line.textChanged.connect(self._on_update_tree)
        self._name_line.textChanged.connect(self._on_update_tree)
        self._alembic_groups_combo.currentIndexChanged.connect(self._on_update_tree)
        self._stack.animFinished.connect(self._on_stack_anim_finished)

    def refresh(self):
        """
        Function that update necessary info of the tool
        """

        self._tree_model.clean()
        self._refresh_alembic_groups()
        self._refresh_frame_ranges()
        self._refresh_shot_name()
        self._refresh_alembic_name()

    def get_selected_alembic_group(self):
        """
        Returns the name of the currently selected set
        :return: str
        """

        alembic_group_name = self._alembic_groups_combo.currentText()
        return alembic_group_name

    def get_alembic_group_nodes(self, abc_grp_name=None, show_error=True):
        """
        Returns a list of the nodes that are in the given alembic group name
        If no name given the name will be retrieved by the Alembic Group ComboBox
        :return:
        """

        if not tp.is_maya():
            artellapipe.logger.warning('DCC {} does not supports the retrieving of Alembic Group Nodes!'.format(tp.Dcc.get_name()))
            return None

        import maya.cmds as cmds

        if abc_grp_name:
            if not tp.Dcc.object_exists(abc_grp_name):
                raise Exception('ERROR: Invalid Alembic Group: {}'.format(abc_grp_name))
        else:
            abc_grp_name = self.get_selected_alembic_group()

        if not abc_grp_name:
            if show_error:
                tp.Dcc.confirm_dialog(
                    title='Error during Alembic Exportation',
                    message='No Alembic Group selected. Please select an Alembic Group from the list'
                )
            return None

        set_nodes = cmds.sets(abc_grp_name, q=True, no=True)
        if not set_nodes:
            if show_error:
                tp.Dcc.confirm_dialog(
                    title='Error during Alembic Exportation',
                    message='No members inside selected Alembic Group\n Alembic Group: {}'.format(abc_grp_name)
                )
            return None

        if set_nodes:
            set_nodes = sorted(set_nodes)

        return set_nodes

    def export_alembic(self, export_path, object_to_export=None, start_frame=1, end_frame=1):
        """
        Function that exports alembic in the given path
        :param export_path: str, path to export alembic into
        :param object_to_export: str, object to export (optional)
        :param start_frame: int, start frame when exporting animated Alembic caches
        :param end_frame: int, end frame when exporting animated Alembic caches
        """

        if not object_to_export or not tp.Dcc.object_exists(object_to_export):
            object_to_export = tp.Dcc.selected_nodes(False)
            if not object_to_export:
                self.show_warning.emit('Impossible to export Alembic from non-existent object {}'.format(object_to_export))
                return
            object_to_export = object_to_export[0]

        tp.Dcc.select_object(object_to_export)
        alembicgroup.AlembicGroup.create_alembic_group()
        self.refresh()

        self._alembic_groups_combo.setCurrentIndex(1)
        self._export_path_line.setText(export_path)
        self._start.setValue(start_frame)
        self._end.setValue(end_frame)
        self._on_export()

        tp.Dcc.new_file()

    def _refresh_alembic_name(self):
        """
        Internal function that updates Alembic name
        """

        if self._name_line.text() != '':
            return

        sel = tp.Dcc.selected_nodes()
        if sel:
            sel = sel[0]
            is_referenced = tp.Dcc.node_is_referenced(sel)
            if is_referenced:
                sel_namespace = tp.Dcc.node_namespace(sel)
                if not sel_namespace or not sel_namespace.startswith(':'):
                    pass
                else:
                    sel_namespace = sel_namespace[1:] + ':'
                    sel = sel.replace(sel_namespace, '')

            self._name_line.setText(tp.Dcc.node_short_name(sel))

    def _refresh_alembic_groups(self):
        """
        Internal function that updates the list of alembic groups
        """

        self._export_btn.setEnabled(False)

        filtered_sets = filter(lambda x: x.endswith(defines.ALEMBIC_GROUP_SUFFIX), tp.Dcc.list_nodes(node_type='objectSet'))
        filtered_sets.insert(0, '')
        self._alembic_groups_combo.blockSignals(True)
        try:
            self._alembic_groups_combo.clear()
            self._alembic_groups_combo.addItems(filtered_sets)
        except Exception:
            pass
        self._alembic_groups_combo.blockSignals(False)

    def _refresh_frame_ranges(self):
        """
        Internal function that updates the frame ranges values
        """

        frame_range = tp.Dcc.get_time_slider_range()
        self._start.setValue(int(frame_range[0]))
        self._end.setValue(int(frame_range[1]))

    def _refresh_shot_name(self):
        """
        Internal function that updates the shot name QLineEdit text
        """

        shot_name = ''
        current_scene = tp.Dcc.scene_name()
        if current_scene:
            current_scene = os.path.basename(current_scene)

        shot_regex = self._project.get_shot_name_regex()
        m = shot_regex.match(current_scene)
        if m:
            shot_name = m.group(1)

        self._shot_line.setText(shot_name)

    def _add_tag_attributes(self, attr_node, tag_node):
        # We add attributes to the first node in the list
        attrs = tp.Dcc.list_user_attributes(tag_node)
        tag_info = dict()
        for attr in attrs:
            try:
                tag_info[attr] = str(tp.Dcc.get_attribute_value(node=tag_info, attribute_name=attr))
            except Exception:
                pass
        if not tag_info:
            artellapipe.logger.warning('Node has not valid tag data: {}'.format(tag_node))
            return

        if not tp.Dcc.attribute_exists(node=attr_node, attribute_name='tag_info'):
            tp.Dcc.add_string_attribute(node=attr_node, attribute_name='tag_info', keyable=True)
        tp.Dcc.set_string_attribute_value(node=attr_node, attribute_name='tag_info', attribute_value=str(tag_info))

    def _get_tag_atributes_dict(self, tag_node):
        # We add attributes to the first node in the list
        tag_info = dict()
        if not tag_node:
            return tag_info

        attrs = tp.Dcc.list_user_attributes(tag_node)
        for attr in attrs:
            try:
                tag_info[attr] = tp.Dcc.get_attribute_value(node=tag_node, attribute_name=attr)
            except Exception:
                pass
        if not tag_info:
            artellapipe.logger.warning('Node has not valid tag data: {}'.format(tag_node))
            return

        return tag_info

    def _get_alembic_rig_export_list(self, root_node):
        export_list = list()
        root_node_child_count = root_node.childCount()
        if root_node_child_count > 0 or len(tp.Dcc.list_shapes(root_node.name)) > 0:
            for j in range(root_node.childCount()):
                c = root_node.child(j)
                c_name = c.name
                if type(c_name) in [list, tuple]:
                    c_name = c_name[0]
                if isinstance(c, AlembicExporterModelHires):
                    children = tp.Dcc.node_children(node=c_name, all_hierarchy=True, full_path=True)
                    export_list.extend(children)
                    export_list.append(c_name)

                    # if tag_node:
                    #     self._add_tag_attributes(c_name, tag_node)
                    # export_list.append(c_name)
                else:
                    if 'transform' != tp.Dcc.node_type(c_name):
                        xform = tp.Dcc.node_parent(node=c_name, full_path=True)
                        parent_xform = tp.Dcc.node_parent(node=xform, full_path=True)
                        if parent_xform:
                            children = tp.Dcc.node_children(node=parent_xform, all_hierarchy=True, full_path=True)
                            export_list.extend(children)
                    else:
                        children = tp.Dcc.node_children(node=c_name, all_hierarchy=True, full_path=True)
                        export_list.extend(children)

        for obj in reversed(export_list):
            if tp.Dcc.node_type(obj) != 'transform':
                export_list.remove(obj)
                continue
            is_visible = tp.Dcc.get_attribute_value(node=obj, attribute_name='visibility')
            if not is_visible:
                export_list.remove(obj)
                continue
            if tp.Dcc.attribute_exists(node=obj, attribute_name='displaySmoothMesh'):
                tp.Dcc.set_integer_attribute_value(node=obj, attribute_name='displaySmoothMesh', attribute_value=2)

        childs_to_remove = list()
        for obj in export_list:
            children = tp.Dcc.node_children(node=obj, all_hierarchy=True, full_path=True)
            shapes = tp.Dcc.list_children_shapes(node=obj, all_hierarchy=True, full_path=True)
            if children and not shapes:
                childs_to_remove.extend(children)

        if childs_to_remove:
            for obj in childs_to_remove:
                if obj in export_list:
                    export_list.remove(obj)

        return export_list

    def _export(self):
        """
        Internal function that exports Alembic
        """

        out_folder = self._export_path_line.text()
        if not os.path.exists(out_folder):
            tp.Dcc.confirm_dialog(
                title='Error during Alembic Exportation',
                message='Output Path does not exists: {}. Select a valid one!'.format(out_folder)
            )
            return

        abc_group_node = self._tree_model._root_node.child(0)
        if not tp.Dcc.object_exists(abc_group_node.name):
            raise Exception('ERROR: Invalid Alembic Group: {}'.format(abc_group_node.name))
        if abc_group_node.childCount() == 0:
            raise Exception('ERROR: Selected Alembic Group has no objects to export!')

        file_paths = list()

        export_info = list()
        for i in range(abc_group_node.childCount()):
            child = abc_group_node.child(i)
            export_path = os.path.normpath(out_folder + os.path.basename(child.name))
            file_paths.append(export_path)
            export_info.append({'path': export_path, 'node': child})

            # for j in range(root_tag_grp.childCount()):
            #     c = child.child(j)
            #     export_info[export_type]['path'] = export_path
        #

        res = tp.Dcc.confirm_dialog(
            title='Export Alembic File',
            message='Are you sure you want to export Alembic to files?\n\n' + '\n'.join([p for p in file_paths]),
            button=['Yes', 'No'],
            default_button='Yes',
            cancel_button='No',
            dismiss_string='No'
        )
        if res != 'Yes':
            artellapipe.logger.debug('Aborting Alembic Export operation ...')
            return

        self._export_alembics(export_info)

        self._stack.slide_in_index(0)

    def _export_alembics(self, alembic_nodes):

        def _recursive_hierarchy(transform):
            child_nodes = list()
            if not transform:
                return child_nodes
            transforms = tp.Dcc.list_relatives(node=transform, full_path=True)
            if not transforms:
                return child_nodes
            for eachTransform in transforms:
                if tp.Dcc.node_type(eachTransform) == 'transform':
                    child_nodes.append(eachTransform)
                    child_nodes.extend(_recursive_hierarchy(eachTransform))
            return child_nodes

        for n in alembic_nodes:
            export_path = n.get('path')
            abc_node = n.get('node')

            if os.path.isfile(export_path):
                res = tp.Dcc.confirm_dialog(
                    title='Alembic File already exits!',
                    message='Are you sure you want to overwrite already existing Alembic File?\n\n{}'.format(export_path),
                    button=['Yes', 'No'],
                    default_button='Yes',
                    cancel_button='No',
                    dismiss_string='No'
                )
                if res != 'Yes':
                    artellapipe.logger.debug('Aborting Alembic Export operation ...')
                    return

            export_list = list()
            all_nodes = list()
            tag_info = dict()

            child_count = abc_node.childCount()
            if not child_count:
                return

            for i in range(abc_node.childCount()):
                root_node = abc_node.child(i)
                root_node_name = root_node.name
                root_tag = taggerutils.get_tag_data_node_from_current_selection(root_node_name)
                root_tag_info = self._get_tag_atributes_dict(root_tag)
                if root_tag_info:
                    tag_info[tp.Dcc.node_short_name(root_node_name)] = root_tag_info
                    hires_grp = tp.Dcc.list_connections(node=root_tag, attribute_name='hires')
                    if hires_grp and tp.Dcc.object_exists(hires_grp[0]):
                        all_nodes.extend(_recursive_hierarchy(root_node_name))
                        export_list.extend(self._get_alembic_rig_export_list(root_node))
                    else:
                        all_nodes.extend(_recursive_hierarchy(root_node_name))
                        export_list.extend(tp.Dcc.list_children(root_node_name, all_hierarchy=False, full_path=True))
                else:
                    all_nodes.extend(_recursive_hierarchy(root_node_name))
                    children_nodes = tp.Dcc.list_children(root_node_name, all_hierarchy=False, full_path=True)
                    for child_node in children_nodes:
                        if tp.Dcc.check_object_type(child_node, 'shape', check_sub_types=True):
                            node_parent = tp.Dcc.node_parent(node=child_node)
                            export_list.append(node_parent)
                        else:
                            export_list.append(child_node)

            for node in all_nodes:
                if tp.Dcc.attribute_exists(node=node, attribute_name='displaySmoothMesh'):
                    tp.Dcc.set_integer_attribute_value(node=node, attribute_name='displaySmoothMesh', attribute_value=2)

            if not export_list:
                self.showWarning.emit('No geometry to export! Aborting Alembic Export operation ...')
                return

            geo_shapes = tp.Dcc.list_shapes(node=export_list)

            if not geo_shapes:
                children = tp.Dcc.list_children(node=export_list, all_hierarchy=True, full_path=True)
                if children:
                    for child in children:
                        geo_shapes = tp.Dcc.list_shapes(node=child)
                        if geo_shapes:
                            break

            if not geo_shapes:
                geo_shapes = list()
                for obj in export_list:
                    if tp.Dcc.check_object_type(obj, 'shape', check_sub_types=True):
                        geo_shapes.append(obj)

            if not geo_shapes:
                self.showWarning.emit('No geometry data to export! Aborting Alembic Export operation ...')
                return
            geo_shape = geo_shapes[0]

            # Retrieve all Arnold attributes to export from the first element of the list
            arnold_attrs = [attr for attr in tp.Dcc.list_attributes(geo_shape) if attr.startswith('ai')]

            artellalib.lock_file(export_path, True)

            valid_alembic = alembic.export(
                root=export_list,
                alembicFile=export_path,
                frameRange=[[float(self._start.value()), float(self._end.value())]],
                userAttr=arnold_attrs,
                uvWrite=True,
                writeUVSets=True,
                writeCreases=True
            )
            if not valid_alembic:
                artellapipe.logger.warning('Error while exporting Alembic file: {}'.format(export_path))
                return

            tag_json_file = abc_node.name.replace('.abc', '_abc.info')
            with open(tag_json_file, 'w') as f:
                json.dump(tag_info, f)

            if self._open_folder_after_export_cbx.isChecked():
                folder_utils.open_folder(os.path.dirname(export_path))

            for n in export_list:
                if tp.Dcc.attribute_exists(node=n, attribute_name='tag_info'):
                    try:
                        tp.Dcc.delete_attribute(node=n, attribute_name='tag_info')
                    except Exception as e:
                        pass

            self.showOk.emit('Alembic File: {} exported successfully!'.format(os.path.basename(abc_node.name)))

    def _on_set_export_path(self):
        """
        Internal function that is calledd when the user selects the folder icon
        Allows the user to select a path to export Alembic group contents
        """

        res = tp.Dcc.select_file_dialog(title='Select Alembic Export Folder', start_directory=self._project.get_path())
        if not res:
            return

        self._export_path_line.setText(res)

    def _on_update_tree(self, index, show_error=False):
        set_text = self.get_selected_alembic_group()

        self._tree_model.clean()

        # Add selected Alembic Group to the tree root node
        abc_group_node = AlembicExporterGroupNode(name=set_text)
        self._tree_model._root_node.addChild(abc_group_node)

        abc_group_objs = self.get_alembic_group_nodes(set_text, show_error)
        if not abc_group_objs:
            if set_text != '':
                artellapipe.logger.warning('Selected Alembic Group is empty: {}'.format(set_text))
            return

        exports_dict = dict()

        for obj in abc_group_objs:
            tag_node = taggerutils.get_tag_data_node_from_current_selection(obj)
            if tag_node:
                attr_exists = tp.Dcc.attribute_exists(node=tag_node, attribute_name='hires')
                if not attr_exists:
                    hires_objs = tp.Dcc.list_relatives(node=obj, all_hierarchy=True, full_path=True, relative_type='mesh')
                    if not hires_objs:
                        obj_meshes = [obj]
                    else:
                        obj_meshes = hires_objs
                else:
                    hires_grp = tp.Dcc.list_connections(node=tag_node, attribute_name='hires')
                    if hires_grp and tp.Dcc.object_exists(hires_grp[0]):
                        hires_objs = tp.Dcc.list_relatives(node=hires_grp, all_hierarchy=True, full_path=True, relative_type='mesh')
                    else:
                        hires_objs = tp.Dcc.list_relatives(node=obj, all_hierarchy=True, full_path=True, relative_type='mesh')
                    if not hires_objs:
                        obj_meshes = [obj]
                    else:
                        obj_meshes = hires_objs
            else:
                # obj_meshes = [obj]
                obj_meshes = tp.Dcc.list_relatives(node=obj, all_hierarchy=True, full_path=True, relative_type='mesh')

            exports_dict[obj] = list()
            for o in obj_meshes:
                if o not in exports_dict:
                    exports_dict[obj].append(o)

        if not exports_dict:
            artellapipe.logger.warning('No objects in Alembic Groups to export')
            return

        shot_name = self._shot_line.text()
        shot_regex = self._project.get_shot_name_regex()
        m = shot_regex.match(shot_name)
        if m:
            shot_name = m.group(1)
        else:
            if self._shot_line.text():
                shot_name = 'Undefined'
            else:
                shot_name = ''

        out_folder = self._export_path_line.text()
        if not os.path.exists(out_folder):
            artellapipe.logger.warning(
                'Output Path does not exists: {}. Select a valid one!'.format(out_folder)
            )
            return

        is_referenced = tp.Dcc.node_is_referenced(set_text)
        if is_referenced:
            set_namespace = tp.Dcc.node_namespace(set_text)
            if not set_namespace or not set_namespace.startswith(':'):
                export_name = set_text
            else:
                set_namespace = set_namespace[1:] + ':'
                export_name = set_text.replace(set_namespace, '')
        else:
            export_name = set_text

        export_name = export_name.replace(defines.ALEMBIC_GROUP_SUFFIX, '')

        abc_name = self._name_line.text()
        if not abc_name:
            abc_name = export_name

        if shot_name:
            anim_path = '{}_{}'.format(shot_name, abc_name+'.abc')
            filename = os.path.normpath(os.path.join(out_folder, shot_name, anim_path))
        else:
            anim_path = '{}'.format(abc_name+'.abc')
            filename = os.path.normpath(os.path.join(out_folder, anim_path))

        anim_node = AlembicNode(path_utils.get_relative_path(filename, self._project.get_path()))
        abc_group_node.addChild(anim_node)
        for obj, geo_list in exports_dict.items():
            root_grp = AlembicExporterNode(obj)
            anim_node.addChild(root_grp)
            tag_node = taggerutils.get_tag_data_node_from_current_selection(obj)
            has_hires = tp.Dcc.attribute_exists(node=tag_node, attribute_name='hires') if tag_node else None
            if tag_node and has_hires:
                hires_grp = tp.Dcc.list_connections(node=tag_node, attribute_name='hires')
                if hires_grp and tp.Dcc.object_exists(hires_grp[0]):
                    hires_node = AlembicExporterModelHires(hires_grp)
                    root_grp.addChild(hires_node)
                    for model in geo_list:
                        model_xform = tp.Dcc.node_parent(node=model, full_path=True)
                        obj_is_visible = tp.Dcc.get_attribute_value(node=model_xform, attribute_name='visibility')
                        if not obj_is_visible:
                            continue
                        obj_node = AlembicExporterNode(model)
                        hires_node.addChild(obj_node)
                else:
                    for geo in geo_list:
                        geo_node = AlembicExporterNode(geo)
                        root_grp.addChild(geo_node)
            else:
                for geo in geo_list:
                    geo_node = AlembicExporterNode(geo)
                    root_grp.addChild(geo_node)

        self._export_btn.setEnabled(True)

        self._abc_tree.expandAll()

    def _on_stack_anim_finished(self, index):
        """
        Internal callback function that is called when stack animation finishes
        :param index:
        :return:
        """

        if index == 1:
            self._export()

    def _on_export(self):
        """
        Internal callback function that is called when the user presses Export button
        """

        self._stack.slide_in_index(1)


class AlembicExporterGroupsModel(QAbstractItemModel, object):

    sortRole = Qt.UserRole
    filterRole = Qt.UserRole + 1

    def __init__(self, parent=None):
        super(AlembicExporterGroupsModel, self).__init__(parent)
        self._root_node = AlembicExporterNode('Root')
        self._root_node.model = self

    def rowCount(self, parent):
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()

        return parent_node.childCount()

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        if not node:
            return

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return node.data(index.column())
        elif role == Qt.DecorationRole:
            resource = node.resource()
            return QIcon(QPixmap(resource))

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid():
            node = index.internalPointer()
            if role == Qt.EditRole:
                node.setData(index.column(), value)
                self.dataChanged.emit(index, index)
                return True

        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if section == 0:
                return 'Alembic'
            else:
                return 'Type'

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, index):
        node = self.get_node(index)
        parent_node = node.parent()
        if parent_node == self._root_node:
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        parent_node = self.get_node(parent)

        child_item = parent_node.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def insertRows(self, pos, rows, parent=QModelIndex()):
        parent_node = self.get_node(parent)
        self.beginInsertRows(parent, pos, pos + rows - 1)
        for row in range(rows):
            child_count = parent_node.childCount()
            child_node = AlembicExporterNode('Untitled'+str(child_count))
            success = parent_node.insertChild(pos, child_node)
        self.endInsertRows()

        return success

    def removeRows(self, pos, rows, parent=QModelIndex()):
        parent_node = self.get_node(parent)
        self.beginRemoveRows(parent, pos, pos + rows - 1)
        for row in range(rows):
            success = parent_node.removeChild(pos)
        self.endRemoveRows()

        return success

    def get_node(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self._root_node

    def clean(self):
        for child_index in range(self._root_node.childCount()):
            self._root_node.removeChild(child_index)


class AlembicExporterNode(object):
    def __init__(self, name, parent=None):

        super(AlembicExporterNode, self).__init__()

        self._name = name
        self._children = []
        self._parent = parent
        self.model = None

        if parent is not None:
            parent.addChild(self)

    def attrs(self):

        classes = self.__class__.__mro__

        kv = {}

        for cls in classes:
            for k, v in cls.__dict__.iteritems():
                if isinstance(v, property):
                    print("Property:", k.rstrip("_"), "\n\tValue:", v.fget(self))
                    kv[k] = v.fget(self)

        return kv

    def typeInfo(self):
        return 'node'

    def addChild(self, child):
        self.model.layoutAboutToBeChanged.emit()
        self._children.append(child)
        child._parent = self
        child.model = self.model
        self.model.layoutChanged.emit()

    def insertChild(self, position, child):

        if position < 0 or position > len(self._children):
            return False

        self.model.layoutAboutToBeChanged.emit()
        self._children.insert(position, child)
        child._parent = self
        child.model = self.model
        self.model.layoutChanged.emit()

        return True

    def removeChild(self, position):

        if position < 0 or position > len(self._children):
            return False

        self.model.layoutAboutToBeChanged.emit()
        child = self._children.pop(position)
        child._parent = None
        child.model = None
        self.model.layoutChanged.emit()

        return True

    def name():
        def fget(self): return self._name

        def fset(self, value): self._name = value

        return locals()

    name = property(**name())

    def child(self, row):
        return self._children[row]

    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tabLevel=-1):

        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "\t"

        output += "|------" + self._name + "\n"

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"

        return output

    def __repr__(self):
        return self.log()

    def data(self, column):

        if column is 0:
            long_name = self.name
            # try:
            #     return long_name.split(':')[-1].split('|')[-1]
            # except Exception:
            return long_name
        elif column is 1:
            return self.typeInfo()

    def setData(self, column, value):
        if column is 0:
            self.name = value.toPyObject()
        elif column is 1:
            pass

    def resource(self):
        pass


class AlembicExporterGroupNode(AlembicExporterNode, object):
    def __init__(self, name, parent=None):
        super(AlembicExporterGroupNode, self).__init__(name=name, parent=parent)


class AlembicNode(AlembicExporterNode, object):
    def __init__(self, name, parent=None):
        super(AlembicNode, self).__init__(name=name, parent=parent)

    def resource(self):
        path = artellapipe.resource.get('icons', 'alembic_white_icon.png')
        return path


class AlembicExporterModelHires(AlembicExporterNode, object):
    def __init__(self, name, parent=None):
        super(AlembicExporterModelHires, self).__init__(name=name, parent=parent)


alembicmanager.register_exporter(AlembicExporter)

