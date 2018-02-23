#!/usr/bin/python
# -*- coding: utf-8 -*-

from vtrex.actions.trex_install_actions import TRexInstallActions


class TRexInstallFlow(object):

    def __init__(self, cli_handler):
        self._cli_handler = cli_handler

    def execute_flow(self, trex_package_url):
        """ Execute flow which configure license server on BreakingPoint Controller """

        with self._cli_handler.get_cli_service(self._cli_handler.enable_mode) as enable_session:
            install_actions = TRexInstallActions(enable_session)

            install_actions.download_trex_package(trex_url=trex_package_url)
            install_actions.unarchive_trex()
