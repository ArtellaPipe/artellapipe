#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artellapipe
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

# For autocompletion
if False:
    from artellapipe.core import asset as core_asset, node, shot, sequence
    from artellapipe.managers import assets, files, names, shaders, shots, sequences, menus, shelf, tools, libs
    from artellapipe.managers import tracking, dependencies, playblasts, ocio
    from artellapipe.widgets import dialog, window, syncdialog

    Asset = core_asset.ArtellaAsset
    AssetNode = node.ArtellaAssetNode
    Shot = shot.ArtellaShot
    Sequence = sequence.ArtellaSequence
    Window = window.ArtellaWindow
    Dialog = dialog.ArtellaDialog
    SyncFileDialog = syncdialog.ArtellaSyncFileDialog
    SyncPathDialog = syncdialog.ArtellaSyncPathDialog
    AssetsMgr = assets.AssetsManager
    FilesMgr = files.FilesManager
    NamesMgr = names.NamesManager
    ShadersMgr = shaders.ShadersManager
    ShotsMgr = shots.ShotsManager
    SequencesMgr = sequences.SequencesManager
    MenusMgr = menus.MenusManager
    LibsMgr = libs.LibsManager
    ToolsMgr = tools.ToolsManager
    DepsMgr = dependencies.DependenciesManager
    Tracker = tracking.TrackingManager
    OCIOMgr = ocio.OCIOManager
    PlayblastsMgr = playblasts.PlayblastsManager


from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
