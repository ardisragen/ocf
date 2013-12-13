import amsoil.core.pluginmanager as pm
#import utils.exceptions as virt_exception

'''@author: SergioVidiella'''

class VTAdminResourceManager(object):
    config = pm.getService("config")

    def __init__(self):
        super(VTAdminResourceManager, self).__init__()

    def get_server_projects(self, server_id):
	vmProjects = {}
	try:
            for vm in VTDriver.getVMsInServer(VTDriver.getServerById(server_id)):
            	if vm.xenvm.projectName not in vmProjects:
                    vmProjects[vm.xenvm.projectName] = vm.xenvm.projectId
	    return vmProjects
	#TODO: Improve Exception management
	except Exception as e:
	    print e
	    raise e

    def get_server_slices(self, server_id):
	vmSlices = {}
	try:
            for vm in VTDriver.getVMsInServer(VTDriver.getServerById(server_id)):
                if vm.xenvm.sliceName not in vmSlices:
                    vmSlices[vm.xenvm.sliceName] = vm.xenvm.sliceId
            return vmSlices
        #TODO: Improve Exception management
        except Exception as e:
            print e
            raise e

    def servers_crud(self, server_id, params):
	#XXX: add/update a server from the params
	pass

    def delete_server(self, server_id):
	try:
            VTDriver.deleteServer(VTDriver.getServerById(server_id))
            return True
	except Exception as e:
            print e
	    return False

    def action_vm(self, request, server_id, vm_id, action):
	#XXX: perform an action over the vm
	pass

    def subscribeEthernetRanges(request, server_id):
	pass

    def subscribeIp4Ranges(request, server_id):
	pass

    def manageEthernet(request,rangeId=None,action=None,macId=None):
	pass

    def manageIp4(request,rangeId=None,action=None,ip4Id=None):
	pass
