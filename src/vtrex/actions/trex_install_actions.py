#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor

from cloudshell.traffic.trex.command_templates import trex_common
from vtrex.constants import TREX_PACK_NAME, TREX_ROOT_PATH, TREX_FOLDER


class TRexInstallActions(object):
    def __init__(self, cli_service):
        """ Save and Restore device configuration actions

        :param cli_service: default mode cli_service
        """

        self._cli_service = cli_service

    def download_trex_package(self, trex_url):
        """  """

        CommandTemplateExecutor(self._cli_service, trex_common.MAKE_DIRECTORY).execute_command(path=TREX_ROOT_PATH)
        CommandTemplateExecutor(self._cli_service, trex_common.CHANGE_PATH).execute_command(path=TREX_ROOT_PATH)
        CommandTemplateExecutor(self._cli_service,
                                trex_common.DOWNLOAD_FILE).execute_command(file_name=TREX_PACK_NAME,
                                                                           url=trex_url)

    def unarchive_trex(self):
        """  """

        CommandTemplateExecutor(self._cli_service, trex_common.CHANGE_PATH).execute_command(path=TREX_ROOT_PATH)

        output = CommandTemplateExecutor(self._cli_service,
                                         trex_common.FILE_INFO).execute_command(file_path=TREX_PACK_NAME)

        if "gzip" in output.lower():
            command = trex_common.UNTAR_GZ_PACKAGE._command.format(trex_package=TREX_PACK_NAME)
        elif "tar" in output.lower():
            command = trex_common.UNTAR_PACKAGE._command.format(trex_package=TREX_PACK_NAME)
        # elif "Zip" in output:
        #     pass
        else:
            raise Exception(self.__class__.__name__, "Can't determine TRex Package format")

        output = self._cli_service.send_command(command=command,
                                                action_map=trex_common.UNTAR_PACKAGE._action_map,
                                                error_map=trex_common.UNTAR_PACKAGE._error_map,
                                                remove_command_from_output=False)

        if re.search(r"error|fail", output, re.IGNORECASE | re.DOTALL):
            raise Exception(self.__class__.__name__, "Un-tar TRex package failed : {}".format(output))

        trex_folder = ""
        for line in output.split("\n"):
            line = line.strip()
            if line and line != command:
                trex_folder = line
                break

        if not trex_folder:
            raise Exception(self.__class__.__name__, "Can't determine root TRex package folder")

        CommandTemplateExecutor(self._cli_service,
                                trex_common.CREATE_SIM_LINK).execute_command(source_path=trex_folder,
                                                                             link_name=TREX_FOLDER)
