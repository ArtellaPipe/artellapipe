#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool that allow to define the nomenclature of the pipeline files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.gui import window

from tpNameIt.core import nameit

import lucidity


class ArtellaNamingData(nameit.NamingData, object):

    _templates_key = 'templates'
    _template_tokens_key = 'template_tokens'

    @classmethod
    def get_template(cls, template_index, data_file):
        """
        Returns a template from the naming data
        :param template_index: int, index of the template to return
        :param data_file: str, path to data file
        :return: Template or None
        """

        data = cls.load_data(data_file)
        if data is not None and template_index > -1:
            try:
                template = data[cls._nameit_key][cls._templates_key][template_index]
                return Template(template['name'], template['pattern'])
            except Exception as e:
                pass

            return None

    @classmethod
    def get_templates(cls, data_file):
        """
        Returns a list of all the templates on the Naming Manager data
        :param data_file: str, path file where data is stored
        :return: list(tpNamingManager.tpTemplate): List of templates
        """

        data = cls.load_data(data_file)
        if data is not None:
            try:
                templates_list = list()
                templates = data[cls._nameit_key][cls._templates_key]
                for template in templates:
                    templates_list.append(Template(template['name'], template['pattern']))
                return templates_list
            except Exception as e:
                artellapipe.logger.warning('Impossible to load templates fron naming data file: {}'.format(data_file))
                artellapipe.logger.error('{} | {}'.format(e, traceback.format_exc()))

        return None

    @classmethod
    def get_template_tokens(cls, data_file):
        """
        Returns a dict with the information of the template tokens
        :param data_file: str
        :return: dict
        """

        data = cls.load_data(data_file)
        if not data:
            return None

        return data[cls._nameit_key][cls._template_tokens_key]

    @classmethod
    def set_template_name(cls, template_index, template_name, data_file):
        """
        Sets the name of the template
        :param template_index: int, index list of the template
        :param template_name: str, new name for the template
        :param data_file: str, path to data file
        :return:
        """

        data = cls.load_data(data_file)
        if data is not None and template_index > -1 and isinstance(template_name, unicode):
            try:
                data[cls._nameit_key][cls._templates_key][template_index]['name'] = template_name
                return cls.write_data(data, data_file=data_file)
            except Exception:
                pass

        return False

    @classmethod
    def add_template(cls, template, data_file):
        """
        Adds a new template into the naming data
        :param template: template to add
        :param data_file: str
        :return:
        """

        data = cls.load_data(data_file)
        if data is not None and template is not None:
            data[cls._nameit_key][cls._templates_key].append(template.data())
            return cls.write_data(data, data_file=data_file)
        return False

    @classmethod
    def remove_template(cls, template_index, data_file):
        """
        Removes a template from the naming data
        :param template_index: int, index of the rule to delete
        :param data_file: str, path to data file
        :return: True if the rule is deleted successfully or False otherwise
        """

        data = cls.load_data(data_file)
        if data is not None and template_index > -1:
            try:
                data[cls._nameit_key][cls._templates_key].pop(template_index)
                return cls.write_data(data, data_file=data_file)
            except Exception as e:
                pass

        return False


class Template(object):
    """
    Class that defines a template in the naming manager
    Is stores naming patterns for files
    """

    def __init__(self, name='New_Template', pattern=''):
        self.name = name
        self.pattern = pattern

    def data(self):
        return self.__dict__

    def parse(self, path_to_parse):
        """
        Parses given path
        :param path_to_parse: str
        :return: list(str)
        """

        try:
            temp = lucidity.Template(self.name, self.pattern)
            return temp.parse(path_to_parse)
        except Exception:
            artellapipe.logger.warning('Given Path: {} does not match template pattern: {} | {}!'.format(path_to_parse, self.name, self.pattern))
            return None

    def format(self, template_data):
        """
        Returns proper path with the given dict data
        :param template_data: dict(str, str)
        :return: str
        """

        temp = lucidity.Template(self.name, self.pattern)
        return temp.format(template_data)


