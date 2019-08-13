#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Solstice Alembic Groups
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDccLib as tp

from tpQtLib.core import base
from tpQtLib.widgets import splitters

import artellapipe
from artellapipe.tools.alembicmanager.core import defines


class AlembicGroup(base.BaseWidget, object):
    def __init__(self, parent=None):
        super(AlembicGroup, self).__init__(parent=parent)

    def ui(self):
        super(AlembicGroup, self).ui()

        add_icon = artellapipe.resource.icon('add')
        delete_icon = artellapipe.resource.icon('delete')

        group_layout = QGridLayout()
        group_layout.setContentsMargins(2, 2, 2, 2)
        group_layout.setSpacing(2)
        self.main_layout.addLayout(group_layout)

        group_name_lbl = QLabel('Group Name: ')
        group_name_lbl.setStyleSheet('background-color: transparent;')
        self.name_line = QLineEdit()
        group_layout.addWidget(group_name_lbl, 0, 0, 1, 1, Qt.AlignRight)
        group_layout.addWidget(self.name_line, 0, 1)

        self.main_layout.addLayout(splitters.SplitterLayout())

        buttons_layout = QVBoxLayout()
        buttons_layout.setContentsMargins(25, 5, 25, 5)
        self.main_layout.addLayout(buttons_layout)

        self._create_btn = QPushButton('Create')
        self._create_btn.setIcon(add_icon)
        buttons_layout.addWidget(self._create_btn)
        buttons_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Fixed, QSizePolicy.Expanding))
        self._clean_alembic_groups_btn = QPushButton('Clean Alembic Groups')
        self._clean_alembic_groups_btn.setIcon(delete_icon)
        self.main_layout.addWidget(self._clean_alembic_groups_btn)

    def setup_signals(self):
        self._create_btn.clicked.connect(partial(lambda: self.create_alembic_group(self.name_line.text())))
        self._clean_alembic_groups_btn.clicked.connect(self.clean_alembic_groups)

    @staticmethod
    def get_alembic_group_name_from_node_name(node_name):
        """
        Returns an alembic group name from the give node name
        :param node_name: str, long name of a Maya node
        :return: str
        """

        if node_name:
            split_name = node_name.split('|')
            if not split_name or len(split_name) == 1:
                return node_name
            split_name = split_name[1]
            rsplit_name = split_name.rsplit(':', 1)
            if not rsplit_name or len(rsplit_name) == 1:
                return node_name
            rsplit_name = rsplit_name[-1]

            return rsplit_name

        return None

    @staticmethod
    def create_alembic_group(name=None, filter_type='transform'):
        """
        Creates a new alembic group (set)
        :param name: str, name of the alembic group
        :param filter_type:
        :return: str, new alembic group created
        """

        if not tp.is_maya():
            artellapipe.solstice.logger.warning(
                'DCC {} does not supports the creation of Alembic groups!'.format(tp.Dcc.get_name()))
            return None

        import maya.cmds as cmds

        sel = tp.Dcc.selected_nodes(full_path=True)
        if not sel:
            tp.Dcc.confirm_dialog(
                title='Impossible to create Alembic Group',
                message='No nodes selected, please select nodes firt and try again!')
            return None

        if not name:
            name = AlembicGroup.get_alembic_group_name_from_node_name(sel[0])

        if not name.endswith(defines.ALEMBIC_GROUP_SUFFIX):
            name += defines.ALEMBIC_GROUP_SUFFIX

        if tp.Dcc.object_exists(name):
            res = tp.Dcc.confirm_dialog(
                title='Alembic Group already exists!',
                message='Do you want to overwrite existing Alembic Group?',
                button=['Yes', 'No'],
                default_button='Yes',
                cancel_button='No',
                dismiss_string='No'
            )
            if res and res == 'Yes':
                tp.Dcc.delete_object(name)

        artellapipe.solstice.logger.debug('Creating Alembic Group with name: {}'.format(name))

        full_sel = tp.Dcc.list_relatives(node=sel, all_hierarchy=True, full_path=True) or []
        main_sel = list()
        for n in full_sel:
            p = tp.Dcc.node_parent(node=n, full_path=True)
            p = p[0] if p else None
            if p and p in full_sel:
                continue
            main_sel.append(n)

        final_sel = None
        if filter_type:
            final_sel = filter(lambda x: tp.Dcc.check_object_type(node=x, node_type=filter_type), main_sel)
        if final_sel is None:
            tp.Dcc.confirm_dialog(
                title='Impossible to create Alembic Group',
                message='No objects found with filter type {}!'.format(filter_type)
            )

        return cmds.sets(sel, n=name)

    # @solstice_maya_utils.maya_undo
    @staticmethod
    def clean_alembic_groups():
        """
        Removes all alembic groups in current scene
        """

        if not tp.is_maya():
            artellapipe.solstice.logger.warning(
                'DCC {} does not supports the creation of Alembic groups!'.format(tp.Dcc.get_name()))
            return None

        import maya.cmds as cmds

        all_sets = cmds.listSets(allSets=True)
        abc_sets = [s for s in all_sets if s.endswith(defines.ALEMBIC_GROUP_SUFFIX)]

        res = tp.Dcc.confirm_dialog(
            title='Removing Alembic Groups!',
            message='Do you want to remove following Alembic Groups?\n' + '\n'.join(abc_sets),
            button=['Yes', 'No'],
            default_button='Yes',
            cancel_button='No',
            dismiss_string='No'
        )
        if res and res == 'Yes':
            cmds.delete(abc_sets)
