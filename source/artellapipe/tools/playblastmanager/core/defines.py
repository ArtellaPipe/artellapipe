#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions used by PlayblastManager
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDccLib as tp

from collections import OrderedDict


class TimeRanges(object):
    RANGE_TIME_SLIDER = 'Time Slider'
    RANGE_START_END = 'Start/End'
    CURRENT_FRAME = 'Current Frame'
    CUSTOM_FRAMES = 'Custom Frames'


class ScaleSettings(object):
    SCALE_WINDOW = 'From Window'
    SCALE_RENDER_SETTINGS = 'From Render Settings'
    SCALE_CUSTOM = 'Custom'


CameraOptions = {
    "displayGateMask": False,
    "displayResolution": False,
    "displayFilmGate": False,
    "displayFieldChart": False,
    "displaySafeAction": False,
    "displaySafeTitle": False,
    "displayFilmPivot": False,
    "displayFilmOrigin": False,
    "overscan": 1.0,
    "depthOfField": False,
}

DisplayOptions = {
    "displayGradient": True,
    "background": (0.631, 0.631, 0.631),
    "backgroundTop": (0.535, 0.617, 0.702),
    "backgroundBottom": (0.052, 0.052, 0.052),
}

_DisplayOptionsRGB = set(["background", "backgroundTop", "backgroundBottom"])

ViewportOptions = {
    "rendererName": "vp2Renderer",
    "fogging": False,
    "fogMode": "linear",
    "fogDensity": 1,
    "fogStart": 1,
    "fogEnd": 1,
    "fogColor": (0, 0, 0, 0),
    "shadows": False,
    "displayTextures": True,
    "displayLights": "default",
    "useDefaultMaterial": False,
    "wireframeOnShaded": False,
    "displayAppearance": 'smoothShaded',
    "selectionHiliteDisplay": False,
    "headsUpDisplay": True,
    "imagePlane": True,
    "nurbsCurves": False,
    "nurbsSurfaces": False,
    "polymeshes": True,
    "subdivSurfaces": False,
    "planes": True,
    "cameras": False,
    "controlVertices": True,
    "lights": False,
    "grid": False,
    "hulls": True,
    "joints": False,
    "ikHandles": False,
    "deformers": False,
    "dynamics": False,
    "fluids": False,
    "hairSystems": False,
    "follicles": False,
    "nCloths": False,
    "nParticles": False,
    "nRigids": False,
    "dynamicConstraints": False,
    "locators": True,                   # We need to enable this option by default so Mask plugin can is showed
    "manipulators": False,
    "dimensions": False,
    "handles": False,
    "pivots": False,
    "textures": False,
    "strokes": False
}

Viewport2Options = {
    "consolidateWorld": True,
    "enableTextureMaxRes": False,
    "bumpBakeResolution": 64,
    "colorBakeResolution": 64,
    "floatingPointRTEnable": True,
    "floatingPointRTFormat": 1,
    "gammaCorrectionEnable": False,
    "gammaValue": 2.2,
    "lineAAEnable": False,
    "maxHardwareLights": 8,
    "motionBlurEnable": False,
    "motionBlurSampleCount": 8,
    "motionBlurShutterOpenFraction": 0.2,
    "motionBlurType": 0,
    "multiSampleCount": 8,
    "multiSampleEnable": False,
    "singleSidedLighting": False,
    "ssaoEnable": False,
    "ssaoAmount": 1.0,
    "ssaoFilterRadius": 16,
    "ssaoRadius": 16,
    "ssaoSamples": 16,
    "textureMaxResolution": 4096,
    "threadDGEvaluation": False,
    "transparencyAlgorithm": 1,
    "transparencyQuality": 0.33,
    "useMaximumHardwareLights": True,
    "vertexAnimationCache": 0
}

if tp.is_maya():
    import maya.mel as mel
    if mel.eval('getApplicationVersionAsFloat') > 2015:
        ViewportOptions.update({
            "motionTrails": False
        })
        Viewport2Options.update({
            "hwFogAlpha": 1.0,
            "hwFogFalloff": 0,
            "hwFogDensity": 0.1,
            "hwFogEnable": False,
            "holdOutDetailMode": 1,
            "hwFogEnd": 100.0,
            "holdOutMode": True,
            "hwFogColorR": 0.5,
            "hwFogColorG": 0.5,
            "hwFogColorB": 0.5,
            "hwFogStart": 0.0,
        })


OBJECT_TYPES = OrderedDict()
OBJECT_TYPES['NURBS Curves'] = 'nurbsCurves'
OBJECT_TYPES['NURBS Surfaces'] = 'nurbsSurfaces'
OBJECT_TYPES['NURBS CVs'] = 'controlVertices'
OBJECT_TYPES['NURBS Hulls'] = 'hulls'
OBJECT_TYPES['Polygons'] = 'polymeshes'
OBJECT_TYPES['Subdiv Surfaces'] = 'subdivSurfaces'
OBJECT_TYPES['Planes'] = 'planes'
OBJECT_TYPES['Lights'] = 'lights'
OBJECT_TYPES['Cameras'] = 'cameras'
OBJECT_TYPES['Image Planes'] = 'imagePlane'
OBJECT_TYPES['Joints'] = 'joints'
OBJECT_TYPES['IK Handles'] = 'ikHandles'
OBJECT_TYPES['Deformers'] = 'deformers'
OBJECT_TYPES['Dynamics'] = 'dynamics'
OBJECT_TYPES['Particle Instancers'] = 'particleInstancers'
OBJECT_TYPES['Fluids'] = 'fluids'
OBJECT_TYPES['Hair Systems'] = 'hairSystems'
OBJECT_TYPES['Follicles'] = 'follicles'
OBJECT_TYPES['nCloths'] = 'nCloths'
OBJECT_TYPES['nParticles'] = 'nParticles'
OBJECT_TYPES['nRigids'] = 'nRigids'
OBJECT_TYPES['Dynamic Constraints'] = 'dynamicConstraints'
OBJECT_TYPES['Locators'] = 'locators'
OBJECT_TYPES['Dimensions'] = 'dimensions'
OBJECT_TYPES['Pivots'] = 'pivots'
OBJECT_TYPES['Handles'] = 'handles'
OBJECT_TYPES['Textures Placements'] = 'textures'
OBJECT_TYPES['Strokes'] = 'strokes'
OBJECT_TYPES['Motion Trails'] = 'motionTrails'
OBJECT_TYPES['Plugin Shapes'] = 'pluginShapes'
OBJECT_TYPES['Clip Ghosts'] = 'clipGhosts'
OBJECT_TYPES['Grease Pencil'] = 'greasePencils'
OBJECT_TYPES['Manipulators'] = 'manipulators'
OBJECT_TYPES['Grid'] = 'grid'
OBJECT_TYPES['HUD'] = 'hud'