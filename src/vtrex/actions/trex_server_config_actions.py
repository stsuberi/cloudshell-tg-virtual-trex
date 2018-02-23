#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
from cloudshell.traffic.trex.command_templates import trex_common

from vtrex.command_templates import trex_install
from vtrex.constants import TREX_ROOT_PATH, TREX_FOLDER, TREX_SERVER_CONFIG


class TRexServerConfigActions(object):
    def __init__(self, cli_service):
        """ Save and Restore device configuration actions

        :param cli_service: default mode cli_service
        """

        self._cli_service = cli_service

    def default_trex_config(self):
        """  """

        CommandTemplateExecutor(self._cli_service,
                                trex_common.CHANGE_PATH).execute_command(path="{}/{}".format(TREX_ROOT_PATH,
                                                                                             TREX_FOLDER))

        CommandTemplateExecutor(self._cli_service,
                                trex_install.TREX_DAEMON_STATE).execute_command(daemon_state="stop")

        output = CommandTemplateExecutor(cli_service=self._cli_service,
                                         command_template=trex_install.CREATE_TREX_CONFIG,
                                         expected_string=r"{prompt}|Enter list of interfaces separated by space".format(
                                             prompt=self._cli_service.command_mode.prompt)).execute_command()

        match = re.finditer(r"\|\s+(?P<id>\d+)\s+\|.*?\|.*?\|.*\|.*?\|.*?\|.*?\|(?P<state>.*)\s+\|", output,
                            re.IGNORECASE | re.MULTILINE)

        vinc_ids = [int(item.groupdict().get("id")) for item in match if
                    "active" not in item.groupdict().get("state").lower()]

        if len(vinc_ids) % 2 == 1:
            vinc_ids = sorted(vinc_ids)[:-1]

        self._cli_service.send_command(command=" ".join(map(str, vinc_ids)),
                                       action_map=trex_install.CONFIG_ACTION_MAP,
                                       check_action_loop_detector=False)

    def custom_trex_config(self, server_config_path):
        """  """

        CommandTemplateExecutor(self._cli_service, trex_common.CHANGE_PATH).execute_command(path="/etc")
        CommandTemplateExecutor(self._cli_service,
                                trex_common.DOWNLOAD_FILE).execute_command(file_name=TREX_SERVER_CONFIG,
                                                                           url=server_config_path)

    def start_trex_daemon(self):
        """  """

        CommandTemplateExecutor(self._cli_service,
                                trex_common.CHANGE_PATH).execute_command(path="{}/{}".format(TREX_ROOT_PATH,
                                                                                             TREX_FOLDER))

        CommandTemplateExecutor(self._cli_service,
                                trex_install.TREX_DAEMON_STATE).execute_command(daemon_state="start")
