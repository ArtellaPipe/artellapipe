#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager for Slack functionality
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

import artellapipe


class SlackManager(object):
    def __init__(self):
        self._project = None

    def get_slack_token(self):
        """
        Returns slack token used by slack API
        :return: str
        """

        return os.environ.get('{}_SLACK_API_TOKEN'.format(artellapipe.project.get_clean_name().upper()), '')

    def get_slack_channel(self):
        """
        Returns slack channel messages wil lbe send
        :return: str
        """

        return os.environ.get('{}_SLACK_CHANNEL'.format(artellapipe.project.get_clean_name().upper()), '')

    def slack_is_available(self):
        """
        Returns whether slack is available or not
        :return: bool
        """

        return self.get_slack_token() and self.get_slack_channel()

    def get_slack_client(self):
        """
        Returns slack client of the current project
        :return: SlackClient
        """

        if not self.slack_is_available():
            return None

        from slackclient import SlackClient
        sc = SlackClient(self.get_slack_token())

        return sc

    def post_message(self, msg):
        """
        Post a message in the project channel
        :param msg:
        :return:
        """

        if not self.slack_is_available():
            return

        slack_client = self.get_slack_client()
        if not slack_client:
            return

        slack_client.api_call(
            'chat.postMessage',
            channel=self.get_slack_channel(),
            text=str(msg),
        )
