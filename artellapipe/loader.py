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

import tpDcc as tp
from tpDcc.libs.python import python


def init(do_reload=False, import_libs=True, dev=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    :param dev: bool, Whether artellapipe is initialized in dev mode or not
    """

    from tpDcc.libs.python import importer
    from artellapipe import register

    logger = create_logger()
    register.register_class('logger', logger)

    if not dev:
        import sentry_sdk
        try:
            sentry_sdk.init("https://eb70c73942e049e4a08f5a01ba788c4b@sentry.io/1771171")
        except (RuntimeError, ImportError):
            sentry_sdk.init("https://eb70c73942e049e4a08f5a01ba788c4b@sentry.io/1771171", default_integrations=False)

    class ArtellaPipe(importer.Importer, object):
        def __init__(self, debug=False):
            super(ArtellaPipe, self).__init__(module_name='artellapipe', debug=debug)

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
        'artellapipe.core',
        'artellapipe.widgets'
    ]

    if import_libs:
        import tpDcc.loader
        tpDcc.loader.init(do_reload=do_reload, dev=dev)
        # import tpNameIt
        # tpNameIt.init(do_reload=do_reload)

    artella_importer = importer.init_importer(importer_class=ArtellaPipe, do_reload=False, debug=dev)
    artella_importer.import_packages(
        order=packages_order,
        only_packages=False)
    if do_reload:
        artella_importer.reload_all()

    init_dcc(do_reload=do_reload)


def init_dcc(do_reload=False):
    """
    Checks DCC we are working on an initializes proper variables
    :param do_reload: bool
    """

    if tp.is_maya():
        from artellapipe.dccs import maya as maya_dcc
        maya_dcc.init(do_reload=do_reload)
    elif tp.is_houdini():
        from artellapipe.dccs import houdini as houdini_dcc
        houdini_dcc.init(do_reload=do_reload)


def create_logger():
    """
    Returns logger of current module
    """

    logging.config.fileConfig(get_logging_config(), disable_existing_loggers=False)
    logger = logging.getLogger('artellapipe')

    return logger


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


def set_project(project_class, do_reload=False):
    """
    This functions sets the given class instance as the current Artella project used
    :param project_class: ArtellaProject
    """

    import artellapipe

    # Register configuration paths
    # NOTE: We must do it before instantiating the project, otherwise project configuration won't be available
    register_configs()

    # Create and register project
    project_inst = project_class()
    artellapipe.__dict__['project'] = project_inst
    artellapipe.__dict__[project_class.__name__.lower()] = project_inst

    register_resources(project_inst)
    register_libs(project_inst, do_reload=do_reload)
    register_tools(project_inst, dev=project_inst.get_environment().lower() == 'development', do_reload=do_reload)
    project_inst.init()


def register_configs():
    """
    Registers aretellapipe configuration files
    """

    from artellapipe import config

    artella_configs_path = os.environ.get('ARTELLA_CONFIGS_PATH', None)
    if artella_configs_path and os.path.isdir(artella_configs_path):
        tp.ConfigsMgr().register_package_configs('artellapipe', artella_configs_path)
    else:
        tp.ConfigsMgr().register_package_configs('artellapipe', os.path.dirname(config.__file__))


def register_resources(project):
    """
    Registers artellapipe and project resources
    """

    project_resources_paths = project.get_resources_paths()
    for resources_key, resources_path in project_resources_paths.items():
        if not os.path.isdir(resources_path):
            continue
        if resources_key:
            tp.ResourcesMgr().register_resource(resources_path, resources_key)
        else:
            tp.ResourcesMgr().register_resource(resources_path)

    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    tp.ResourcesMgr().register_resource(resources_path)


def register_libs(project_inst, do_reload=False):
    """
    Function that registera all available libs for given project
    :param project_inst: ArtellaProject
    :param do_reload: bool
    """

    import artellapipe

    if python.is_python2():
        import pkgutil as loader
    else:
        import importlib as loader

    libs = project_inst.config_data.get('libs', list())
    libs_to_register = dict()
    libs_path = '{}.libs.{}'
    for lib_name in libs:
        for pkg in ['artellapipe', project_inst.get_clean_name()]:
            pkg_path = libs_path.format(pkg, lib_name)
            try:
                pkg_loader = loader.find_loader(pkg_path)
            except Exception:
                pkg_loader = None
            if pkg_loader is not None:
                if lib_name not in libs_to_register:
                    libs_to_register[lib_name] = list()
                libs_to_register[lib_name].append(pkg_loader)

    for pkg_loaders in libs_to_register.values():
        for pkg_loader in pkg_loaders:
            artellapipe.LibsMgr().register_lib(project=project_inst, pkg_loader=pkg_loader, do_reload=do_reload)


def register_tools(project_inst, dev=False, do_reload=False):
    """
    Function that register all available tools for given project
    :param project_inst: ArtellaProject
    """

    import artellapipe.toolsets

    package_names = ['artellapipe', project_inst.get_clean_name()]

    # Tools
    project_name = project_inst.get_clean_name()
    tools_to_load = project_inst.config_data.get('tools', list())
    config_dict = {'project': project_name}
    tp.ToolsMgr().load_package_tools(
        package_name='artellapipe', root_package_name=project_name, tools_to_load=tools_to_load,
        config_dict=config_dict, dev=dev)
    tp.ToolsMgr().load_package_tools(
        package_name=project_name, tools_to_load=tools_to_load, config_dict=config_dict, dev=dev)

    artellapipe.MenusMgr().create_menus(project_inst.get_clean_name(), project=project_inst)

    # Toolsets
    # NOTE: Project specific toolsets paths MUST be registered in project specific loader
    # TODO: Register a default project path where toolsets can be located
    # NOTE: We can still using project specific loader to register custom toolset paths
    tp.ToolsetsMgr().register_path('artellapipe', os.path.dirname(os.path.abspath(artellapipe.toolsets.__file__)))
    for project_toolset_path in project_inst.get_toolsets_paths():
        tp.ToolsetsMgr().register_path(project_inst.get_clean_name(), project_toolset_path)
    for package_name in package_names:
        tp.ToolsetsMgr().load_registered_toolsets(
            package_name, tools_to_load=tools_to_load, dev=dev, do_reload=do_reload)
