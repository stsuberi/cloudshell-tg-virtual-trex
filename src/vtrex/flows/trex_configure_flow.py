#!/usr/bin/python
# -*- coding: utf-8 -*-

from vtrex.actions.trex_server_config_actions import TRexServerConfigActions


class TRexConfigureFlow(object):

    def __init__(self, cli_handler):
        self._cli_handler = cli_handler

    def execute_flow(self, server_config):
        """ Execute flow which configure license server on BreakingPoint Controller """

        with self._cli_handler.get_cli_service(self._cli_handler.enable_mode) as enable_session:
            config_actions = TRexServerConfigActions(enable_session)

            if server_config:
                config_actions.custom_trex_config(server_config_path=server_config)
            else:
                config_actions.default_trex_config()

            config_actions.start_trex_daemon()
