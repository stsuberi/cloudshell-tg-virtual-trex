#!/usr/bin/python
# -*- coding: utf-8 -*-

from vtrex.flows.trex_autoload_flow import TRexAutoloadFlow
from cloudshell.traffic.trex.cli.trex_cli_handler import TRexCliHandler


class CiscoTRexAutoloadRunner(object):
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
    def autoload_flow(self):
        return TRexAutoloadFlow(cli_handler=self.cli_handler)

    def trex_autoload_ports(self):
        """ """

        return self.autoload_flow.execute_flow()
