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
import logging.config

# =================================================================================

PACKAGE = 'artellapipe'

# =================================================================================


def init(import_libs=True, dev=False):
    """
    Initializes module
    :param import_libs: bool, Whether to import deps libraries by default or not
    :param dev: bool, Whether artellapipe is initialized in dev mode or not
    """

    import tpDcc
    import tpDcc.loader as dcc_loader
    from tpDcc.libs.python import importer
    from artellapipe import register

    if dev:
        register.cleanup()

    logger = create_logger()
    register.register_class('logger', logger)

    if not dev:
        import sentry_sdk
        try:
            sentry_sdk.init("https://eb70c73942e049e4a08f5a01ba788c4b@sentry.io/1771171")
        except (RuntimeError, ImportError):
            sentry_sdk.init("https://eb70c73942e049e4a08f5a01ba788c4b@sentry.io/1771171", default_integrations=False)

    if import_libs:
        dcc_loader.init(dev=dev)
        # import tpNameIt
        # tpNameIt.init(do_reload=do_reload)

    skip_modules = ['{}.{}'.format(PACKAGE, name) for name in ['loader', 'dccs', 'libs', 'tools']]
    importer.init_importer(package=PACKAGE, skip_modules=skip_modules)

    # Get DCC
    dcc_mod = tpDcc.loader.get_dcc_loader_module(package='artellapipe.dccs')
    if dcc_mod:
        dcc_mod.init(dev=dev)

    # When working in production, we use custom exception hook to show message box to user
    if not dev:
        from artellapipe.utils import exceptions
        exceptions.ArtellaExceptionHook()


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


def set_project(project_class):
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
    register_libs(project_inst)
    register_tools(project_inst, dev=project_inst.get_environment().lower() == 'development')
    project_inst.init()


def register_configs():
    """
    Registers aretellapipe configuration files
    """

    import tpDcc as tp
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

    import tpDcc as tp

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


def register_libs(project_inst):
    """
    Function that registera all available libs for given project
    :param project_inst: ArtellaProject
    """

    import artellapipe
    from tpDcc.libs.python import python

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
            artellapipe.LibsMgr().register_lib(project=project_inst, pkg_loader=pkg_loader)


def register_tools(project_inst, dev=False):
    """
    Function that register all available tools for given project
    :param project_inst: ArtellaProject
    :param dev: bool
    """

    import tpDcc as tp
    import artellapipe.toolsets

    package_names = ['artellapipe', project_inst.get_clean_name()]

    # Tools
    project_name = project_inst.get_clean_name()
    tools_to_register = project_inst.config_data.get('tools', list())
    config_dict = {'project': project_name}
    tp.ToolsMgr().register_package_tools(
        pkg_name=PACKAGE, root_pkg_name=project_name, tools_to_register=tools_to_register,
        config_dict=config_dict, dev=dev)
    tp.ToolsMgr().register_package_tools(
        pkg_name=project_name, tools_to_register=tools_to_register, config_dict=config_dict, dev=dev)

    tp.ToolsMgr().load_registered_tools(project_name)
    tp.ToolsMgr().load_registered_tools(PACKAGE)

    artellapipe.MenusMgr().create_menus(project_inst.get_clean_name(), project=project_inst)

    # Toolsets
    # NOTE: Project specific toolsets paths MUST be registered in project specific loader
    # TODO: Register a default project path where toolsets can be located
    # NOTE: We can still using project specific loader to register custom toolset paths
    tp.ToolsetsMgr().register_path('artellapipe', os.path.dirname(os.path.abspath(artellapipe.toolsets.__file__)))
    for project_toolset_path in project_inst.get_toolsets_paths():
        tp.ToolsetsMgr().register_path(project_inst.get_clean_name(), project_toolset_path)
    for package_name in package_names:
        tp.ToolsetsMgr().load_registered_toolsets(package_name, tools_to_load=tools_to_register)
