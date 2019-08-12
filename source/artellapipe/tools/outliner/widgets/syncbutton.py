#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for sync buttons
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import ast
import time
import string
import webbrowser
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *