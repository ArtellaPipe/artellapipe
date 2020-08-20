"""
Module that contains manager for Artella files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import locale
import logging
import inspect
import tempfile
import importlib
import webbrowser

import six

import tpDcc as tp
from tpDcc.libs.python import python, osplatform, path as path_utils
from tpDcc.libs.qt.core import qtutils

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe
from artellapipe.libs import artella as artella_lib
from artellapipe.libs.artella.core import artellalib
from artellapipe.libs.naming.core import naminglib
from artellapipe.utils import exceptions

LOGGER = logging.getLogger('artellapipe')


class FilesManager(python.Singleton, object):

    _config = None
    _registered_file_classes = dict()

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tp.ConfigsMgr().get_config(
                config_name='artellapipe-files',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment()
            )

        return self.__class__._config

    @property
    def files(self):
        return self.config.get('files', default=dict())

    @property
    def file_classes(self):
        if not self.__class__._registered_file_classes:
            self._register_file_classes()

        return self.__class__._registered_file_classes

    def register_file_class(self, file_type, file_class):
        """
        Registers a new file class into the project
        :param file_type: str
        :param file_class: class
        """

        self.__class__._registered_file_classes[file_type] = file_class
        return True

    def get_file_class(self, file_type_name):
        """
        Returns file type by its name
        :param file_type_name: str
        :return: class
        """

        if not self.check_file_type(file_type_name):
            LOGGER.warning('File Type with name "{}" not registered!'.format(file_type_name))
            return

        return self.__class__._registered_file_classes[file_type_name]

    def check_file_type(self, file_type_name):
        """
        Returns whether or not give file type name corresponds to a valid file type
        :param file_type_name: str
        :return: bool
        """

        if file_type_name not in self.file_classes:
            return False

        return True

    def is_valid_file_type(self, file_type):
        """
        Returns whether the current file type is valid or not for current project
        :param file_type: str
        :return: bool
        """

        return file_type in self.files

    def get_file_type_info(self, file_type):
        """
        Returns dictionary with the information of the given file type
        :param file_type: str
        :return: dict
        """

        if not self.files:
            return None

        return self.files[file_type] if file_type in self.files else dict()

    def get_file_type_name(self, file_type):
        """
        Returns nice name of the given file type
        :param file_type: str
        :return: str
        """

        if not self.files:
            return

        if file_type not in self.files:
            return file_type

        return self.files[file_type].get('name', file_type)

    def get_file_type_extensions(self, file_type):
        """
        Returns extensions of the given file type
        :param file_type: str
        :return: list(str)
        """

        file_type_info = self.get_file_type_info(file_type)
        return file_type_info.get('extensions', list()) if file_type else list()

    def get_file_types_by_extension(self, file_type_extension):
        """
        Returns file type by the given extension
        :param file_type_extension: str
        :return: list
        """

        asset_files = self.files
        if not asset_files:
            return None

        valid_file_types = list()
        for file_type_name, file_type_class in self.file_classes.items():
            if file_type_extension in file_type_class.FILE_EXTENSIONS:
                valid_file_types.append(file_type_class)

        return valid_file_types

    def get_template(self, template_name):
        """
        Returns path template with the given name
        :param template_name: str
        :return: Template
        """

        template = naminglib.ArtellaNameLib().get_template(template_name)
        if not template:
            LOGGER.warning('No Template found with name: "{}"'.format(template_name))

        return template

    def parse_path(self, path):
        all_templates = naminglib.ArtellaNameLib().templates
        for template in all_templates:
            path_dict = naminglib.ArtellaNameLib().parse_template(template.name, path)
            if not path_dict:
                continue
            return path_dict

    def fix_path(self, path_to_fix, clean_path=True):
        """
        Converts path to a path relative to project environment variable
        :param path_to_fix: str
        :param clean_path: bool
        :return: str
        """

        self._check_project()

        project_env_var = artellapipe.project.env_var

        if clean_path:
            path_to_fix = path_utils.clean_path(path_to_fix)

        project_var = os.environ.get(project_env_var)
        if not project_var:
            return path_to_fix

        root_prefix = artella_lib.config.get('app', 'root_prefix')

        if path_to_fix.startswith('${}/'.format(project_env_var)):
            path_to_fix = path_to_fix.replace('${}/'.format(project_env_var), project_var)
        elif path_to_fix.startswith('${}/'.format(root_prefix)):
            path_to_fix = path_to_fix.replace('${}/'.format(root_prefix), project_var)

        return path_to_fix

    def relative_path(self, full_path):
        """
        Returns relative path of the given path relative to Project path
        :param full_path: str
        :return: str
        """

        self._check_project()

        return path_utils.clean_path(os.path.relpath(full_path, artellapipe.project.get_path()))

    def get_temp_path(self, *args):
        """
        Returns temporary folder path of the project
        :return: str
        """

        self._check_project()

        temp_path = '{temp}/' + artellapipe.project.get_clean_name() + '/pipeline/{user}'

        return path_utils.clean_path(os.path.join(self._format_path(temp_path), *args))

    def resolve_path(self, path_to_resolve):
        """
        Converts path to a valid full path
        :param path_to_resolve: str
        :return: str
        """

        self._check_project()

        path_to_resolve = path_to_resolve.replace('\\', '/')
        project_var = os.environ.get(artellapipe.project.env_var)
        if not project_var:
            return path_to_resolve

        if path_to_resolve.startswith(project_var):
            path_to_resolve = path_to_resolve.replace(project_var, '${}/'.format(artellapipe.project.env_var))

        return path_to_resolve

    def prefix_path_with_project_path(self, path_to_prefix, env_var=False):
        """
        Adds project path to given path as prefix
        :param path_to_prefix: str
        :param env_var: bool
        :return: str
        """

        self._check_project()

        if not path_to_prefix:
            return

        path_to_prefix = path_utils.clean_path(path_to_prefix)

        production_folder = artellapipe.project.get_production_folder()
        if production_folder:
            if path_to_prefix.startswith((production_folder, os.sep + production_folder, '/' + production_folder)):
                return self.prefix_path_with_artella_env_path(path_to_prefix)

        if env_var:
            project_env_var = artellapipe.project.env_var
            project_var = path_utils.clean_path(os.environ.get(project_env_var))
            if path_to_prefix.startswith(project_var):
                return path_to_prefix
            return path_utils.clean_path(os.path.join(project_var, path_to_prefix))
        else:
            project_path = path_utils.clean_path(artellapipe.project.get_path())
            if path_to_prefix.startswith(project_path):
                return path_to_prefix

            return path_utils.clean_path(os.path.join(project_path, path_to_prefix))

    def prefix_path_with_artella_env_path(self, path_to_prefix):
        """
        Adds Artella environment variable path to given path as prefix
        :param path_to_prefix: str
        :return: str
        """

        root_prefix = artella_lib.config.get('app', 'root_prefix')
        artella_var = os.environ.get(root_prefix, None)
        if not artella_var:
            return path_to_prefix

        return path_utils.join_path(artella_var, path_to_prefix)

    def sync_files(self, files):
        """
        Synchronizes given files from Artella server into user hard drive
        :param files: list(str)
        """

        self._check_project()

        files = python.force_list(files)

        sync_dialog = artellapipe.SyncFileDialog(project=artellapipe.project, files=files)
        sync_dialog.sync()

    def sync_paths(self, paths, recursive=False):
        """
        Synchronizes given paths from Artella server into user hard drive
        :param paths: list(str)
        """

        self._check_project()

        paths = python.force_list(paths)

        sync_dialog = artellapipe.SyncPathDialog(project=artellapipe.project, paths=paths, recursive=recursive)
        sync_dialog.sync()

    def sync_latest_published_version(self, file_to_sync):
        """
        Synchronizes given files from Artella server into user hard drive and make sure that the last version of the
        file is synchronized
        :param file_to_sync: str
        :return: tuple(str, str, str), tuple containing the version number, version name and version path
        """

        latest_version = self.get_latest_published_version(file_to_sync)
        if not latest_version:
            LOGGER.warning('No published version found for: "{}"'.format(file_to_sync))
            return None

        latest_publihsed_path = latest_version[2]
        print(latest_publihsed_path)

    def lock_file(self, file_path=None, notify=False):
        """
        Locks given file in Artella
        :param file_path: str
        :param notify: bool
        :return: bool
        """

        self._check_project()

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            return False

        valid_lock = artellalib.lock_file(file_path=file_path, force=True)
        if not valid_lock:
            return False

        if notify:
            artellapipe.project.notify(title='Lock File', msg='File "{}" locked successfully!'.format(file_path))

        return True

    def unlock_file(self, file_path=None, notify=False, warn_user=True):
        """
        Unlocks current file in Artella
        :param file_path: str
        :param notify: bool
        :param warn_user: bool
        :return: bool
        """

        self._check_project()

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            LOGGER.warning('File Path "{}" is not valid!'.format(valid_path))
            return False

        if warn_user:
            msg = 'If changes in file: \n\n{}\n\n are not submitted to Artella yet, submit them before ' \
                  'unlocking the file please. \n\n Do you want to continue?'.format(file_path)
            res = tp.Dcc.confirm_dialog(
                title='Unlock File', message=msg,
                button=['Yes', 'No'], default_button='Yes', cancel_button='No', dismiss_string='No')
            if res != tp.Dcc.DialogResult.Yes:
                return False

        artellalib.unlock_file(file_path=file_path)
        if notify:
            artellapipe.project.notify(title='Unlock File', msg='File "{}" unlocked successfully!'.format(file_path))

        return True

    def check_lock_status(self, file_path=None, show_message=False):
        """
        Returns the current lock status of the file in Artella
        :param file_path: stro
        :param show_message: bool
        :return: bool
        """

        self._check_project()

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            LOGGER.warning('File Path "{}" is not valid!'.format(valid_path))
            return False

        in_edit_mode, is_locked_by_me = artellalib.is_locked(file_path=file_path)
        if not in_edit_mode:
            msg = 'File is not locked!'
            color = 'white'
        else:
            if is_locked_by_me:
                msg = 'File locked by you!'
                color = 'green'
            else:
                msg = 'File locked by other user!'
                color = 'red'

        if show_message:
            tp.Dcc.show_message_in_viewport(msg=msg, color=color)

        if not in_edit_mode:
            return False

        return True

    def upload_working_version(self, file_path=None, skip_saving=False, notify=False, comment=None, force=False):
        """
        Uploads a new working version of the given file
        :param file_path: str
        :param skip_saving: bool
        :param notify: bool
        :param comment: str
        :param force: bool
        :return: bool
        """

        self._check_project()

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        file_path = self.fix_path(file_path)
        valid_path = self._check_file_path(file_path)
        if not valid_path:
            LOGGER.warning('File Path "{}" is not valid!'.format(valid_path))
            return False

        short_path = file_path.replace(artellapipe.AssetsMgr().get_assets_path(), '')[1:]

        if artellapipe.project.is_enterprise():
            current_version = artellalib.get_current_version(file_path)
            if current_version == -1:
                current_version = 0
            new_version = current_version + 1
        else:
            history = artellalib.get_file_history(file_path)
            file_versions = history.versions
            if not file_versions:
                current_version = -1
            else:
                current_version = 0
                for v in file_versions:
                    if int(v[0]) > current_version:
                        current_version = int(v[0])
            new_version = current_version + 1

        if comment:
            comment = str(comment)
        else:
            comment = qtutils.get_comment(
                text_message='Make New Version ({}) : {}'.format(
                    new_version, short_path), title='Comment', parent=tp.Dcc.get_main_window())

        if comment:
            artellalib.upload_new_asset_version(file_path=file_path, comment=comment, skip_saving=skip_saving)
            if notify:
                artellapipe.project.notify(
                    title='New Working Version',
                    msg='Version {} for file "{}" uploaded to Artella server successfully!'.format(
                        new_version, file_path))
            return True

        return False

    def _check_project(self):
        """
        Internal function that checks whether or not assets manager has a project set. If not an exception is raised
        """

        if not artellapipe.project:
            raise exceptions.ArtellaProjectUndefinedException('Artella Project is not defined!')

        return True

    def _check_file_path(self, file_path):
        """
        Returns whether given path is a valid project path or not
        :param file_path: str
        :return: str
        """

        if not file_path:
            file_path = tp.Dcc.scene_name()
            if not file_path:
                LOGGER.error('File {} is not a valid file project path!'.format(file_path))
                return False

        if not file_path.startswith(artellapipe.project.get_path()):
            LOGGER.error(
                'File "{}" is not a valid project path because it is not located in Project Folder!'.format(file_path))
            return

        if not os.path.isfile(file_path):
            LOGGER.error('File {} cannot be locked because it does not exists!'.format(file_path))
            return False

        return True

    def _format_path(self, format_string, path='', **kwargs):
        """
        Resolves the given string with the given path and keyword arguments
        :param format_string: str
        :param path: str
        :param kwargs: dict
        :return: str
        """

        LOGGER.debug('Format String: {}'.format(format_string))

        dirname, name, extension = path_utils.split_path(path)
        encoding = locale.getpreferredencoding()
        temp = tempfile.gettempdir()
        if temp:
            temp = temp.decode(encoding)

        username = osplatform.get_user().lower()
        if username:
            username = username.decode(encoding)

        local = os.getenv('APPDATA') or os.getenv('HOME')
        if local:
            local = local.decode(encoding)

        kwargs.update(os.environ)

        labels = {
            "name": name,
            "path": path,
            "user": username,
            "temp": temp,
            "local": local,
            "dirname": dirname,
            "extension": extension,
        }

        kwargs.update(labels)

        resolved_string = six.u(str(format_string)).format(**kwargs)

        LOGGER.debug('Resolved string: {}'.format(resolved_string))

        return path_utils.clean_path(resolved_string)

    def _register_file_classes(self):
        """
        Internal function that registers file classes
        """

        if not hasattr(artellapipe, 'project') or not artellapipe.project:
            LOGGER.warning('Impossible to register file classes because Artella project is not defined!')
            return False

        for file_type, file_info in self.config.get('files', default=dict()).items():
            full_file_class = file_info.get('class', None)
            if not full_file_class:
                LOGGER.warning('No class defined for File Type "{}". Skipping ...'.format(file_type))
                continue
            file_type_extensions = file_info.get('extensions', list())
            file_type_rule = file_info.get('rule', None)
            file_type_template = file_info.get('template', None)
            file_class_split = full_file_class.split('.')
            file_class = file_class_split[-1]
            file_module = '.'.join(file_class_split[:-1])
            LOGGER.info('Registering File: {}'.format(file_module))

            module_loader = loader.find_loader(file_module)
            if not module_loader:
                LOGGER.warning('Impossible to load File Module: {}'.format(file_module))
                continue

            class_found = None
            try:
                mod = importlib.import_module(module_loader.fullname)
            except Exception as exc:
                LOGGER.warning('Impossible to register file class: {} | {}'.format(module_loader.fullname, exc))
                continue

            for cname, obj in inspect.getmembers(mod, inspect.isclass):
                if cname == file_class:
                    class_found = obj
                    break

            if not class_found:
                LOGGER.warning('No File Class "{}" found in Module: "{}"'.format(file_class, file_module))
                continue

            obj.FILE_TYPE = file_type
            obj.FILE_EXTENSIONS = file_type_extensions
            obj.FILE_RULE = file_type_rule
            obj.FILE_TEMPLATE = file_type_template

            self.register_file_class(file_type, obj)

        return True

    def get_asset_file(self, file_type, extension=None):
        """
        Returns asset file object class linked to given file type for current project
        :param file_type: str
        :param extension: str
        :return: ArtellaAssetType
        """

        self._check_project()

        if not self.is_valid_file_type(file_type):
            return

        asset_file_class_found = None
        for asset_file_class in self.file_classes.values():
            if asset_file_class.FILE_TYPE == file_type:
                asset_file_class_found = asset_file_class
                break

        if not asset_file_class_found:
            LOGGER.warning('No Asset File Class found for file of type: "{}"'.format(file_type))
            return

        return asset_file_class_found

    def get_artella_url(self, file_path=None, open=False):
        """
        Opens URL path of the given path
        :param file_path: str
        :param open: bool
        """

        self._check_project()

        if not file_path:
            file_path = tp.Dcc.scene_name()
        if not file_path:
            return

        if os.path.isfile(file_path):
            file_path = os.path.dirname(file_path)

        relative_path = os.path.relpath(file_path, artellapipe.project.get_path())
        artella_url = '{}/{}'.format(artellapipe.project.get_artella_url(), relative_path)

        if open:
            webbrowser.open(artella_url)

        return artella_url
