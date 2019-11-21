#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle tools
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import inspect
import traceback
import logging.config

from tpPyUtils import importer, decorators, python

import artellapipe.register
from artellapipe.core import tool
from artellapipe.utils import exceptions, resource

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

LOGGER = logging.getLogger()


class ToolImporter(importer.Importer, object):
    def __init__(self, tool_pkg, debug=False):

        self.tool_path = tool_pkg.filename

        super(ToolImporter, self).__init__(module_name=tool_pkg.fullname, debug=debug)

    def get_module_path(self):
        """
        Returns path where module is located
        :return: str
        """

        return self.tool_path


class ToolsManager(object):
    """
    Class that handles all tools
    """

    def __init__(self):

        self._tools = dict()

    @property
    def tools(self):
        return self._tools

    def register_tool(self, project, pkg_loader):
        """
        Register tool given path
        :param str tool_path: path to the module (for example, artellapipe.tools.welcome)
        """

        from artellapipe.core import config

        project_name = project.get_clean_name()
        tool_path = pkg_loader.fullname
        if pkg_loader in self._tools:
            LOGGER.warning('Tool with path "{}" is already registered. Skipping ...'.format(tool_path))
            return False

        tool_config = config.ArtellaConfiguration(
            project_name=project_name,
            config_name=tool_path.replace('.', '-'),
            environment=project.get_environment(),
            config_dict={
                'join': os.path.join,
                'user': os.path.expanduser('~'),
                'filename': pkg_loader.filename,
                'fullname': pkg_loader.fullname,
                'project': project_name
            }
        )
        tool_id = tool_config.data.get('id', None)
        tool_name = tool_config.data.get('name', None)
        tool_icon = tool_config.data.get('icon', None)
        if not tool_id:
            LOGGER.warning(
                'Impossible to register tool "{}" because its ID is not defined'.format(tool_path))
            return False
        if not tool_name:
            LOGGER.warning(
                'Impossible to register tool "{}" because its ID is not defined'.format(tool_path))
            return False
        if tool_id in self._tools:
            LOGGER.warning(
                'Impossible to register tool "{}" because its ID "{}" is already defined.'.format(tool_path, tool_id))
            return False

        tools_found = list()
        version_found = None
        for sub_module in loader.walk_packages([pkg_loader.filename]):
            importer, sub_module_name, _ = sub_module
            qname = pkg_loader.fullname + '.' + sub_module_name
            try:
                mod = importer.find_module(sub_module_name).load_module(sub_module_name)
            except Exception as exc:
                msg = 'Impossible to register Tool: {}. Exception raised: {} | {}'.format(
                    tool_path, exc, traceback.format_exc())
                LOGGER.warning(msg)
                continue

            if qname.endswith('__version__') and hasattr(mod, '__version__'):
                if version_found:
                    LOGGER.warning('Already found version: "{}" for "{}"'.format(version_found, tool_path))
                else:
                    version_found = getattr(mod, '__version__')

            for cname, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, artellapipe.Tool):
                    tools_found.append((qname, version_found))
                    version_found = None

        if not tools_found:
            LOGGER.warning('No Tools found in Module "{}". Skipping ...'.format(tool_path))
            return False
        if len(tools_found) > 1:
            LOGGER.warning('Multiple Tools Found ({}) in Module "{}". Skipping ...'.format(len(tools_found), tool_path))
            return False

        tool_found = tools_found[0]

        tool_loader = loader.find_loader(tool_found[0])

        # Register tool resources
        def_resources_path = os.path.join(pkg_loader.filename, 'resources')
        resources_path = tool_config.data.get('resources_path', def_resources_path)
        if os.path.isdir(resources_path):
            resource.ResourceManager().register_resource(resources_path, key='tools')
        else:
            LOGGER.info('No resources directory found for tool "{}" ...'.format(tool_name))

        self._tools[tool_id] = {
            'name': tool_name,
            'icon': tool_icon,
            'loader': pkg_loader,
            'config': tool_config,
            'tool_loader': tool_loader,
            'tool_package': pkg_loader.fullname,
            'tool_package_path': pkg_loader.filename,
            'version': tool_found[1] if tool_found[1] is not None else "0.0.0"
        }

        LOGGER.info('Tool "{}" registered successfully!'.format(tool_path))

        return True

    def get_tool_data_from_id(self, tool_id):
        """
        Returns registered tool from its id
        :param tool_id: str
        :return: dict
        """

        return self._tools[tool_id] if tool_id in self._tools else None

    def get_tool_data_from_name(self, tool_name, as_dict=False):
        """
        Returns registered tool from its name
        :param tool_name: str
        :return:
        """

        if not tool_name:
            return None

        for tool_id, tool_data in self._tools.items():
            current_name = tool_data.get('name', None)
            if current_name == tool_name:
                if as_dict:
                    return {
                        tool_id: self._tools[tool_id]
                    }
                else:
                    return self._tools[tool_id]

        return None

    def get_tool_data_from_tool(self, tool, as_dict=False):
        """
        Returns registered tool data from a tool object
        :return: dict
        """

        if not hasattr(tool, 'config'):
            return None

        tool_id = tool.config.data.get('id', None)
        if tool_id and tool_id in self._tools:
            if as_dict:
                return {
                    tool_id: self._tools[tool_id]
                }
            else:
                return self._tools[tool_id]

        return None

    def get_tool_menus(self):
        """
        Returns dictionary with the menu info for all the registered tools
        :return: dict
        """

        tool_menus = dict()

        for tool_path, tool_data in self._tools.items():
            tool_config = tool_data['config']
            if not tool_config:
                continue
            menu_data = tool_config.data.get('menu', None)
            if not menu_data:
                continue

            tool_menus[tool_path] = menu_data

        return tool_menus

    def get_tool_shelfs(self):
        """
        Returns dictionary with the shelf info for all the registered tools
        :return: dict
        """

        tool_shelfs = dict()

        for tool_path, tool_data in self._tools.items():
            tool_config = tool_data['config']
            if not tool_config:
                continue
            shelf_data = tool_config.data.get('shelf', None)
            if not shelf_data:
                continue

            tool_shelfs[tool_path] = shelf_data

        return tool_shelfs

    def run_tool(self, project, tool_path, do_reload=False, debug=False, extra_args=None):
        """
        Runs tool with the given path or name
        :param str tool_path: name or path of the tool (artellapipe.tools.welcome or welcome)
        """

        from artellapipe.widgets import dialog

        tool_to_run = None

        if extra_args is None:
            extra_args = dict()

        # We pass a tool ID
        if tool_path in self._tools:
            tool_to_run = tool_path
        else:
            # We pass a name or tool path
            for tool_id in self._tools.keys():
                path = self._tools[tool_id]['tool_package']
                sec_path = path.replace('.', '-')
                if sec_path == tool_path:
                    tool_to_run = tool_id
                    break
                else:
                    tool_name = path.split('.')[-1]
                    if tool_name == tool_path:
                        tool_to_run = tool_id
                        break

        if not tool_to_run or tool_to_run not in self._tools:
            LOGGER.warning('Tool "{}" is not registered. Impossible to run!'.format(tool_path))
            return

        pkg_loader = self._tools[tool_to_run]['loader']
        tool_config = self._tools[tool_to_run]['config']
        tool_fullname = self._tools[tool_to_run]['loader'].fullname
        tool_version = self._tools[tool_to_run]['version']

        sentry_id = tool_config.data.get('sentry_id', None)
        if sentry_id and not project.is_dev():
            import sentry_sdk
            sentry_sdk.init(sentry_id, release=tool_version)

        # Initialize and reload tool modules if necessary
        tool_importer = ToolImporter(pkg_loader, debug=debug)
        import_order = ['{}.{}'.format(pkg_loader.fullname, mod) for mod in
                        tool_config.data.get('import_order', list())]
        tool_importer.import_packages(order=import_order, only_packages=False)
        if do_reload:
            tool_importer.reload_all()

        # Create tool log directory
        default_logger_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artellapipe', 'logs', 'tools'))
        default_logging_config = os.path.join(pkg_loader.filename, '__logging__.ini')
        logger_dir = tool_config.data.get('logger_dir', default_logger_dir)
        if not os.path.isdir(logger_dir):
            os.makedirs(logger_dir)
        logging.config.fileConfig(
            tool_config.data.get('logging_file', default_logging_config), disable_existing_loggers=False)
        tool_logger_level_env = '{}_LOG_LEVEL'.format(pkg_loader.fullname.replace('.', '_').upper())
        LOGGER.setLevel(os.environ.get(tool_logger_level_env, tool_config.data.get('logger_level', 'WARNING')))

        try:
            tool_found = None
            for sub_module in loader.walk_packages([self._tools[tool_to_run]['tool_package_path']]):
                importer, sub_module_name, _ = sub_module
                mod = importer.find_module(sub_module_name).load_module(sub_module_name)
                for cname, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, artellapipe.Tool):
                        tool_found = obj
                        break

            if not tool_found:
                LOGGER.error("Error while launching tool: {}".format(tool_fullname))
                return None

            if extra_args:
                tool_widget = tool_found(project=project, config=tool_config, **extra_args)
            else:
                tool_widget = tool_found(project=project, config=tool_config, **extra_args)

            tool_name = tool_config.data.get('name', 'Tool')
            tool_logo = tool_config.data.get('logo', project.get_clean_name())
            tool_url = tool_config.data.get('url', None)

            if tool_found.ATTACHER_TYPE == tool.ToolAttacher.Window:
                win_name = '{}_{}_Window'.format(project.name, tool_name)
                tool_win = artellapipe.Window(name=win_name, project=project, tool=tool_widget)
                tool_win.setWindowTitle('{} - {} - {}'.format(project.name, tool_name, tool_version))
                tool_win._dragger._button_closed.clicked.disconnect()
                tool_win._dragger._button_closed.clicked.connect(tool_widget.close_tool_attacher)
                tool_win.add_logo(resource.ResourceManager().pixmap(tool_logo), 910, 0)
                tool_icon = tool_config.data.get('icon', None)
                if tool_icon:
                    tool_win.setWindowIcon(resource.ResourceManager().icon(tool_icon))
                if tool_url:
                    tool_win.set_info_url(tool_url)
                tool_widget.set_attacher(tool_win)
                tool_win.show()
            elif tool_found.ATTACHER_TYPE == tool.ToolAttacher.Dialog:
                tool_dlg = dialog.ArtellaDialog(project=project, tool=tool_widget)
                tool_dlg.setObjectName('{}_{}_Dialog'.format(project.name, tool_name))
                tool_dlg.setWindowTitle('{} - {} - {}'.format(project.name, tool_name, tool_version))
                tool_dlg.add_logo(resource.ResourceManager().pixmap(tool_logo), 910, 0)
                tool_icon = tool_config.data.get('icon', None)
                if tool_icon:
                    tool_dlg.setWindowIcon(resource.ResourceManager().icon(tool_icon))
                tool_widget.set_attacher(tool_dlg)
                tool_dlg.exec_()

            return tool_widget
        except Exception as exc:
            exceptions.capture_sentry_exception(exc)

        return None

    def get_config(self, tool_id):
        if not tool_id:
            return None

        if tool_id:
            tool_data = self.get_tool_data_from_id(tool_id)
            if tool_data:
                return tool_data.get('config', None)

        LOGGER.warning(
            'Impossible to retrieve configuration of tool: "{}" because tool is not registered'.format(tool_id))

        return None


@decorators.Singleton
class ArtellaToolsManagerSingleton(ToolsManager, object):
    def __init__(self):
        ToolsManager.__init__(self)


artellapipe.register.register_class('ToolsMgr', ArtellaToolsManagerSingleton)
