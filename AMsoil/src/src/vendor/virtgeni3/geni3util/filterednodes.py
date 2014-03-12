
#
# The tags of the nodes that will be excluded from the {advertisement, manifest} XML(s).
# This will be a dictionary of dictionaries, each entry for each XML.
# Each internal dictionary will be a dictionary of lists.
# Each internal dictionary key will consist on the parent node tag that will be filtered.
# The list assigned to each key will consist on the filtered tags of each node.
# The name of the filtered tags must be the same as the name of the model attributes.
#

#
# CONSTANTS
#

#
# Advertisement RSpec
#
# Server
SERVER_KEY = "server"
SERVER_ID = "id"
XEN_SERVER_ID = "vtserver_ptr_id"
SERVER_AGENT_URL = "agent_url"
SERVER_AGENT_PASSWORD = "agent_password"
SERVER_ENABLED = "enabled"
SERVER_URL = "url"
SERVER_VIRTUALMACHINES = "vms"
SERVER_VIRTUALMACHINES_ALLOCATED = "vms_allocated"
SERVER_VIRTUALIZATION_TECHNOLOGY = "virtualization_technology"
SERVER_OPERATING_SYSTEM_VERSION = "operating_system_version"
SERVER_OPERATING_SYSTEM_TYPE = "operating_system_type"
SERVER_OPERATING_SYSTEM_DISTRO = "operating_system_distribution"
#
# NetworkInterface
NETWORK_INTERFACE_KEY = "network_interface"
NETWORK_INTERFACE_ID = "id"
NETWORK_INTERFACE_ID_FORM = "id_form"
NETWORK_INTERFACE_IS_BRIDGE = "is_bridge"
NETWORK_INTERFACE_MAC_ID = "mac_id"
#
# MacRange
SUBSCRIBED_MAC_RANGE_KEY = "subscribed_mac_range"
SUBSCRIBED_MAC_RANGE_ID = "id"
SUBSCRIBED_MAC_RANGE_NUMBER_OF_SLOTS = "number_slots"
SUBSCRIBED_MAC_RANGE_IS_GLOBAL = "is_global"
SUBSCRIBED_MAC_RANGE_NEXT_AVAILABLE_MAC = "next_available_mac"
#
# Ip4Range
SUBSCRIBED_IP4_RANGE_KEY= "subscribed_ip4_range"
SUBSCRIBED_IP4_RANGE_ID = "id"
SUBSCRIBED_IP4_RANGE_NUMBER_OF_SLOTS = "number_slots"
SUBSCRIBED_IP4_RANGE_IS_GLOBAL = "is_global"
SUBSCRIBED_IP4_RANGE_NEXT_AVAILABLE_IP4 = "next_available_ip"
SUBSCRIBED_IP4_RANGE_NETMASK = "netmask"
SUBSCRIBED_IP4_RANGE_DNS1 = "dns1"
SUBSCRIBED_IP4_RANGE_DNS2 = "dns2"
SUBSCRIBED_IP4_RANGE_GATEWAY = "gw"
#
#
# Manifest RSpec
#
# ...

#
# LISTS
#

#
# Advertisement RSpec
#
ADVERTISEMENT_RSPEC_KEY = "advertisement"
#
# Server
SERVER_FILTERED_NODES = [
    SERVER_ID,
    XEN_SERVER_ID,
    SERVER_AGENT_URL,
    SERVER_AGENT_PASSWORD,
    SERVER_ENABLED,
    SERVER_URL,
    SERVER_VIRTUALMACHINES,
    SERVER_VIRTUALMACHINES_ALLOCATED,
    SERVER_VIRTUALIZATION_TECHNOLOGY,
    SERVER_OPERATING_SYSTEM_VERSION,
    SERVER_OPERATING_SYSTEM_TYPE,
    SERVER_OPERATING_SYSTEM_DISTRO
]
#
# NetworkInterface
NETWORK_INTERFACE_FILTERED_NODES = [
    NETWORK_INTERFACE_ID,
    NETWORK_INTERFACE_ID_FORM,
    NETWORK_INTERFACE_IS_BRIDGE,
    NETWORK_INTERFACE_MAC_ID
]
#
# MacRange
MAC_RANGE_FILTERED_NODES = [
    SUBSCRIBED_MAC_RANGE_ID,
    SUBSCRIBED_MAC_RANGE_NUMBER_OF_SLOTS,
    SUBSCRIBED_MAC_RANGE_IS_GLOBAL,
    SUBSCRIBED_MAC_RANGE_NEXT_AVAILABLE_MAC
]
#
# Ip4Range
IP4_RANGE_FILTERED_NODES = [
    SUBSCRIBED_IP4_RANGE_ID,
    SUBSCRIBED_IP4_RANGE_NUMBER_OF_SLOTS,
    SUBSCRIBED_IP4_RANGE_IS_GLOBAL,
    SUBSCRIBED_IP4_RANGE_NEXT_AVAILABLE_IP4,
    SUBSCRIBED_IP4_RANGE_NETMASK,
    SUBSCRIBED_IP4_RANGE_DNS1,
    SUBSCRIBED_IP4_RANGE_DNS2,
    SUBSCRIBED_IP4_RANGE_GATEWAY
]
#
#
# Manifest RSpec
#
MANIFEST_RSPEC_KEY = "manifest"
#
# ...

#
# DICTIONARIES
#

#
# Advertisement RSpec
#
ADVERTISEMENT_FILTERED_NODES = {
    SERVER_KEY : SERVER_FILTERED_NODES,
    NETWORK_INTERFACE_KEY : NETWORK_INTERFACE_FILTERED_NODES,
    SUBSCRIBED_MAC_RANGE_KEY : MAC_RANGE_FILTERED_NODES,
    SUBSCRIBED_IP4_RANGE_KEY : IP4_RANGE_FILTERED_NODES
}
#
# Manifest RSpec
#
# ...
#

#
# RSpecs dictionary.
# This is the global dictionary that must be imported.
# Contains all the information of the class in a dictionary of dictionaries.
#
RSPECS_FILTERED_NODES = {
    ADVERTISEMENT_RSPEC_KEY : ADVERTISEMENT_FILTERED_NODES
}   