class NameWidget(nameit.NameIt, object):

    DEFAULT_DATA = {
        'nameit':
            {
                'rules':
                    [],
                'tokens':
                    [],
                'templates':
                    []
            }
    }
    NAMING_DATA = ArtellaNamingData

    def __init__(self, project, parent=None):
        self._project = project
        NameWidget.DATA_FILE = self._project.naming_file
        super(NameWidget, self).__init__(parent=parent)

    def ui(self):

        # We must create the list before calling super ui, otherwise data loading will fail
        # Templates Tab
        templates_main_layout = QVBoxLayout()
        templates_main_layout.setContentsMargins(5, 5, 5, 5)
        templates_main_layout.setSpacing(0)
        self.templates_list = QListWidget()
        templates_main_layout.addWidget(self.templates_list)
        left_panel_buttons_layout_templates = QHBoxLayout()
        left_panel_buttons_layout_templates.setContentsMargins(5, 5, 5, 0)
        templates_main_layout.addLayout(left_panel_buttons_layout_templates)
        self.add_template_btn = QPushButton('+')
        self.remove_template_btn = QPushButton('-')
        left_panel_buttons_layout_templates.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))
        left_panel_buttons_layout_templates.addWidget(self.add_template_btn)
        left_panel_buttons_layout_templates.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))
        left_panel_buttons_layout_templates.addWidget(self.remove_template_btn)
        left_panel_buttons_layout_templates.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Templates Panel
        self.templates_widget = QWidget()
        templates_layout = QVBoxLayout()
        self.templates_widget.setLayout(templates_layout)
        pattern_layout = QHBoxLayout()
        pattern_layout.setContentsMargins(5, 5, 5, 5)
        pattern_layout.setSpacing(5)
        pattern_lbl = QLabel('Pattern: ')
        self.pattern_line = QLineEdit()
        pattern_layout.addWidget(pattern_lbl)
        pattern_layout.addWidget(self.pattern_line)
        templates_layout.addLayout(pattern_layout)
        templates_layout.addLayout(splitters.SplitterLayout())
        self.template_tokens_layout = QGridLayout()
        self.template_tokens_layout.setAlignment(Qt.AlignTop)
        template_tokens_frame = QFrame()
        template_tokens_frame.setFrameShape(QFrame.StyledPanel)
        template_tokens_frame.setFrameShadow(QFrame.Sunken)
        template_tokens_frame.setLayout(self.template_tokens_layout)
        templates_layout.addWidget(template_tokens_frame)

        self.templates_widget.hide()

        super(NameWidget, self).ui()

        templates_tab = QWidget()
        self.tabs.addTab(templates_tab, 'Templates')
        templates_tab.setLayout(templates_main_layout)
        self.group_layout.addWidget(self.templates_widget)
        
    def setup_signals(self):
        super(NameWidget, self).setup_signals()
        
        self.add_template_btn.clicked.connect(self.on_add_template)
        self.remove_template_btn.clicked.connect(self.on_remove_template)
        self.templates_list.currentItemChanged.connect(self.on_change_template)
        self.templates_list.itemChanged.connect(self.on_edit_template_name)
        self.pattern_line.textChanged.connect(self.on_edit_pattern)

    def _init_data(self):
        """
        Overrides base NameIt _init_data function
        """

        super(NameWidget, self)._init_data()

        self._load_templates()

    def _load_templates(self):
        """
        Internal function that loads templates from DB
        """

        try:
            templates = self.NAMING_DATA.get_templates(data_file=self.DATA_FILE)
            if templates is not None:
                for template in templates:
                    self.on_add_template(template)
            return True
        except Exception as e:
            artellapipe.logger.error('Error while loading templates from: {} | {} | {}'.format(self.DATA_FILE, e, traceback.format_exc()))

        return False

    def _clear_template_tokens(self):
        """
        Clears all template tokens from layout
        """

        for i in range(self.template_tokens_layout.count(), -1, -1):
            item = self.template_tokens_layout.itemAt(i)
            if item is None:
                continue
            item.widget().setParent(None)
            self.template_tokens_layout.removeItem(item)

    def _add_template_token(self, template_token_name, template_token_data=None):
        """
        Adds template token to layout
        :param template_token_name: str
        :param template_token_data: dict
        """

        row = 0
        while self.template_tokens_layout.itemAtPosition(row, 0) is not None:
            row += 1

        self.template_tokens_layout.addWidget(QLabel(template_token_name), row, 0)
        self.template_tokens_layout.addWidget(QLabel(template_token_data.get('description', '') if template_token_data else '< NOT FOUND >'), row, 1)

    def _update_template_tokens(self, template):
        """
        Internal function that updates template tokens currently loaded
        :param template: Template
        """

        if not template:
            return

        temp = lucidity.Template(template.name, template.pattern)
        temp.duplicate_placeholder_mode = temp.STRICT
        temp_tokens = temp.keys()

        template_tokens_dict = self.NAMING_DATA.get_template_tokens(data_file=self.DATA_FILE)
        template_tokens_names = template_tokens_dict.keys()

        self._clear_template_tokens()

        for token in temp_tokens:
            if token in template_tokens_names:
                self._add_template_token(token, template_tokens_dict[token])
            else:
                self._add_template_token(token)

    def on_change_tab(self, tab_index):
        """
        Overrides base NameIt on_change tab function
        """

        if tab_index == 2:
            self.rules_widget.hide()
            self.tokens_widget.hide()
            self.templates_widget.show()
        else:
            self.templates_widget.hide()
            super(NameWidget, self).on_change_tab(tab_index)

    def on_add_template(self, *args):
        """
        Creates a new template and add it to the Naming Manager
        :return:
        """

        load_template = True
        if len(args) == 0:
            load_template = False

        template = None
        if not load_template:
            template = Template()
        elif load_template and len(args) == 1 and isinstance(args[0], Template):
            template = args[0]

        if template is not None:
            item = QListWidgetItem(template.name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.templates_list.addItem(item)

            if len(args) == 0:
                self.NAMING_DATA.add_template(template, data_file=self.DATA_FILE)

            if not load_template:
                self.templates_list.setCurrentItem(item)
    
    def on_remove_template(self):
        """
        Removes the selected template from the list of templates
        :return: bool, True if the element deletion is successful or False otherwise
        """

        current_template = self.templates_list.currentItem()
        if current_template is not None:
            template_index = self.templates_list.currentRow()
            name = self.templates_list.currentItem().text()
            if template_index > -1 and name is not None:
                template = self.NAMING_DATA.get_template(template_index, data_file=self.DATA_FILE)
                if template is not None:
                    if template.name == name:
                        self.NAMING_DATA.remove_template(template_index, data_file=self.DATA_FILE)
                        self.templates_list.takeItem(self.templates_list.row(self.templates_list.currentItem()))

    def on_change_template(self, template_item):
        """
        Changes the selected template
        :param template_item: new QlistWidgetItem selected
        """

        if not template_item or not template_item.listWidget().count() > 0:
            return

        template = self.NAMING_DATA.get_template(template_item.listWidget().currentRow(), data_file=self.DATA_FILE)
        if not template:
            return

        self.pattern_line.setText(template.pattern)

        self._update_template_tokens(template)

    def on_edit_template_name(self, template_item):
        """
        Changes name of the template
        :param template_item: Renamed QListWidgetItem
        """

        template_index = template_item.listWidget().currentRow()
        self.NAMING_DATA.set_template_name(template_index, template_item.text(), data_file=self.DATA_FILE)
        templates = self.NAMING_DATA.get_templates(data_file=self.DATA_FILE)
        templates[template_index].name = template_item.text()

    def on_edit_pattern(self, pattern):
        print(pattern)


class NameManager(window.ArtellaWindow, object):

    VERSION = '0.0.1'
    LOGO_NAME = 'namemanager_logo'

    def __init__(self, project):
        super(NameManager, self).__init__(
            project=project,
            name='NameManagerWindow',
            title='Name Manager',
            size=(600, 900)
        )

    def ui(self):
        super(NameManager, self).ui()

        self._name_widget = NameWidget(project=self._project)
        self.main_layout.addWidget(self._name_widget)

    @property
    def nameit(self):
        return self._name_widget

    @staticmethod
    def parse_template(template_name, path_to_parse):
        """
        Parses given path in the given template
        :param template_name: str
        :param path_to_parse: str
        :return: list(str)
        """

        templates = NameWidget.NAMING_DATA.get_templates(data_file=NameWidget.DATA_FILE)
        if not templates:
            return False

        for template in templates:
            if template.name == template_name:
                return template.parse(path_to_parse)

        return None

    @classmethod
    def check_template_validity(cls, template_name, path_to_check):
        """
        Returns whether given path matches given pattern or not
        :param template_name: str
        :param path_to_check: str
        :return: bool
        """

        parse = cls.parse_template(template_name, path_to_check)
        if parse is not None and type(parse) is dict:
            return True

        return False

    @staticmethod
    def format_template(template_name, template_tokens):
        """
        Returns template path filled with tempalte tokens data
        :param template_name: str
        :param template_tokens: dict
        :return: str
        """

        templates = NameWidget.NAMING_DATA.get_templates(data_file=NameWidget.DATA_FILE)
        if not templates:
            return False

        for template in templates:
            if template.name == template_name:
                return template.format(template_tokens)

        return None


def run(project):
    win = NameManager(project=project)
    win.show()

    return win
