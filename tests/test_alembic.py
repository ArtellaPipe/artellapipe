#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tests for artellapipe-utils
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.abspath(__file__))
if tests_path not in sys.path:
    sys.path.append(tests_path)

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch

import mock_import
mock_import.prepare_modules()

os.environ['ARTELLAPIPE_UTILS_LOG_LEVEL'] = 'DEBUG'
from artellapipe.utils import alembic

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests_data')


@patch('tpMayaLib.cmds.AbcExport')
def test_export_alembic(mock_abc_export):
    out_abc = os.path.join(data_path, 'abc_out.abc')
    alembic.export_alembic(out_abc)
    assert mock_abc_export.called


@patch('tpMayaLib.cmds.AbcImport')
def test_import_alembic(mock_abc_import):
    project = MagicMock()
    project.name = 'Default'
    in_abc = os.path.join(data_path, 'abc_in.abc')
    alembic.import_alembic(project, in_abc)
    assert mock_abc_import.called


@patch('tpMayaLib.cmds.AbcExport')
def test_export_alembic(mock_abc_export):
    out_abc = os.path.join(data_path, 'abc_out.abc')
    alembic.export_alembic(out_abc)
    assert mock_abc_export.called


@patch('tpMayaLib.cmds.file')
def test_reference_alembic(mock_abc_import):
    project = MagicMock()
    project.name = 'Default'
    in_abc = os.path.join(data_path, 'abc_in.abc')
    alembic.reference_alembic(project, in_abc)
    assert mock_abc_import.called
