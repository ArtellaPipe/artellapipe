#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle libs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import importlib
import traceback
import logging.config

import tpDcc
from tpDcc.libs.python import importer, python

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe

LOGGER = logging.getLogger('artellapipe')


class LibsManager(object):
    """
    Class that handles all libs
    """

    _libs = dict()

    @property
    def libs(self):
        return self.__class__._libs

    def register_lib(self, project, pkg_loader):
        project_name = project.get_clean_name()
        lib_path = pkg_loader.fullname
        if pkg_loader in self.libs:
            LOGGER.warning('Lib with path "{}" is already registered. Skipping ...'.format(lib_path))
            return False

        mod_config_settings = None
        try:
            mod = importlib.import_module(pkg_loader.fullname)
            if hasattr(mod, 'config_settings'):
                mod_config_settings = mod.config_settings
        except Exception as exc:
            pass

        config_dict = {
            'join': os.path.join,
            'user': os.path.expanduser('~'),
            'filename': pkg_loader.filename,
            'fullname': pkg_loader.fullname,
            'project': project_name
        }
        if mod_config_settings:
            config_dict.update(mod_config_settings)

        lib_config = self._create_lib_config(
            project_name=project_name, lib_path=lib_path, project=project,
            config_dict=config_dict
        )

        lib_id = lib_config.data.get('id', None)
        lib_name = lib_config.data.get('name', None)
        skip_modules = lib_config.data.get('skip_modules', list())
        if not lib_id:
            LOGGER.warning(
                'Impossible to register library "{}" because its ID is not defined'.format(lib_path))
            return False
        if not lib_name:
            LOGGER.warning(
                'Impossible to register library "{}" because its ID is not defined'.format(lib_path))
            return False
        if lib_id in self.libs:
            LOGGER.warning(
                'Impossible to register library "{}" because its ID "{}" is already defined.'.format(lib_path, lib_id))
            return False

        version_found = None
        for sub_module in loader.walk_packages([pkg_loader.filename]):
            importer, sub_module_name, _ = sub_module
            skip_module = False
            for skip in skip_modules:
                if sub_module_name == skip or sub_module_name.startswith(skip):
                    skip_module = True
                    break
            if skip_module:
                continue
            if sub_module_name in skip_modules or sub_module_name:
                continue
            qname = pkg_loader.fullname + '.' + sub_module_name
            try:
                mod = importer.find_module(sub_module_name).load_module(sub_module_name)
            except Exception as exc:
                msg = 'Impossible to register Library: {}. Exception raised: {} | {}'.format(
                    lib_path, exc, traceback.format_exc())
                LOGGER.warning(msg)
                continue

            if qname.endswith('__version__') and hasattr(mod, '__version__'):
                if version_found:
                    LOGGER.warning('Already found version: "{}" for "{}"'.format(version_found, lib_path))
                else:
                    version_found = getattr(mod, '__version__')

        # Register tool resources
        def_resources_path = os.path.join(pkg_loader.filename, 'resources')
        resources_path = lib_config.data.get('resources_path', def_resources_path)
        if not resources_path or not os.path.isdir(resources_path):
            resources_path = def_resources_path
        if os.path.isdir(resources_path):
            tpDcc.ResourcesMgr().register_resource(resources_path, key='tools')

        self.libs[lib_id] = {
            'name': lib_name,
            'config': lib_config,
            'lib_loader': pkg_loader,
            'lib_package': pkg_loader.fullname,
            'lib_package_path': pkg_loader.filename,
            'version': version_found if version_found is not None else "0.0.0"
        }

        LOGGER.info('Library "{}" registered successfully!'.format(lib_path))

        self.load_library(lib_path=lib_id)

        return True

    def load_library(self, lib_path):

        lib_to_load = None

        # We pass a tool ID
        if lib_path in self.libs:
            lib_to_load = lib_path
        else:
            # We pass a name or tool path
            for lid_id in self.libs.keys():
                path = self.libs[lid_id]['lib_package']
                sec_path = path.replace('.', '-')
                if sec_path == lib_path:
                    lib_to_load = lid_id
                    break
                else:
                    lib_name = path.split('.')[-1]
                    if lib_name == lib_path:
                        lib_to_load = lid_id
                        break

        if not lib_to_load or lib_to_load not in self.libs:
            LOGGER.warning('Lib "{}" is not registered. Impossible to run!'.format(lib_path))
            return

        pkg_loader = self.libs[lib_to_load]['lib_loader']
        lib_config = self.libs[lib_to_load]['config']

        sentry_id = lib_config.data.get('sentry_id', None)
        if sentry_id:
            import sentry_sdk
            sentry_sdk.init(sentry_id)

        # Create tool log directory
        default_logger_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artellapipe', 'logs', 'libs'))
        default_logging_config = os.path.join(pkg_loader.filename, '__logging__.ini')
        logger_dir = lib_config.data.get('logger_dir', default_logger_dir)
        if not os.path.isdir(logger_dir):
            os.makedirs(logger_dir)
        logging.config.fileConfig(
            lib_config.data.get('logging_file', default_logging_config), disable_existing_loggers=False)

        # Import library modules
        mod = importlib.import_module(pkg_loader.fullname)
        # skip_modules = ['{}.{}'.format(pkg_loader.fullname, m) for m in lib_config.data.get('skip_modules', list())]
        # importer.init_importer(package=pkg_loader.fullname, skip_modules=skip_modules)

        mod.__dict__['config'] = lib_config

        dev = True if artellapipe.project.is_dev() else False
        if hasattr(mod, 'init'):
            mod.init(dev=dev)

        return True

    def _create_lib_config(self, project_name, lib_path, project, config_dict):
        lib_config = tpDcc.ConfigsMgr().get_config(
            config_name=lib_path.replace('.', '-'),
            package_name=project_name,
            root_package_name='artellapipe',
            environment=project.get_environment(),
            config_dict=config_dict
        )

        return lib_config
