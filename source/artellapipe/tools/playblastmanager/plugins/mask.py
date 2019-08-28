#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Time Range Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import ast

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpQtLib.widgets import splitters, button

import tpDccLib as tp

import artellapipe
from artellapipe.tools.playblastmanager.core import plugin

if tp.is_maya():
    import tpMayaLib as maya


class MaskTextAlignment(object):
    TopLeft = ['topLeftText', 'tlt']
    TopCenter = ['topCenterText', 'tct']
    TopRight = ['topRightText', 'trt']
    BottomLeft = ['bottomLeftText', 'blt']
    BottomCenter = ['bottomCenterText', 'bct']
    BottomRight = ['bottomRightText', 'brt']


class MaskObject(object):

    mask_plugin = 'playblast.py'
    mask_node = 'CameraMask'
    mask_transform = 'cameramask'
    mask_shape = 'cameramask_shape'

    def __init__(self):
        super(MaskObject, self).__init__()

    @classmethod
    def create_mask(cls):
        if tp.Dcc.is_plugin_loaded(plugin_name=cls.mask_plugin):
            try:
                tp.Dcc.load_plugin(os.path.realpath(__file__).replace('.pyc', '.py'))
            except Exception as e:
                artellapipe.logger.error('Failed to load SolsticeMask plugin! | {}'.format(str(e)))
                artellapipe.logger.debug('Please import {} plugin manually!'.format(cls.mask_plugin))
                return

        if not cls.get_mask():
            transform_node = tp.Dcc.create_node(node_type='transform', node_name=cls.mask_transform)
            maya.cmds.createNode(cls.mask_node, name=cls.mask_shape, parent=transform_node)

        cls.refresh_mask()

    @classmethod
    def get_mask(cls):
        if tp.Dcc.is_plugin_loaded(cls.mask_plugin):
            nodes = maya.cmds.ls(type=cls.mask_node)
            if len(nodes) > 0:
                return nodes[0]

        return None

    @classmethod
    def delete_mask(cls):
        mask = cls.get_mask()
        if mask:
            transform = maya.cmds.listRelatives(mask, fullPath=True, parent=True)
            if transform:
                tp.Dcc.delete_object(transform)
            else:
                tp.Dcc.delete_object(mask)

    @classmethod
    def get_camera_name(cls):
        if maya.cmds.optionVar(exists='solstice_playblast_camera'):
            return maya.cmds.optionVar(query='solstice_playblast_camera')
        else:
            return ''

    @classmethod
    def get_label_text(cls):
        if maya.cmds.optionVar(exists='solstice_mask_'):
            pass

    @classmethod
    def refresh_mask(cls):
        mask = cls.get_mask()
        if not mask:
            return

        tp.Dcc.set_string_attribute_value(node=mask, attribute_name='camera', attribute_value=cls.get_camera_name())


