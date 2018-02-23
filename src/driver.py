#!/usr/bin/python
# -*- coding: utf-8 -*-

import copy

from cloudshell.api.cloudshell_api import CloudShellAPISession, InputNameValue, SetConnectorRequest
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadCommandContext, \
    AutoLoadDetails, AutoLoadResource, AutoLoadAttribute
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from cloudshell.devices.driver_helper import get_cli, get_api

from vtrex.runners.trex_autoload_runner import CiscoTRexAutoloadRunner
from vtrex.runners.trex_configuration_runner import CiscoTRexConfigurationRunner

from constants import *
from utils.sandbox_msg import get_sandbox_msg

# noinspection PyAttributeOutsideInit
ATTR_LOGICAL_NAME = "Logical Name"
ATTR_REQUESTED_SOURCE_VNIC = "Requested Source vNIC Name"
ATTR_REQUESTED_TARGET_VNIC = "Requested Target vNIC Name"
MANAGEMENT_PORT = "TRex Management Port"
MODEL_PORT = "Virtual Port"
SSH_SESSION_POOL = 1


class CiscoVirtualTRexDriver(ResourceDriverInterface):
    def __init__(self):
        """ Constructor must be without arguments, it is created with reflection at run time """

        self.name = None
        self.model = None

    def initialize(self, context):
        """ Initialize the driver session, this function is called everytime a new instance of the driver is created
            This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """

        self.name = context.resource.name
        self.model = context.resource.model
        self._cli = get_cli(SSH_SESSION_POOL)

    def install_trex(self, context, resource_cache):

        is_update = context.resource.attributes["Update TRex"]

        if is_update == "True":

            api = get_api(context)

            trex_url = context.resource.attributes["TRex Package URL"]
            ip_address = context.resource.address
            username = context.resource.attributes["User"]
            password = api.DecryptPassword(context.resource.attributes["Password"]).Value

            configuration_operations = CiscoTRexConfigurationRunner(cli=self._cli,
                                                                    resource_address=ip_address,
                                                                    username=username,
                                                                    password=password)

            configuration_operations.install_trex(trex_package_url=trex_url)
            configuration_operations.configure_trex(server_config=context.resource.attributes["TRex Server Config"])

    def configure_device_command(self, context, resource_cache):
        """ Configure Virtual Chassis and Blades, create mapping between VChassis and VBlades
        :param ResourceCommandContext context: the context the command runs on
        :type resource_cache: str
        """

        self.install_trex(context, resource_cache)

    def get_inventory(self, context):
        """ Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        # See below some example code demonstrating how to return the resource structure
        # and attributes. In real life, of course, if the actual values are not static,
        # this code would be preceded by some SNMP/other calls to get the actual resource information

        ip_address = context.resource.address

        if not ip_address or ip_address == "NA":
            return AutoLoadDetails([], [])
        else:
            username = context.resource.attributes["User"]
            api = get_api(context)
            password = api.DecryptPassword(context.resource.attributes["Password"]).Value

            autoload_operations = CiscoTRexAutoloadRunner(cli=self._cli,
                                                          resource_address=ip_address,
                                                          username=username,
                                                          password=password)
            trex_ports = autoload_operations.trex_autoload_ports()

            resources = []
            attributes = []

            # Add TRex Management port
            attributes.append(AutoLoadAttribute("0", "Requested vNIC Name", "Network adapter 1"))
            resources.append(AutoLoadResource(model=MODEL_PORT, name=MANAGEMENT_PORT, relative_address="0"))

            # Add TRex test ports
            for i, uid in enumerate(trex_ports, start=1):
                address = str(i)
                attributes.append(AutoLoadAttribute(address,
                                                    "Requested vNIC Name",
                                                    "Network adapter {id}".format(id=str(i + 1))))
                # attributes.append(AutoLoadAttribute(address, "TRex Port UID", uid))
                attributes.append(AutoLoadAttribute(address, ATTR_LOGICAL_NAME, address))

                resources.append(AutoLoadResource(model=MODEL_PORT,
                                                  name="Port {}".format(address),
                                                  relative_address=address))
            return AutoLoadDetails(resources, attributes)

    def connect_child_resources(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :rtype: str
        """

        api = CloudShellAPISession(host=context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   domain="Global")
        resource_name = context.resource.fullname
        reservation_id = context.reservation.reservation_id
        connectors = context.connectors

        if not context.connectors:
            return "Success"

        resource = api.GetResourceDetails(resource_name)

        to_disconnect = []
        to_connect = []
        temp_connectors = []
        ports = self._get_ports(resource)

        for connector in connectors:
            me, other = self._set_remap_connector_details(connector, resource_name, temp_connectors)
            to_disconnect.extend([me, other])

        connectors = temp_connectors

        # these are connectors from app to vlan where user marked to which interface the connector should be connected
        connectors_with_predefined_target = [connector for connector in connectors if connector.vnic_id != ""]

        # these are connectors from app to vlan where user left the target interface unspecified
        connectors_without_target = [connector for connector in connectors if connector.vnic_id == ""]

        for connector in connectors_with_predefined_target:
            if connector.vnic_id not in ports.keys():
                raise Exception("Tried to connect an interface that is not on reservation - " + connector.vnic_id)

            else:
                if hasattr(ports[connector.vnic_id], "allocated"):
                    raise Exception(
                        "Tried to connect several connections to same interface: " + ports[connector.vnic_id])

                else:
                    to_connect.append(SetConnectorRequest(SourceResourceFullName=ports[connector.vnic_id].Name,
                                                          TargetResourceFullName=connector.other,
                                                          Direction=connector.direction,
                                                          Alias=connector.alias))
                    ports[connector.vnic_id].allocated = True

        unallocated_ports = [port for key, port in ports.items() if not hasattr(port, "allocated")]

        if len(unallocated_ports) < len(connectors_without_target):
            raise Exception("There were more connections to Cisco TRex than available interfaces after deployment.")
        else:
            for port in unallocated_ports:
                if connectors_without_target:
                    connector = connectors_without_target.pop()
                    to_connect.append(SetConnectorRequest(SourceResourceFullName=port.Name,
                                                          TargetResourceFullName=connector.other,
                                                          Direction=connector.direction,
                                                          Alias=connector.alias))

        if connectors_without_target:
            raise Exception("There were more connections to Cisco TRex than available interfaces after deployment.")

        api.RemoveConnectorsFromReservation(reservation_id, to_disconnect)
        api.SetConnectorsInReservation(reservation_id, to_connect)

        return "Success"

    @staticmethod
    def _set_remap_connector_details(connector, resource_name, connectors):
        attribs = connector.attributes
        if resource_name in connector.source.split("/"):
            remap_requests = attribs.get(ATTR_REQUESTED_SOURCE_VNIC, "").split(",")

            me = connector.source
            other = connector.target

            for vnic_id in remap_requests:
                new_con = copy.deepcopy(connector)
                CiscoVirtualTRexDriver._update_connector(new_con, me, other, vnic_id)
                connectors.append(new_con)

        elif resource_name in connector.target.split("/"):
            remap_requests = attribs.get(ATTR_REQUESTED_TARGET_VNIC, "").split(",")

            me = connector.target
            other = connector.source

            for vnic_id in remap_requests:
                new_con = copy.deepcopy(connector)
                CiscoVirtualTRexDriver._update_connector(new_con, me, other, vnic_id)
                connectors.append(new_con)
        else:
            raise Exception("Oops, a connector doesn't have required details:\n Connector source: {0}\n"
                            "Connector target: {1}\nPlease contact your admin".format(connector.source,
                                                                                      connector.target))

        return me, other

    @staticmethod
    def _update_connector(connector, me, other, vnic_id):
        connector.vnic_id = vnic_id
        connector.me = me
        connector.other = other

    @staticmethod
    def _get_ports(resource):
        ports = {str(idx): port for idx, port in enumerate(resource.ChildResources)
                 if port.ResourceModelName == MODEL_PORT}
        return ports

    def cleanup(self):
        """ Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """

        pass
