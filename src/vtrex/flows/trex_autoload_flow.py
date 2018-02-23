#!/usr/bin/python
# -*- coding: utf-8 -*-

from vtrex.actions.trex_autoload_actions import TRexAutoloadActions


class TRexAutoloadFlow(object):

    def __init__(self, cli_handler):
        self._cli_handler = cli_handler

    def execute_flow(self):
        """ Execute flow which configure license server on BreakingPoint Controller """

        with self._cli_handler.get_cli_service(self._cli_handler.enable_mode) as enable_session:
            autoload_actions = TRexAutoloadActions(enable_session)

            return autoload_actions.get_trex_ports()
