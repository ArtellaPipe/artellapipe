"""
Module that contains manager for Artella files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

import tpDccLib as tp
from tpPyUtils import python, decorators, path as path_utils
from tpQtLib.core import qtutils

import artellapipe
import artellapipe.register
from artellapipe.libs import artella as artella_lib
from artellapipe.libs.artella.core import artellalib
from artellapipe.utils import exceptions

LOGGER = logging.getLogger()


class ArtellaFilesManager(object):
    def __init__(self):
        self._project = None

    def set_project(self, project):
        """
        Sets the project this manager belongs to
        :param project: ArtellaProject
        """

        self._project = project

    def fix_path(self, path_to_fix):
        """
        Converts path to a path relative to project environment variable
        :param path_to_fix: str
        :return: str
        """

        self._check_project()

        project_env_var = self._project.env_var

        path_to_fix = path_to_fix.replace('\\', '/')
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

        return path_utils.clean_path(os.path.relpath(full_path, self._project.get_path()))

    def get_temp_path(self, *args):
        """
        Returns temporary folder path of the project
        :return: str
        """

        self._check_project()

        temp_path = '{temp}/' + self._project.get_clean_name() + '/pipeline/{user}'

        return path_utils.clean_path(os.path.join(self._format_path(temp_path), *args))

    def resolve_path(self, path_to_resolve):
        """
        Converts path to a valid full path
        :param path_to_resolve: str
        :return: str
        """

        path_to_resolve = path_to_resolve.replace('\\', '/')
        project_var = os.environ.get(self._project.env_var)
        if not project_var:
            return path_to_resolve

        if path_to_resolve.startswith(project_var):
            path_to_resolve = path_to_resolve.replace(project_var, '${}/'.format(self.env_var))

        return path_to_resolve

    def sync_files(self, files):
        """
        Synchronizes given files from Artella server into user hard drive
        :param files: list(str)
        """

        self._check_project()

        files = python.force_list(files)

        sync_dialog = artellapipe.SyncFileDialog(project=self._project, files=files)
        sync_dialog.sync()

    def sync_paths(self, paths):
        """
        Synchronizes given paths from Artella server into user hard drive
        :param paths: list(str)
        """

        self._check_project()

        paths = python.force_list(paths)

        sync_dialog = artellapipe.SyncPathDialog(project=self._project, paths=paths)
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
            self._project.tray.show_message(title='Lock File', msg='File locked successfully!')

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
            self.tray.show_message(title='Unlock File', msg='File unlocked successfully!')

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

        history = artellalib.get_file_history(file_path)
        file_versions = history.versions
        if not file_versions:
            current_version = -1
        else:
            current_version = 0
            for v in file_versions:
                if int(v[0]) > current_version:
                    current_version = int(v[0])
        current_version += 1

        if comment:
            comment = str(comment)
        else:
            comment = qtutils.get_comment(
                text_message='Make New Version ({}) : {}'.format(
                    current_version, short_path), title='Comment', parent=tp.Dcc.get_main_window())

        if comment:
            artellalib.upload_new_asset_version(file_path=file_path, comment=comment, skip_saving=skip_saving)
            if notify:
                self.tray.show_message(
                    title='New Working Version', msg='Version {} uploaded to Artella server successfully!'.format(
                        current_version))
            return True

        return False

    def _check_project(self):
        """
        Internal function that checks whether or not assets manager has a project set. If not an exception is raised
        """

        if not self._project:
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
                LOGGER.error('File {} cannot be locked because it does not exists!'.format(file_path))
                return False

        if not file_path.startswith(self._project.get_path()):
            LOGGER.error('Impossible to lock file that is nos located in {} Project Folder!'.format(self.name))
            return

        if not os.path.isfile(file_path):
            LOGGER.error('File {} cannot be locked because it does not exists!'.format(file_path))
            return False

        return True


@decorators.Singleton
class ArtellaFilesManagerSingleton(ArtellaFilesManager, object):
    def __init__(self):
        ArtellaFilesManager.__init__(self)


artellapipe.register.register_class('FilesMgr', ArtellaFilesManagerSingleton)
