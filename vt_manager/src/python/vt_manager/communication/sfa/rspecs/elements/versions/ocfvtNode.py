from sfa.util.xrn import Xrn
from sfa.util.xml import XpathFilter

from sfa.rspecs.elements.node import Node
from sfa.rspecs.elements.sliver import Sliver
from sfa.rspecs.elements.location import Location
from vt_manager.communication.sfa.rspecs.elements.ocf_vt_server import OcfVtServer
from sfa.rspecs.elements.hardware_type import HardwareType
from sfa.rspecs.elements.disk_image import DiskImage
from sfa.rspecs.elements.interface import Interface
from sfa.rspecs.elements.bwlimit import BWlimit
from sfa.rspecs.elements.pltag import PLTag
from sfa.rspecs.elements.versions.pgv2Services import PGv2Services     
from sfa.rspecs.elements.versions.pgv2SliverType import PGv2SliverType     
from sfa.rspecs.elements.versions.pgv2Interface import PGv2Interface     


from vt_manager.communication.sfa.rspecs.elements.range import Range
from vt_manager.communication.sfa.rspecs.elements.network_interface import NetworkInterface

from sfa.planetlab.plxrn import xrn_to_hostname

class OcfVtNode:
    @staticmethod
    def add_nodes(xml, nodes):
        node_elems = []
        for node in nodes:
            node_fields = ['component_manager_id', 'component_id', 'client_id', 'sliver_id', 'exclusive']
            node_elem = xml.add_instance('node', node, node_fields)
            node_elems.append(node_elem)
            # set component name
            if node.get('component_id'):
                component_name = xrn_to_hostname(node['component_id'])
                node_elem.set('component_name', component_name)
            # set hardware types
            if node.get('hardware_types'):
                for hardware_type in node.get('hardware_types', []):
		    for field in OcfVtServer.fields:	
		        #node_elem.add_instance(field,{field:hardware_type[field]},[])#XXX Ugly notation
			simple_elem = node_elem.add_element(field)
			simple_elem.set_text(hardware_type[field])
            # set location
            if node.get('location'):
                node_elem.add_instance('location', node['location'], Location.fields)       
            # set interfaces
            PGv2Interface.add_interfaces(node_elem, node.get('interfaces'))
            #if node.get('interfaces'):
            #    for interface in  node.get('interfaces', []):
            #        node_elem.add_instance('interface', interface, ['component_id', 'client_id'])
            # set available element
            if node.get('boot_state'):
                if node.get('boot_state').lower() == 'boot':
                    available_elem = node_elem.add_element('available', now='true')
                else:
                    available_elem = node_elem.add_element('available', now='false')
            # add services
	    if node.get('services'):
		for service in node.get('services',[]):
		   fields = service.fields
		   s = node_elem.add_element('service', type=str(service.__class__.__name__))
		   for field in fields:
			if service[field]:
				simple_elem = s.add_element(field)#node_elem.add_element(field)
                        	simple_elem.set_text(service[field])
            #PGv2Services.add_services(node_elem, node.get('services', [])) 
            # add slivers
            slivers = node.get('slivers', [])
            if not slivers:
		pass
                # we must still advertise the available sliver types
                #slivers = Sliver({'type': 'plab-vserver'})
                # we must also advertise the available initscripts
                #slivers['tags'] = []
                #if node.get('pl_initscripts'): 
                #    for initscript in node.get('pl_initscripts', []):
                #        slivers['tags'].append({'name': 'initscript', 'value': initscript['name']})
            #PGv2SliverType.add_slivers(node_elem, slivers)
        return node_elems

    @staticmethod
    def get_nodes(xml, filter={}):
        xpath = '//node%s | //default:node%s' % (XpathFilter.xpath(filter), XpathFilter.xpath(filter))
        node_elems = xml.xpath(xpath)
        return OcfVtNode.get_node_objs(node_elems)

    @staticmethod
    def get_nodes_with_slivers(xml, filter={}):
        xpath = '//node[count(sliver_type)>0] | //default:node[count(default:sliver_type) > 0]' 
        node_elems = xml.xpath(xpath)        
        return OcfVtNode.get_node_objs(node_elems)

    @staticmethod
    def get_node_objs(node_elems):
        nodes = []
        for node_elem in node_elems:
            node = Node(node_elem.attrib, node_elem)
            nodes.append(node) 
            if 'component_id' in node_elem.attrib:
                node['authority_id'] = Xrn(node_elem.attrib['component_id']).get_authority_urn()
            
            # get hardware types
            hardware_type_elems = node_elem.xpath('./default:hardware_type | ./hardware_type')
            node['hardware_types'] = [hw_type.get_instance(HardwareType) for hw_type in hardware_type_elems]
            
            # get location
            location_elems = node_elem.xpath('./default:location | ./location')
            locations = [location_elem.get_instance(Location) for location_elem in location_elems]
            if len(locations) > 0:
                node['location'] = locations[0]

            # get interfaces
            iface_elems = node_elem.xpath('./default:interface | ./interface')
            node['interfaces'] = [iface_elem.get_instance(Interface) for iface_elem in iface_elems]

            # get services
            node['services'] = PGv2Services.get_services(node_elem)
            
            # get slivers
            node['slivers'] = PGv2SliverType.get_slivers(node_elem)    
            available_elems = node_elem.xpath('./default:available | ./available')
            if len(available_elems) > 0 and 'name' in available_elems[0].attrib:
                if available_elems[0].attrib.get('now', '').lower() == 'true': 
                    node['boot_state'] = 'boot'
                else: 
                    node['boot_state'] = 'disabled' 
        return nodes


    @staticmethod
    def add_slivers(xml, slivers):
        component_ids = []
        for sliver in slivers:
            filter = {}
            if isinstance(sliver, str):
                filter['component_id'] = '*%s*' % sliver
                sliver = {}
            elif 'component_id' in sliver and sliver['component_id']:
                filter['component_id'] = '*%s*' % sliver['component_id']
            if not filter: 
                continue
            nodes = OcfVtNode.get_nodes(xml, filter)
            if not nodes:
                continue
            node = nodes[0]
            PGv2SliverType.add_slivers(node, sliver)

    @staticmethod
    def remove_slivers(xml, hostnames):
        for hostname in hostnames:
            nodes = OcfVtNode.get_nodes(xml, {'component_id': '*%s*' % hostname})
            for node in nodes:
                slivers = OcfVtSliverType.get_slivers(node.element)
                for sliver in slivers:
                    node.element.remove(sliver.element) 
if __name__ == '__main__':
    from sfa.rspecs.rspec import RSpec
    #import pdb
    r = RSpec('/tmp/emulab.rspec')
    r2 = RSpec(version = 'OcfVt')
    nodes = OcfVtNode.get_nodes(r.xml)
    OcfVtNode.add_nodes(r2.xml.root, nodes)
    #pdb.set_trace()
        
                                    
