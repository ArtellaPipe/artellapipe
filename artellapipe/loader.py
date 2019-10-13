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

import os
import inspect
import logging.config


def init(do_reload=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    """

    import sentry_sdk
    try:
        sentry_sdk.init("https://eb70c73942e049e4a08f5a01ba788c4b@sentry.io/1771171")
    except RuntimeError:
        sentry_sdk.init("https://eb70c73942e049e4a08f5a01ba788c4b@sentry.io/1771171", default_integrations=False)

    from tpPyUtils import importer

    class ArtellaPipe(importer.Importer, object):
        def __init__(self):
            super(ArtellaPipe, self).__init__(module_name='artellapipe')

        def get_module_path(self):
            """
            Returns path where tpNameIt module is stored
            :return: str
            """

            try:
                mod_dir = os.path.dirname(
                    inspect.getframeinfo(inspect.currentframe()).filename)
            except Exception:
                try:
                    mod_dir = os.path.dirname(__file__)
                except Exception:
                    try:
                        import artellapipe
                        mod_dir = artellapipe.__path__[0]
                    except Exception:
                        return None

            return mod_dir

    packages_order = [
        'artellapipe.utils',
        'artellapipe.gui',
        'artellapipe.core'
    ]

    artella_importer = importer.init_importer(importer_class=ArtellaPipe, do_reload=False)
    artella_importer.import_packages(order=packages_order, only_packages=False)
    if do_reload:
        artella_importer.reload_all()

    create_logger_directory()

    from artellapipe.utils import resource
    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    resource.ResourceManager().register_resource(resources_path)


def create_logger_directory():
    """
    Creates artellapipe logger directory
    """

    artellapipe_logger_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artellapipe', 'logs'))
    if not os.path.isdir(artellapipe_logger_dir):
        os.makedirs(artellapipe_logger_dir)


def get_logging_config():
    """
    Returns logging configuration file path
    :return: str
    """

    create_logger_directory()

    return os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))


def get_logging_level():
    """
    Returns logging level to use
    :return: str
    """

    if os.environ.get('ARTELLAPIPE_LOG_LEVEL', None):
        return os.environ.get('ARTELLAPIPE_LOG_LEVEL')

    return os.environ.get('ARTELLAPIPE_LOG_LEVEL', 'WARNING')


def set_project(project_class):
    """
    This functions sets the given class instance as the current Artella project used
    :param project_class: ArtellaProject
    """

    import artellapipe
    project_inst = project_class()
    artellapipe.__dict__['project'] = project_inst
    artellapipe.__dict__[project_class.__name__.lower()] = project_inst
    project_inst.init()


# Load logger configuration
logging.config.fileConfig(get_logging_config(), disable_existing_loggers=False)
