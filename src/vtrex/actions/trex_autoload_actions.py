#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor

from cloudshell.traffic.trex.command_templates import trex_autoload
from cloudshell.traffic.trex.command_templates import trex_common
from vtrex.constants import TREX_ROOT_PATH, TREX_FOLDER


class TRexAutoloadActions(object):
    def __init__(self, cli_service):
        """ Save and Restore device configuration actions

        :param cli_service: default mode cli_service
        """

        self._cli_service = cli_service

    def get_trex_ports(self):
        """ """

        CommandTemplateExecutor(self._cli_service,
                                trex_common.CHANGE_PATH).execute_command(
            path="{}/{}".format(TREX_ROOT_PATH, TREX_FOLDER))

        output = CommandTemplateExecutor(self._cli_service, trex_autoload.GET_AVAILABLE_PORTS).execute_command()

        if re.search(r"error|fail", output, re.IGNORECASE | re.DOTALL):
            raise Exception(self.__class__.__name__,
                            "Determining TRex ports count failed with error: {}".format(output))

        ports_list = re.finditer(r"^[0-9A-F]+:(?P<port_uid>[0-9A-F]+:[0-9A-F]+.[0-9A-F]+).*?(\*(?P<state>\w+)\*)*$",
                                 output,
                                 re.IGNORECASE | re.MULTILINE)

        test_ports = [port.groupdict().get("port_uid", None) for port in ports_list if
                      not port.groupdict().get("state", None)]

        # return len(re.findall(r"[0-9A-F]+:[0-9A-F]+:[0-9A-F]+.[0-9A-F]+", output, re.IGNORECASE | re.DOTALL))
        return test_ports
