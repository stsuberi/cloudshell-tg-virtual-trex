#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate

CONFIG_ACTION_MAP = OrderedDict({"[\[\(][Yy]/[Nn][\)\]]|Press ENTER to confirm": lambda session, logger: session.send_line("", logger)})


CREATE_TREX_CONFIG = CommandTemplate("./dpdk_setup_ports.py -i", action_map=CONFIG_ACTION_MAP)
TREX_DAEMON_STATE = CommandTemplate("./trex_daemon_server {daemon_state}")
