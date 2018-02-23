#!/usr/bin/python
# -*- coding: utf-8 -*-

from vtrex.flows.trex_install_flow import TRexInstallFlow
from vtrex.flows.trex_configure_flow import TRexConfigureFlow
from cloudshell.traffic.trex.cli.trex_cli_handler import TRexCliHandler


class CiscoTRexConfigurationRunner(object):
    def __init__(self, cli, resource_address, username, password):
        self._cli = cli
        self.resource_address = resource_address
        self.username = username
        self.password = password

    @property
    def cli_handler(self):
        """ CLI Handler property """

        return TRexCliHandler(self._cli, self.resource_address, self.username, self.password)

    @property
    def install_trex_flow(self):
        return TRexInstallFlow(cli_handler=self.cli_handler)

    def install_trex(self, trex_package_url):
        """ """

        return self.install_trex_flow.execute_flow(trex_package_url=trex_package_url)

    @property
    def configure_trex_flow(self):
        return TRexConfigureFlow(cli_handler=self.cli_handler)

    def configure_trex(self, server_config):
        """ """

        return self.configure_trex_flow.execute_flow(server_config=server_config)