class MaskWidget(plugin.PlayblastPlugin, object):

    id = 'Mask'
    label = 'Mask'

    def __init__(self, project, parent=None):
        super(MaskWidget, self).__init__(project=project, parent=parent)

        self._mask = None

    def ui(self):
        super(MaskWidget, self).ui()

        enable_layout = QHBoxLayout()
        enable_layout.setContentsMargins(0, 0, 0, 0)
        enable_layout.setSpacing(2)

        self.enable_mask_cbx = QCheckBox('Enable')
        self.enable_mask_cbx.setEnabled(True)
        create_mask_btn = QPushButton('Create')
        delete_mask_btn = QPushButton('Delete')

        enable_layout.addWidget(self.enable_mask_cbx)
        enable_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        enable_layout.addLayout(splitters.SplitterLayout())
        enable_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        enable_layout.addWidget(create_mask_btn)
        enable_layout.addWidget(delete_mask_btn)

        self.main_layout.addLayout(enable_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())

        labels_layout = QVBoxLayout()
        labels_group = QGroupBox('Labels')
        labels_group.setLayout(labels_layout)
        self.main_layout.addWidget(labels_group)

        grid_layout = QGridLayout()
        labels_layout.addLayout(grid_layout)

        top_left_lbl = QLabel('Top Left: ')
        top_center_lbl = QLabel('Top Center: ')
        top_right_lbl = QLabel('Top Right: ')
        bottom_left_lbl = QLabel('Bottom Left: ')
        bottom_center_lbl = QLabel('Bottom Center: ')
        bottom_right_lbl = QLabel('Bottom Right: ')
        padding_text_lbl = QLabel('Text Padding: ')
        font_lbl = QLabel('Font: ')
        color_lbl = QLabel('Color: ')
        alpha_lbl = QLabel('Transparency: ')
        scale_lbl = QLabel('Scale: ')

        self.top_left_line = QLineEdit()
        self.top_center_line = QLineEdit()
        self.top_right_line = QLineEdit()
        self.bottom_left_line = QLineEdit()
        self.bottom_center_line = QLineEdit()
        self.bottom_right_line = QLineEdit()
        self.padding_text_spn = QSpinBox()
        self.font_line = QLineEdit()
        self.font_line.setReadOnly(True)
        self.font_line.setText('Consolas')
        self.font_btn = QPushButton('...')
        self.color_btn = button.ColorButton(colorR=1, colorG=1, colorB=1)
        self.alpha_btn = button.ColorButton(colorR=1, colorG=1, colorB=1)
        self.scale_spn = QDoubleSpinBox()
        self.scale_spn.setRange(0.1, 2.0)
        self.scale_spn.setValue(1.0)
        self.scale_spn.setSingleStep(0.01)
        self.scale_spn.setDecimals(2)
        self.scale_spn.setMaximumWidth(80)

        grid_layout.addWidget(top_left_lbl, 0, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(top_center_lbl, 1, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(top_right_lbl, 2, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(bottom_left_lbl, 3, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(bottom_center_lbl, 4, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(bottom_right_lbl, 5, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(padding_text_lbl, 6, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(font_lbl, 7, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(color_lbl, 8, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(alpha_lbl, 9, 0, alignment=Qt.AlignLeft)
        grid_layout.addWidget(scale_lbl, 10, 0, alignment=Qt.AlignLeft)

        grid_layout.addWidget(self.top_left_line, 0, 1)
        grid_layout.addWidget(self.top_center_line, 1, 1)
        grid_layout.addWidget(self.top_right_line, 2, 1)
        grid_layout.addWidget(self.bottom_left_line, 3, 1)
        grid_layout.addWidget(self.bottom_center_line, 4, 1)
        grid_layout.addWidget(self.bottom_right_line, 5, 1)
        grid_layout.addWidget(self.padding_text_spn, 6, 1)
        grid_layout.addWidget(self.font_line, 7, 1)
        grid_layout.addWidget(self.font_btn, 7, 2)
        grid_layout.addWidget(self.color_btn, 8, 1)
        grid_layout.addWidget(self.alpha_btn, 9, 1)
        grid_layout.addWidget(self.scale_spn, 10, 1)

        self.main_layout.addLayout(splitters.SplitterLayout())

        # ========================================================================

        borders_layout = QVBoxLayout()
        borders_layout.setAlignment(Qt.AlignLeft)
        borders_group = QGroupBox('Borders')
        borders_group.setLayout(borders_layout)
        self.main_layout.addWidget(borders_group)

        cbx_layout = QHBoxLayout()
        grid_layout_2 = QGridLayout()
        borders_layout.addLayout(cbx_layout)
        borders_layout.addLayout(grid_layout_2)

        border_color_lbl = QLabel('Color: ')
        border_alpha_lbl = QLabel('Transparency: ')
        border_scale_lbl = QLabel('Scale: ')

        self.top_cbx = QCheckBox('Top')
        self.top_cbx.setChecked(True)
        self.bottom_cbx = QCheckBox('Bottom')
        self.bottom_cbx.setChecked(True)
        cbx_layout.addWidget(self.top_cbx)
        cbx_layout.addWidget(self.bottom_cbx)

        self.border_color_btn = button.ColorButton(colorR=0, colorG=0, colorB=0)
        self.border_color_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.border_alpha_btn = button.ColorButton(colorR=1, colorG=1, colorB=1)
        self.border_scale_spn = QDoubleSpinBox()
        self.border_scale_spn.setRange(0.5, 2.0)
        self.border_scale_spn.setValue(1.0)
        self.border_scale_spn.setSingleStep(0.01)
        self.border_scale_spn.setDecimals(2)
        self.border_scale_spn.setMaximumWidth(80)

        grid_layout_2.addWidget(border_color_lbl, 0, 0, alignment=Qt.AlignLeft)
        grid_layout_2.addWidget(border_alpha_lbl, 1, 0, alignment=Qt.AlignLeft)
        grid_layout_2.addWidget(border_scale_lbl, 2, 0, alignment=Qt.AlignLeft)

        grid_layout_2.addWidget(self.border_color_btn, 0, 1)
        grid_layout_2.addWidget(self.border_alpha_btn, 1, 1)
        grid_layout_2.addWidget(self.border_scale_spn, 2, 1)

        counter_layout = QVBoxLayout()
        counter_layout.setAlignment(Qt.AlignLeft)
        counter_group = QGroupBox('Counter')
        counter_group.setLayout(counter_layout)
        self.main_layout.addWidget(counter_group)

        grid_layout_3 = QGridLayout()
        counter_layout.addLayout(grid_layout_3)

        align_lbl = QLabel('Alignment: ')
        padding_lbl = QLabel('Padding: ')

        self.align_combo = QComboBox()
        self.align_combo.addItem('None')
        self.align_combo.addItem('Top-Left')
        self.align_combo.addItem('Top-Center')
        self.align_combo.addItem('Top-Right')
        self.align_combo.addItem('Bottom-Left')
        self.align_combo.addItem('Bottom-Center')
        self.align_combo.addItem('Bottom-Right')
        self.padding_spn = QSpinBox()
        self.padding_spn.setRange(1, 6)
        self.padding_spn.setValue(1)
        self.padding_spn.setSingleStep(1)
        self.padding_spn.setMaximumWidth(80)

        grid_layout_3.addWidget(align_lbl, 0, 0, alignment=Qt.AlignLeft)
        grid_layout_3.addWidget(padding_lbl, 1, 0, alignment=Qt.AlignLeft)

        grid_layout_3.addWidget(self.align_combo, 0, 1)
        grid_layout_3.addWidget(self.padding_spn, 1, 1)

        create_mask_btn.clicked.connect(self._on_create_mask)
        delete_mask_btn.clicked.connect(self._on_delete_mask)
        self.enable_mask_cbx.stateChanged.connect(self.optionsChanged)
        self.top_left_line.textChanged.connect(self.optionsChanged)
        self.top_center_line.textChanged.connect(self.optionsChanged)
        self.top_right_line.textChanged.connect(self.optionsChanged)
        self.bottom_left_line.textChanged.connect(self.optionsChanged)
        self.bottom_center_line.textChanged.connect(self.optionsChanged)
        self.bottom_right_line.textChanged.connect(self.optionsChanged)
        self.color_btn.colorChanged.connect(self.optionsChanged)
        self.alpha_btn.colorChanged.connect(self.optionsChanged)
        self.scale_spn.valueChanged.connect(self.optionsChanged)
        self.top_cbx.stateChanged.connect(self.optionsChanged)
        self.bottom_cbx.stateChanged.connect(self.optionsChanged)
        self.border_color_btn.colorChanged.connect(self.optionsChanged)
        self.border_alpha_btn.colorChanged.connect(self.optionsChanged)
        self.border_scale_spn.valueChanged.connect(self.optionsChanged)
        self.align_combo.currentIndexChanged.connect(self.optionsChanged)
        self.padding_spn.valueChanged.connect(self.optionsChanged)
        self.font_line.textChanged.connect(self.optionsChanged)
        self.padding_text_spn.valueChanged.connect(self.optionsChanged)
        self.font_btn.clicked.connect(self._on_select_font)

        self.enable_mask_cbx.stateChanged.connect(self._on_update_enable_mask)
        self.top_left_line.textChanged.connect(self._on_update_top_left_text)
        self.top_center_line.textChanged.connect(self._on_update_top_center_text)
        self.top_right_line.textChanged.connect(self._on_update_top_right_text)
        self.bottom_left_line.textChanged.connect(self._on_update_bottom_left_text)
        self.bottom_center_line.textChanged.connect(self._on_update_bottom_center_text)
        self.bottom_right_line.textChanged.connect(self._on_update_bottom_right_text)
        self.padding_text_spn.valueChanged.connect(self._on_update_text_padding)
        self.font_line.textChanged.connect(self._on_update_font_name)
        self.color_btn.colorChanged.connect(self._on_update_color)
        self.alpha_btn.colorChanged.connect(self._on_update_transparency)
        self.scale_spn.valueChanged.connect(self._on_update_font_scale)
        self.top_cbx.stateChanged.connect(self._on_update_top_border)
        self.bottom_cbx.stateChanged.connect(self._on_update_bottom_border)
        self.border_color_btn.colorChanged.connect(self._on_update_border_color)
        self.border_alpha_btn.colorChanged.connect(self._on_update_border_alpha)
        self.border_scale_spn.valueChanged.connect(self._on_update_border_scale)
        self.align_combo.currentIndexChanged.connect(self._on_update_counter_position)
        self.padding_spn.valueChanged.connect(self._on_update_counter_padding)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        inputs = {
            'enable': self.enable_mask_cbx.isChecked(),
            'top_left': self.top_left_line.text(),
            'top_center': self.top_center_line.text(),
            'top_right': self.top_right_line.text(),
            'bottom_left': self.bottom_left_line.text(),
            'bottom_center': self.bottom_center_line.text(),
            'text_padding': self.padding_text_spn.value(),
            'bottom_right': self.bottom_right_line.text(),
            'text_padding': self.padding_text_spn.value(),
            'font': self.font_line.text(),
            'color': self.color_btn.color.toTuple(),
            'transparency': self.alpha_btn.color.toTuple(),
            'scale': self.scale_spn.value(),
            'top_border': self.top_cbx.isChecked(),
            'bottom_border': self.bottom_cbx.isChecked(),
            'border_color': self.border_color_btn.color.toTuple(),
            'border_transparency': self.border_alpha_btn.color.toTuple(),
            'border_scale': self.border_scale_spn.value(),
            'counter_align': self.align_combo.currentIndex(),
            'counter_padding': self.padding_spn.value()
        }

        return inputs

    def apply_inputs(self, attr_dict):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        enable = attr_dict.get('enable', True)
        top_left = attr_dict.get('top_left', '')
        top_center = attr_dict.get('top_center', '')
        top_right = attr_dict.get('top_right', '')
        bottom_left = attr_dict.get('bottom_left', '')
        bottom_center = attr_dict.get('bottom_center', '')
        bottom_right = attr_dict.get('bottom_right', '')
        font = attr_dict.get('font', 'Consolas')
        text_padding = attr_dict.get('text_padding', 10)
        color = attr_dict.get('color', (255, 255, 255, 255))
        transparency = attr_dict.get('transparency', (255, 255, 255, 255))
        scale = attr_dict.get('scale', 1.0)
        top_border = attr_dict.get('top_border', True)
        bottom_border = attr_dict.get('bottom_border', True)
        border_color = attr_dict.get('border_color', (0, 0, 0, 0))
        border_transparency = attr_dict.get('border_transparency', (255, 255, 255, 255))
        border_scale = attr_dict.get('border_scale', 1.0)
        counter_align = attr_dict.get('counter_align', 0)
        counter_padding = attr_dict.get('counter_padding', 1)

        if type(color) not in [list, tuple]:
            color = ast.literal_eval(color)
        if type(transparency) not in [list, tuple]:
            transparency = ast.literal_eval(transparency)
        if type(border_color) not in [list, tuple]:
            border_color = ast.literal_eval(border_color)
        if type(border_transparency) not in [list, tuple]:
            border_transparency = ast.literal_eval(border_transparency)

        self.enable_mask_cbx.setChecked(bool(enable))
        self.top_left_line.setText(top_left)
        self.top_center_line.setText(top_center)
        self.top_right_line.setText(top_right)
        self.bottom_left_line.setText(bottom_left)
        self.bottom_center_line.setText(bottom_center)
        self.bottom_right_line.setText(bottom_right)
        self.padding_text_spn.setValue(int(text_padding))
        self.font_line.setText(font)
        self.color_btn.color = QColor(*color)
        self.alpha_btn.color = QColor(*transparency)
        self.scale_spn.setValue(float(scale))
        self.top_cbx.setChecked(bool(top_border))
        self.bottom_cbx.setChecked(bool(bottom_border))
        self.border_color_btn.color = QColor(*border_color)
        self.border_alpha_btn.color = QColor(*border_transparency)
        self.border_scale_spn.setValue(float(border_scale))
        self.align_combo.setCurrentIndex(int(counter_align))
        self.padding_spn.setValue(int(counter_padding))

    def on_playblast_finished(self, options):
        """
        Overrides base ArtellaPlayblastPlugin on_playblast_finished function
        Internal callback function that is called when a Playblast is generated
        :param options: dict
        """

        MaskObject.delete_mask()

    def create_mask(self, options=None):
        """
        Creates new mask object
        :param options: dict
        :return: str
        """

        mask = MaskObject.get_mask()
        if not self.enable_mask_cbx.isChecked() and mask:
            MaskObject.delete_mask()
            return

        MaskObject.create_mask()
        mask = MaskObject.get_mask()
        tp.Dcc.set_boolean_attribute_value(node=mask, attribute_name='hiddenInOutliner', attribute_value=True)

        if options:
            tp.Dcc.set_string_attribute_value(node=mask, attribute_name='camera', attribute_value=options.get('camera', MaskObject.get_camera_name()))
        else:
            tp.Dcc.set_string_attribute_value(node=mask, attribute_name='camera', attribute_value=MaskObject.get_camera_name())

        color = self.color_btn.color
        alpha = self.alpha_btn.color
        border_color = self.border_color_btn.color
        border_alpha = self.border_alpha_btn.color

        tp.Dcc.set_attribute_value(node=mask, attribute_name='counterPosition', attribute_value=self.align_combo.currentIndex())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='counterPadding', attribute_value=self.padding_spn.value())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='topLeftText', attribute_value=self.top_left_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='topCenterText', attribute_value=self.top_center_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='topRightText', attribute_value=self.top_right_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomLeftText', attribute_value=self.bottom_left_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomCenterText', attribute_value=self.bottom_center_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomRightText', attribute_value=self.bottom_right_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='textPadding', attribute_value=self.padding_text_spn.value())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontName', attribute_value=self.font_line.text())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontColor', attribute_value=(color.red()/255.0, color.green()/255.0, color.blue()/255.0))
        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontAlpha', attribute_value=alpha.red()/255.0)
        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontScale', attribute_value=self.scale_spn.value())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='topBorder', attribute_value=self.top_cbx.isChecked())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomBorder', attribute_value=self.bottom_cbx.isChecked())
        tp.Dcc.set_attribute_value(node=mask, attribute_name='borderColor', attribute_value=(border_color.red()/255.0, border_color.green()/255.0, border_color.blue()/255.0))
        tp.Dcc.set_attribute_value(node=mask, attribute_name='borderAlpha', attribute_value= border_alpha.red()/255.0)
        tp.Dcc.set_attribute_value(node=mask, attribute_name='borderScale', attribute_value=self.border_scale_spn.value())

    def _on_create_mask(self):
        self.create_mask()
        # if not self.enable_mask_cbx.isChecked():
        #     self.enable_mask_cbx.blockSignals(True)
        #     self.enable_mask_cbx.setChecked(True)
        #     self.enable_mask_cbx.blockSignals(False)

    def _on_delete_mask(self):
        MaskObject.delete_mask()

    def _on_select_font(self):
        new_font = QFontDialog.getFont(self.font_line.text())
        if new_font:
            self.font_line.setText(new_font[0].family())

    def _on_update_enable_mask(self, flag):
        mask = MaskObject.get_mask()
        if mask and not flag:
            res = QMessageBox.question(self, 'Removing Camera Mask', 'Are you sure you want disable mask option. Current mask will be deleted')
            if res == QMessageBox.Yes:
                MaskObject.delete_mask()
            else:
                self.enable_mask_cbx.blockSignals(True)
                self.enable_mask_cbx.setChecked(True)
                self.enable_mask_cbx.blockSignals(False)

    def _on_update_counter_position(self, index):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='counterPosition', attribute_value=index)

    def _on_update_counter_padding(self, value):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='counterPadding', attribute_value=value)

    def _on_update_top_left_text(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='topLeftText', attribute_value=new_text)

    def _on_update_top_center_text(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='topCenterText', attribute_value=new_text)

    def _on_update_top_right_text(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='topRightText', attribute_value=new_text)

    def _on_update_bottom_left_text(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomLeftText', attribute_value=new_text)

    def _on_update_bottom_center_text(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomCenterText', attribute_value=new_text)

    def _on_update_bottom_right_text(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomRightText', attribute_value=new_text)

    def _on_update_text_padding(self, value):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='textPadding', attribute_value=value)

    def _on_update_font_name(self, new_text):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontName', attribute_value=new_text)

    def _on_update_color(self):
        mask = MaskObject.get_mask()
        if not mask:
            return

        new_color = self.color_btn.color
        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontColor', attribute_value=(new_color.red(), new_color.green(), new_color.blue()))

    def _on_update_transparency(self):
        mask = MaskObject.get_mask()
        if not mask:
            return

        new_alpha = self.alpha.color
        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontAlpha', attribute_value=new_alpha.red()/255.0)

    def _on_update_font_scale(self, value):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='fontScale', attribute_value=value)

    def _on_update_top_border(self, flag):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='topBorder', attribute_value=flag)

    def _on_update_bottom_border(self, flag):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='bottomBorder', attribute_value=flag)

    def _on_update_border_color(self):
        mask = MaskObject.get_mask()
        if not mask:
            return

        border_color = self.border_color_btn.color
        tp.Dcc.set_attribute_value(node=mask, attribute_name='borderColor', attribute_value=(border_color.red(), border_color.green(), border_color.blue()))

    def _on_update_border_alpha(self):
        mask = MaskObject.get_mask()
        if not mask:
            return

        border_alpha = self.border_alpha_btn.color

        tp.Dcc.set_attribute_value(node=mask, attribute_name='borderAlpha', attribute_value=max(min(border_alpha.red()/255.0, 1.0), 0.0))

    def _on_update_border_scale(self, value):
        mask = MaskObject.get_mask()
        if not mask:
            return

        tp.Dcc.set_attribute_value(node=mask, attribute_name='borderScale', attribute_value=value)


class MaskLocator(maya.OpenMayaUIV2.MPxLocatorNode, object):
    _NAME_ = 'CameraMask'
    _ID_ = maya.OpenMayaV2.MTypeId(0x1111B159)
    _DRAW_DB_CLASSIFICATION_ = 'drawdb/geometry/cameraMask'
    _DRAW_REGISTRANT_ID_ = 'MaskNode'
    _TEXT_ATTRS_ = [
        MaskTextAlignment.TopLeft,
        MaskTextAlignment.TopCenter,
        MaskTextAlignment.TopRight,
        MaskTextAlignment.BottomLeft,
        MaskTextAlignment.BottomCenter,
        MaskTextAlignment.BottomRight
    ]

    def __init__(self):
        super(MaskLocator, self).__init__()

    @classmethod
    def creator(cls):
        return MaskLocator()

    @classmethod
    def initialize(cls):
        t_attr = maya.OpenMayaV2.MFnTypedAttribute()
        str_data = maya.OpenMayaV2.MFnStringData()
        n_attr = maya.OpenMayaV2.MFnNumericAttribute()

        test_attr = maya.OpenMayaV2.MFnTypedAttribute()
        str_test = maya.OpenMayaV2.MFnStringData()
        obj = str_test.create('')
        camera_name = t_attr.create('camera', 'cam', maya.OpenMayaV2.MFnData.kString, obj)
        t_attr.writable = True
        t_attr.storable = True
        t_attr.keyable = False
        MaskLocator.addAttribute(camera_name)

        counter_position = n_attr.create('counterPosition', 'cp', maya.OpenMayaV2.MFnNumericData.kShort, 6)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(0)
        n_attr.setMax(6)
        MaskLocator.addAttribute(counter_position)

        counter_padding = n_attr.create('counterPadding', 'cpd', maya.OpenMayaV2.MFnNumericData.kShort, 4)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(1)
        n_attr.setMax(6)
        MaskLocator.addAttribute(counter_padding)

        for i in range(len(cls._TEXT_ATTRS_)):
            obj = str_data.create('Position {}'.format(str(i / 2 + 1).zfill(2)))
            position = t_attr.create(cls._TEXT_ATTRS_[i][0], cls._TEXT_ATTRS_[i][1], maya.OpenMayaV2.MFnData.kString, obj)
            t_attr.writable = True
            t_attr.storable = True
            t_attr.keyable = True
            MaskLocator.addAttribute(position)

        text_padding = n_attr.create('textPadding', 'tp', maya.OpenMayaV2.MFnNumericData.kShort, 10)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(0)
        n_attr.setMax(50)
        MaskLocator.addAttribute(text_padding)

        font_name = t_attr.create('fontName', 'ft', maya.OpenMayaV2.MFnData.kString, str_data.create('Consolas'))
        t_attr.writable = True
        t_attr.storable = True
        t_attr.keyable = True
        MaskLocator.addAttribute(font_name)

        font_color = n_attr.createColor("fontColor", "fc")
        n_attr.default = (1.0, 1.0, 1.0)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        MaskLocator.addAttribute(font_color)

        font_alpha = n_attr.create("fontAlpha", "fa", maya.OpenMayaV2.MFnNumericData.kFloat, 1.0)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(0.0)
        n_attr.setMax(1.0)
        MaskLocator.addAttribute(font_alpha)

        font_scale = n_attr.create("fontScale", "fs", maya.OpenMayaV2.MFnNumericData.kFloat, 1.0)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(0.1)
        n_attr.setMax(2.0)
        MaskLocator.addAttribute(font_scale)

        top_border = n_attr.create("topBorder", "tbd", maya.OpenMayaV2.MFnNumericData.kBoolean, True)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        MaskLocator.addAttribute(top_border)

        bottom_border = n_attr.create("bottomBorder", "bbd", maya.OpenMayaV2.MFnNumericData.kBoolean, True)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        MaskLocator.addAttribute(bottom_border)

        border_color = n_attr.createColor("borderColor", "bc")
        n_attr.default = (0.0, 0.0, 0.0)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        MaskLocator.addAttribute(border_color)

        border_alpha = n_attr.create("borderAlpha", "ba", maya.OpenMayaV2.MFnNumericData.kFloat, 1.0)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(0.0)
        n_attr.setMax(1.0)
        MaskLocator.addAttribute(border_alpha)

        border_scale = n_attr.create("borderScale", "bs", maya.OpenMayaV2.MFnNumericData.kFloat, 1.0)
        n_attr.writable = True
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.setMin(0.5)
        n_attr.setMax(2.0)
        MaskLocator.addAttribute(border_scale)


class MaskData(maya.OpenMayaV2.MUserData, object):
    def __init__(self):
        super(MaskData, self).__init__(False)


class MaskDrawOverride(maya.OpenMayaRenderV2.MPxDrawOverride, object):
    _NAME_ = 'SolsticeMask_draw_override'

    def __init__(self, obj):
        super(MaskDrawOverride, self).__init__(obj, MaskDrawOverride.draw)

    @staticmethod
    def creator(obj):
        return MaskDrawOverride(obj)

    @staticmethod
    def draw(context, data):
        return

    def supportedDrawAPIs(self):
        return maya.OpenMayaRenderV2.MRenderer.kAllDevices

    def isBounded(self, obj_path, camera_path):
        return False

    def boundingBox(self, obj_path, camera_path):
        return maya.OpenMayaV2.MBoundingBox()

    def hasUIDrawables(self):
        return True

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        data = old_data
        if not isinstance(data, MaskData):
            data = MaskData()

        dag_node_fn = maya.OpenMayaV2.MFnDagNode(obj_path)
        data.camera_name = dag_node_fn.findPlug('camera', False).asString()
        data.text_fields = list()
        for i in range(len(MaskLocator._TEXT_ATTRS_)):
            data.text_fields.append(dag_node_fn.findPlug(MaskLocator._TEXT_ATTRS_[i][0], False).asString())
        counter_padding = dag_node_fn.findPlug('counterPadding', False).asInt()
        if counter_padding < 1:
            counter_padding = 1
        elif counter_padding > 6:
            counter_padding = 6
        current_time = int(maya.cmds.currentTime(query=True))
        counter_position = dag_node_fn.findPlug('counterPosition', False).asInt()
        if counter_position > 0 and counter_position <= len(MaskLocator._TEXT_ATTRS_):
            data.text_fields[counter_position-1] = '{}'.format(str(current_time).zfill(counter_padding))
        data.text_padding = dag_node_fn.findPlug('textPadding', False).asInt()
        data.font_name = dag_node_fn.findPlug('fontName', False).asString()
        r = dag_node_fn.findPlug('fontColorR', False).asFloat()
        g = dag_node_fn.findPlug('fontColorG', False).asFloat()
        b = dag_node_fn.findPlug('fontColorB', False).asFloat()
        a = dag_node_fn.findPlug('fontAlpha', False).asFloat()
        data.font_color = maya.OpenMayaV2.MColor((r, g, b, a))
        data.font_scale = dag_node_fn.findPlug('fontScale', False).asFloat()
        br = dag_node_fn.findPlug('borderColorR', False).asFloat()
        bg = dag_node_fn.findPlug('borderColorG', False).asFloat()
        bb = dag_node_fn.findPlug('borderColorB', False).asFloat()
        ba = dag_node_fn.findPlug('borderAlpha', False).asFloat()
        data.border_color = maya.OpenMayaV2.MColor((br, bg, bb , ba))
        data.border_scale = dag_node_fn.findPlug('borderScale', False).asFloat()
        data.top_border = dag_node_fn.findPlug('topBorder', False).asBool()
        data.bottom_border = dag_node_fn.findPlug('bottomBorder', False).asBool()

        return data

    def addUIDrawables(self, obj_path, draw_manager, frame_context, data):
        if not isinstance(data, MaskData):
            return

        icon_names = draw_manager.getIconNames()

        draw_manager.icon(maya.OpenMayaV2.MPoint(50, 50), icon_names[5], 1.0)

        camera_path = frame_context.getCurrentCameraPath()
        camera = maya.OpenMayaV2.MFnCamera(camera_path)
        if data.camera_name and self.camera_exists(data.camera_name) and not self.is_camera_match(camera_path, data.camera_name):
            return

        camera_aspect_ratio = camera.aspectRatio()
        device_aspect_ratio = maya.cmds.getAttr('defaultResolution.deviceAspectRatio')
        vp_x, vp_y, vp_width, vp_height = frame_context.getViewportDimensions()
        vp_half_width = vp_width * 0.5
        vp_half_height = vp_height * 0.5
        vp_aspect_ratio = vp_width / float(vp_height)

        scale = 1.0

        if camera.filmFit == maya.OpenMayaV2.MFnCamera.kHorizontalFilmFit:
            mask_width = vp_width / camera.overscan
            mask_height = mask_width / device_aspect_ratio
        elif camera.filmFit == maya.OpenMayaV2.MFnCamera.kVerticalFilmFit:
            mask_height = vp_height / camera.overscan
            mask_width = mask_height * device_aspect_ratio
        elif camera.filmFit == maya.OpenMayaV2.MFnCamera.kFillFilmFit:
            if vp_aspect_ratio < camera_aspect_ratio:
                if camera_aspect_ratio < device_aspect_ratio:
                    scale = camera_aspect_ratio / vp_aspect_ratio
                else:
                    scale = device_aspect_ratio / vp_aspect_ratio
            elif camera_aspect_ratio > device_aspect_ratio:
                scale = device_aspect_ratio / camera_aspect_ratio
            mask_width = vp_width / camera.overscan * scale
            mask_height = mask_width / device_aspect_ratio
        elif camera.filmFit == maya.OpenMayaV2.MFnCamera.kOverscanFilmFit:
            if vp_aspect_ratio < camera_aspect_ratio:
                if camera_aspect_ratio < device_aspect_ratio:
                    scale = camera_aspect_ratio / vp_aspect_ratio
                else:
                    scale = device_aspect_ratio / vp_aspect_ratio
            elif camera_aspect_ratio > device_aspect_ratio:
                scale = device_aspect_ratio / camera_aspect_ratio

            mask_height = vp_height / camera.overscan / scale
            mask_width = mask_height * device_aspect_ratio
        else:
            maya.OpenMayaV2.MGlobal.displayError('ShotMask: Unknown Film Fit value')
            return

        mask_half_width = mask_width * 0.5
        mask_x = vp_half_width - mask_half_width
        mask_half_height = 0.5 * mask_height
        mask_bottom_y = vp_half_height - mask_half_height
        mask_top_y = vp_half_height + mask_half_height
        border_height = int(0.05 * mask_height * data.border_scale)
        background_size = (int(mask_width), border_height)

        draw_manager.beginDrawable()
        draw_manager.setFontName(data.font_name)
        draw_manager.setFontSize(int((border_height - border_height * 0.15) * data.font_scale))
        draw_manager.setColor(data.font_color)

        if data.top_border:
            self.draw_border(draw_manager, maya.OpenMayaV2.MPoint(mask_x, mask_top_y - border_height), background_size, data.border_color)
        if data.bottom_border:
            self.draw_border(draw_manager, maya.OpenMayaV2.MPoint(mask_x, mask_bottom_y), background_size, data.border_color)

        self.draw_text(draw_manager, maya.OpenMayaV2.MPoint(mask_x + data.text_padding, mask_top_y - border_height), data.text_fields[0], maya.OpenMayaRenderV2.MUIDrawManager.kLeft, background_size)
        self.draw_text(draw_manager, maya.OpenMayaV2.MPoint(vp_half_width, mask_top_y - border_height), data.text_fields[1], maya.OpenMayaRenderV2.MUIDrawManager.kCenter, background_size)
        self.draw_text(draw_manager, maya.OpenMayaV2.MPoint(mask_x + mask_width - data.text_padding, mask_top_y - border_height), data.text_fields[2], maya.OpenMayaRenderV2.MUIDrawManager.kRight, background_size)
        self.draw_text(draw_manager, maya.OpenMayaV2.MPoint(mask_x + data.text_padding, mask_bottom_y), data.text_fields[3], maya.OpenMayaRenderV2.MUIDrawManager.kLeft, background_size)
        self.draw_text(draw_manager, maya.OpenMayaV2.MPoint(vp_half_width, mask_bottom_y), data.text_fields[4], maya.OpenMayaRenderV2.MUIDrawManager.kCenter, background_size)
        self.draw_text(draw_manager, maya.OpenMayaV2.MPoint(mask_x + mask_width - data.text_padding, mask_bottom_y), data.text_fields[5], maya.OpenMayaRenderV2.MUIDrawManager.kRight, background_size)

        draw_manager.endDrawable()

    def draw_border(self, draw_manager, position, background_size, color):
        draw_manager.text2d(position, ' ', alignment=maya.OpenMayaRenderV2.MUIDrawManager.kLeft, backgroundSize=background_size, backgroundColor=color)

    def draw_text(self, draw_manager, position, text, alignment, background_size):
        if len(text) > 0:
            draw_manager.text2d(position, text, alignment=alignment, backgroundSize=background_size, backgroundColor=maya.OpenMayaV2.MColor((0.0, 0.0, 0.0, 0.0)))

    def camera_exists(self, name):
        return name in maya.cmds.listCameras()

    def is_camera_match(self, camera_path, name):
        path_name = camera_path.fullPathName()
        split_path_name = path_name.split('|')
        if len(split_path_name) >= 1:
            if split_path_name[-1] == name:
                return True
        if len(split_path_name) >= 2:
            if split_path_name[-2] == name:
                return True

        return False


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def initializePlugin(obj):
    plugin_fn = maya.OpenMayaV2.MFnPlugin(obj, 'Solstice Short Film', '1.0', 'Any')
    try:
        plugin_fn.registerNode(
            MaskLocator._NAME_,
            MaskLocator._ID_,
            MaskLocator.creator,
            MaskLocator.initialize,
            maya.OpenMayaV2.MPxNode.kLocatorNode,
            MaskLocator._DRAW_DB_CLASSIFICATION_
        )
    except Exception:
        maya.OpenMayaV2.MGlobal.displayError('Failed to register node: {}'.format(MaskLocator._NAME_))

    try:
        maya.OpenMayaRenderV2.MDrawRegistry.registerDrawOverrideCreator(
            MaskLocator._DRAW_DB_CLASSIFICATION_,
            MaskLocator._DRAW_REGISTRANT_ID_,
            MaskDrawOverride.creator
        )
    except Exception:
        maya.OpenMayaV2.MGlobal.displayError('Failed to register draw override: {}'.format(MaskDrawOverride._NAME_))


def uninitializePlugin(obj):
    plugin_fn = maya.OpenMayaV2.MFnPlugin(obj)
    try:
        maya.OpenMayaRenderV2.MDrawRegistry.deregisterDrawOverrideCreator(
            MaskLocator._DRAW_DB_CLASSIFICATION_,
            MaskLocator._DRAW_REGISTRANT_ID_
        )
    except Exception:
        maya.OpenMayaV2.MGlobal.displayError('Failed to deregister draw override: {}'.format(MaskDrawOverride._NAME_))

    try:
        plugin_fn.deregisterNode(MaskLocator._ID_)
    except Exception:
        maya.OpenMayaV2.MGlobal.displayError('Failed to unregister node: {}'.format(MaskLocator._NAME_))
