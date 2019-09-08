import traceback

import artellapipe


class ArtellaPipeException(Exception):
    """
    Custom exception that raises Bug Tracker Tool for Artella
    """

    def __init__(self, project, msg=None):
        self._project = project
        if msg is None:
            msg = 'An error ocurred in Artella Project: {}'.format(project.name.title())
        self._show_bug_tracker(msg)
        super(ArtellaPipeException, self).__init__(msg)

    def _show_bug_tracker(self, msg):
        """
        Internal function that shows Bug Tracker with the error
        :param msg: str
        """

        from artellapipe.tools.bugtracker import bugtracker

        artellapipe.logger.error(msg)
        artellapipe.logger.error('{} | {}'.format(msg, traceback.format_exc()))
        bugtracker.ArtellaBugTracker.run(self._project, traceback.format_exc())
