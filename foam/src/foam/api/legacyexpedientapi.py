#Vasileios: legacy ch_api of optin_manager. This worked with Expedient, 
#so we keep the function calls and modify the internal code
#in order to utilize FOAM functionality

#legacy django imports
'''
from expedient.common.rpc4django import rpcmethod
from django.contrib.auth.models import User
from decorator import decorator
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.models import Site
'''

import os
import sys

#legacy optin imports
#from foam.ethzlegacyoptinstuff.legacyoptin.xmlrpcmodels import CallBackServerProxy, FVServerProxy
from foam.ethzlegacyoptinstuff.legacyoptin.optsmodels import Experiment, ExperimentFLowSpace #,\
    #UserOpts, OptsFlowSpace, MatchStruct
from foam.ethzlegacyoptinstuff.legacyoptin.flowspaceutils import dotted_ip_to_int, mac_to_int,\
    int_to_dotted_ip, int_to_mac, parseFVexception

#foam general imports
import logging
import zlib
import base64
import xmlrpclib
from xml.parsers.expat import ExpatError
import jsonrpc
from flaskext.xmlrpc import XMLRPCHandler, Fault
from flask import request
import foam.task
import foam.lib
import foam.api.xmlrpc
import foam.version
from foam.creds import CredVerifier, Certificate
from foam.config import AUTO_SLIVER_PRIORITY, GAPI_REPORTFOAMVERSION
from foam.core.configdb import ConfigDB
from foam.core.log import KeyAdapter

#GENI API imports
from foam.geni.db import GeniDB, UnknownSlice, UnknownNode
import foam.geni.approval
import foam.geni.ofeliaapproval
import foam.geni.lib
import sfa

#FV import
from foam.flowvisor import Connection as FV

#my imports
from foam.app import admin_apih #admin is setup beforehand so handler is perfect for handling slices
#from foam.ethzlegacyoptinstuff.api_exp_to_rspecv3.expdatatogeniv3rspec import create_ofv3_rspec,\
#    extract_IP_mask_from_IP_range
#from foam.app import legexpgapi2_apih #use legexpgapi2 handler
from pprint import pprint
import json


def _same(val):
	return "%s" % val 

#legacy class as is
class om_ch_translate(object): 
  attr_funcs = {
    # attr_name: (func to turn to str, width)
    "dl_src": (int_to_mac, mac_to_int, 48, "mac_src","dl_src"),
    "dl_dst": (int_to_mac, mac_to_int, 48, "mac_dst","dl_dst"),
    "dl_type": (_same, int, 16, "eth_type","dl_type"),
    "vlan_id": (_same, int, 12, "vlan_id","dl_vlan"),
    "nw_src": (int_to_dotted_ip, dotted_ip_to_int, 32, "ip_src","nw_src"),
    "nw_dst": (int_to_dotted_ip, dotted_ip_to_int, 32, "ip_dst","nw_dst"),
    "nw_proto": (_same, int, 8, "ip_proto","nw_proto"),
    "tp_src": (_same, int, 16, "tp_src","tp_src"),
    "tp_dst": (_same, int, 16, "tp_dst","tp_dst"),
    "port_num": (_same, int, 16, "port_number","in_port"),
    }

from foam.ethzlegacyoptinstuff.api_exp_to_rspecv3.expdatatogeniv3rspec import *

class AMLegExpAPI(foam.api.xmlrpc.Dispatcher):
  def __init__ (self, log):
    super(AMLegExpAPI, self).__init__("legacyexpedientapi", log)
    self._actionLog = KeyAdapter("expedient", logging.getLogger('legexpapi-actions'))
    #retriev updated dict as a json file from foam db folder
    filedir = './opt/foam/db'
    filename = os.path.join(filedir, 'expedient_slices_info.json')
    if os.path.isfile(filename):
      f = open(filename, 'r')
      self.slice_info_dict = json.load(f)
      f.close()
    else:
      self.slice_info_dict = {}

  def recordAction (self, action, credentials = [], urn = None):
    cred_ids = []
    self._actionLog.info("Sliver: %s  LegExpAPI Action: %s" % (urn, action))
    for cred in credentials:
      self._actionLog.info("Credential: %s" % (cred))

  def priv_CreateSliver(self, slice_urn, credentials, rspec, users, force_approval=False, options=None):	
    #user_info = {}
    user_info = users
    try:
      #if CredVerifier.checkValid(credentials, "createsliver"):
      if True:
        self.recordAction("createsliver", credentials, slice_urn)
        try:
          #cert = Certificate(request.environ['CLIENT_RAW_CERT'])
          #user_info["urn"] = cert.getURN()
          #user_info["email"] = cert.getEmailAddress()
          self._log.debug("Parsed user cert with URN (%(urn)s) and email (%(email)s)" % users)
        except Exception, e:
          self._log.exception("UNFILTERED EXCEPTION")
          user_info["urn"] = None
          user_info["email"] = None
        sliver = foam.geni.lib.createSliver(slice_urn, credentials, rspec, user_info)
        style = ConfigDB.getConfigItemByKey("geni.approval.approve-on-creation").getValue()
        if style == foam.geni.approval.NEVER:
          approve = False
        elif style == foam.geni.approval.ALWAYS:
          approve = True
        else:
          approve = foam.geni.ofeliaapproval.of_analyzeForApproval(sliver)
        if approve or force_approval:
          pid = foam.task.approveSliver(sliver.getURN(), AUTO_SLIVER_PRIORITY)
          self._log.debug("task.py launched for approve-sliver (PID: %d)" % pid)	
        data = GeniDB.getSliverData(sliver.getURN(), True)
        foam.task.emailCreateSliver(data)
        return self.successResult(GeniDB.getManifest(sliver.getURN()))
      return
		
    except foam.geni.lib.RspecParseError, e:
      self._log.info(str(e))
      e._foam_logged = True
      raise e
    except foam.geni.lib.RspecValidationError, e:
      self._log.info(str(e))
      e._foam_logged = True
      raise e
    except foam.geni.lib.DuplicateSliver, ds:
      self._log.info("Attempt to create multiple slivers for slice [%s]" % (ds.slice_urn))
      ds._foam_logged = True
      raise ds
    except foam.geni.lib.UnknownComponentManagerID, ucm:
      raise Fault("UnknownComponentManager", "Component Manager ID specified in %s does not match this aggregate." % (ucm.cid))
    except (foam.geni.lib.UnmanagedComponent, UnknownNode), uc:
      self._log.info("Attempt to request unknown component %s" % (uc.cid))
      f = Fault("UnmanagedComponent", "DPID in component %s is unknown to this aggregate." % (uc.cid))
      f._foam_logged = True
      raise f
    except Exception, e:
      self._log.exception("Exception")
      raise e
		  
  def priv_DeleteSliver(self, slice_urn, credentials, options=None):
    try:
      #if CredVerifier.checkValid(credentials, "deletesliver", slice_urn):
      if True:
        self.recordAction("deletesliver", credentials, slice_urn)
        if GeniDB.getSliverURN(slice_urn) is None:
          raise Fault("DeleteSliver", "Sliver for slice URN (%s) does not exist" % (slice_urn))
          return self.errorResult(12, "") #not sure if this is needed
        sliver_urn = GeniDB.getSliverURN(slice_urn)
        data = GeniDB.getSliverData(sliver_urn, True)
        foam.geni.lib.deleteSliver(sliver_urn = sliver_urn)
        foam.task.emailGAPIDeleteSliver(data)
        return self.successResult(True)
      return self.successResult(False)
		
    except UnknownSlice, x:
      self._log.info("Attempt to delete unknown sliver for slice URN %s" % (slice_urn))
      x._foam_logged = True
      raise x 
    except Exception, e:
      self._log.exception("Exception")
      raise e


  #modified, checked
  #@decorator
  def pub_check_fv_set(self, func, *arg, **kwargs):
    if (FV.xmlconn is None):
      self._log.exception("No xlmlrpc connection with Flowvisor detected")
      raise Exception("No xlmlrpc connection with Flowvisor detected")
    #leave json com out for now    
    #if (FV.jsonconn is None):
    #  self._log.exception("No jsonrpc connection with FlowVisor detected")
    #  raise Exception("No jsonrpc connection with FlowVisor detected")
    return func(*arg, **kwargs)

  #as is
  #@decorator
  def pub_check_user(self, func, *args, **kwargs):
    '''
    #Check that the user is authenticated and known.
    
    if "request" not in kwargs:
      raise Exception("Request not available for XML-RPC %s" % \
                        func.func_name)
    meta = kwargs["request"].META
    if not hasattr(kwargs["request"], "user"):
      raise Exception("Authentication Middleware not installed in settings.")
    
    if not kwargs['request'].user.is_authenticated():
      raise Exception("User not authenticated for XML-RPC %s." % func.func_name)
    else:
      kwargs['user'] = kwargs['request'].user
      # Check that the user can actually make the xmlrpc call
      this_user = kwargs['user']
      if not this_user.get_profile().is_clearinghouse_user:
        raise Exception("Remote user %s is not a clearinghouse user" % (this_user.username))
    '''  
		#right now you can use foo creds for connection		
    if "request" not in kwargs:
      raise Exception("Request not available for XML-RPC %s" % \
                      func.func_name)  
    if not hasattr(kwargs["request"], "user"):
      raise Exception("Authentication Middleware not installed in settings.")
    kwargs['user'] = kwargs['request'].user
    
    return func(*args, **kwargs)

  #modified, checked
  #@check_user
  #@rpcmethod()
  def pub_checkFlowVisor(self, *arg, **kwargs):
    if (FV.xmlconn is None):
      self._log.exception("No xlmlrpc connection with Flowvisor detected")
      raise Exception("No xlmlrpc connection with Flowvisor detected")
    #leave json com out for now    
    #if (FV.jsonconn is None):
    #  self._log.exception("No jsonrpc connection with FlowVisor detected")
    #  raise Exception("No jsonrpc connection with FlowVisor detected")
    return ""

  #as is
  def pub_convert_star(self, fs):
    temp = fs.copy()
    for ch_name, (to_str, from_str, width, om_name, of_name) in \
    om_ch_translate.attr_funcs.items():
      ch_start = "%s_start" % ch_name
      ch_end = "%s_end" % ch_name
      if ch_start not in fs or fs[ch_start] == "*":
        temp[ch_start] = to_str(0)
      if ch_end not in fs or fs[ch_end] == "*":
        temp[ch_end] = to_str(2**width - 1)
    return temp

  #as is  
  def pub_convert_star_int(self, fs):
    temp = fs.copy()
    for ch_name, (to_str, from_str, width, om_name, of_name) in \
    om_ch_translate.attr_funcs.items():
      ch_start = "%s_start" % ch_name
      ch_end = "%s_end" % ch_name
      if ch_start not in fs or fs[ch_start] == "*":
        temp[ch_start] = 0
      else:
        temp[ch_start] = from_str(fs[ch_start])    
      if ch_end not in fs or fs[ch_end] == "*":
        temp[ch_end] = 2**width - 1
      else:
        temp[ch_end] = from_str(fs[ch_end])                    
    return temp

  #as is
  def pub_get_direction(self, direction):
    if (direction == 'ingress'):
      return 0
    if (direction == 'egress'):
      return 1
    if (direction == 'bidirectional'):
      return 2
    return 2
  
  def create_slice_fs(self, switch_slivers):
    #legacy create slice flowspaces
    all_efs = [] 
    for sliver in switch_slivers:
      if "datapath_id" in sliver:
        dpid = sliver['datapath_id']
      else:
        dpid = "00:" * 8
        dpid = dpid[:-1]
          
      if len(sliver['flowspace'])==0:
        efs = ExperimentFLowSpace()
        #efs.exp  = e
        efs.dpid = dpid
        efs.direction = 2
        all_efs.append(efs)
      else:
        for sfs in sliver['flowspace']:
          efs = ExperimentFLowSpace()
          #efs.exp  = e
          efs.dpid = dpid
          if "direction" in sfs:
              efs.direction = self.get_direction(sfs['direction'])
          else:
              efs.direction = 2       
          fs = self.pub_convert_star(sfs)
          for attr_name,(to_str, from_str, width, om_name, of_name) in \
          om_ch_translate.attr_funcs.items():
              ch_start ="%s_start"%(attr_name)
              ch_end ="%s_end"%(attr_name)
              om_start ="%s_s"%(om_name)
              om_end ="%s_e"%(om_name)
              setattr(efs,om_start,from_str(fs[ch_start]))
              setattr(efs,om_end,from_str(fs[ch_end]))
          all_efs.append(efs)
    return all_efs

  #coded from scratch, to be checked
  #@check_user
  #@check_fv_set
  #@rpcmethod(signature=['struct', # return value
  #                      'string', 'string', 'string',
  #                      'string', 'string', 'string',
  #                      'array', 'array'])
  def pub_create_slice(self, slice_id, project_name, project_description,
                    slice_name, slice_description, controller_url,
                    owner_email, owner_password,
                    switch_slivers, **kwargs):               
    '''
    Create an OpenFlow slice. 
    
    The C{switch_sliver} list contains a dict for each switch to be added to the
    slice's topology. Each such dict has the following items:
    
    - C{datapath_id}: the switch's datapath id
    - C{flowspace}: an array of dicts describing the switch's flowspace
    Each such dict has the following keys:
        - C{id}: integer. Per clearinghouse unique identifier for the rule.
        - C{port_num_start}, C{port_num_end}: string. the port range for this 
        flowspace
        - C{dl_src_start}, C{dl_src_end}: string. link layer address range in
        "xx:xx:xx:xx:xx:xx" format or '*' for wildcard
        - C{dl_dst_start}, C{dl_dst_end}: string. link layer address range in
        "xx:xx:xx:xx:xx:xx" format or '*' for wildcard
        - C{vlan_id_start}, C{vlan_id_end}: string. vlan id range or
        "*" for wildcard
        - C{nw_src_start}, C{nw_src_end}: string. network address range in 
        "x.x.x.x" format or '*' for wildcard
        - C{nw_dst_start}, C{nw_dst_end}: string. network address range in
        "x.x.x.x" format or '*' for wildcard
        - C{nw_proto_start}, C{nw_proto_end}: string. network protocol range or
        "*" for wildcard
        - C{tp_src_start}, C{tp_src_end}: string. transport port range or "*"
        for wildcard
        - C{tp_dst_start}, C{tp_dst_end}: string. transport port range or "*"
        for wildcard

    The call returns a dict with the following items:
    - C{error_msg}: a summary error message or "" if no errors occurred.
    - C{switches}: a list of dicts with the following items:
        - C{datapath_id}: id of the switch that caused the error
        - C{error}: optional error msg for the switch
        - all other fields of the C{switch_sliver} dicts mentioned above
        (port_num, direction, ...). The values for these items are the error
        messages associated with each field.

    @param slice_id: a string that uniquely identifies the slice at the 
        clearinghouse.
    @type slice_id: int
    
    @param project_name: a name for the project under which this slice 
        is created
    @type project_name: string
    
    @param project_description: text describing the project
    @type project_description: string
    
    @param slice_name: Name for the slice
    @type slice_name: string
    
    @param slice_description: text describing the slice/experiment
    @type slice_description: string
    
    @param controller_url: The URL for the slice's OpenFlow controller specified
        as <transport>:<hostname>[:<port>], where:
            - tranport is 'tcp' ('ssl' will be added later)
            - hostname is the controller's hostname
            - port is the port on which the controller listens to openflow
            messages (defaults to 6633).
    @type controller_url: string
    
    @param owner_email: email of the person responsible for the slice
    @type owner_email: string
    
    @param owner_password: initial password the user can use to login to the
        FlowVisor Web interface. Will need to be changed on initial login.
    @type owner_password: string
    
    @param switch_slivers: description of the topology and flowspace for slice
    @type switch_slivers: list of dicts
    
    @param kwargs: will contain additional useful information about the request.
        Of most use are the items in the C{kwargs['request'].META} dict. These
        include 'REMOTE_USER' which is the username of the user connecting or
        if using x509 certs then the domain name. Additionally, kwargs has the
        user using the 'user' key.
    
    @return: switches and links that have caused errors
    @rtype: dict
    '''
    
#    self._actionLog.info("Legacy Expedient API: create_slice got the following:")
#    self._actionLog.info("    slice_id: %s" % slice_id)
#    self._actionLog.info("    project_name: %s" % project_name)
#    self._actionLog.info("    project_desc: %s" % project_description)
#    self._actionLog.info("    slice_name: %s" % slice_name)
#    self._actionLog.info("    slice_desc: %s" % slice_description)
#    self._actionLog.info("    controller: %s" % controller_url)
#    self._actionLog.info("    owner_email: %s" % owner_email)
#    self._actionLog.info("    owner_pass: %s" % owner_password)
    #self._actionLog.info("    switch_slivers"
    #pprint(switch_slivers, indent=8)
    
    #legacy experiment creation (old database access)
    '''    
    e = Experiment.objects.filter(slice_id=slice_id)
    if (e.count()>0):
      old_e = e[0]
      old_fv_name = old_e.get_fv_slice_name()
      update_exp = True
      old_exp_fs = ExperimentFLowSpace.objects.filter(exp=old_e)
    else:
      update_exp = False  
    '''  
  
#    e = Experiment()
#    e.slice_id = slice_id
#    e.project_name = project_name
#    e.project_desc = project_description
#    e.slice_name = slice_name
#    e.slice_desc = slice_description
#    e.controller_url = controller_url
#    e.owner_email = owner_email
#    e.owner_password = owner_password
#    e.save()
    #update dict info
    self.slice_info_dict[slice_id] = {}
    self.slice_info_dict[slice_id]['project_name'] = project_name
    self.slice_info_dict[slice_id]['project_desc'] = project_description
    self.slice_info_dict[slice_id]['slice_name'] = slice_name
    self.slice_info_dict[slice_id]['slice_desc'] = slice_description
    self.slice_info_dict[slice_id]['controller_url'] = controller_url
    self.slice_info_dict[slice_id]['owner_email'] = owner_email
    self.slice_info_dict[slice_id]['owner_password'] = owner_password
    self.slice_info_dict[slice_id]['switch_slivers'] = switch_slivers 
   
    all_efs = self.create_slice_fs(switch_slivers)
    
    #set the necessary parameters so that we can use FOAM internal functions for sliver creation
    #Vasileios: now that the requested flowspaces are identified, create the rspec (to be used in FOAM)
    slice_of_rspec = create_ofv3_rspec(slice_id, project_name, project_description, \
                                      slice_name, slice_description, controller_url, \
                                      owner_email, owner_password, \
                                      switch_slivers, all_efs)
    self._log.info(slice_of_rspec) #print the rspec in the log for debugging

    #form the slice URN according to http://groups.geni.net/geni/wiki/GeniApiIdentifiers
    slice_urn = "urn:publicid:IDN+openflow:foam:fp7-ofelia.eu:ocf+slice+" + str(slice_id)
    creds = [] #creds are not needed at least for now: to be fixed
    user_info = {}
    user_info["urn"] = "urn:publicid:IDN+" + "openflow:fp7-ofelia.eu:ocf:ch+" + "user+" + str(owner_email) #temp hack
    user_info["email"] = str(owner_email)
    
    #now we have: slice_urn, creds, rspec and user_info : great!
    update_exp = True    
    #if GeniDB.getSliverURN(slice_urn) is None:
    if not GeniDB.sliceExists(slice_urn):
      update_exp = False    

    #moving on (now use gapi2 calls)
    if (update_exp):
      try:
        #old_exp_fs.delete()
        #old_e.delete()
        old_exp_shutdown_success = self.priv_DeleteSliver(slice_urn, creds, [])
      except Exception, e:
        import traceback
        traceback.print_exc()
        raise Exception("Exception while trying to shutdown old slice!")
      if old_exp_shutdown_success == False:
        raise Exception("Old slice could not be shutdown")
        
    #create new slice
    creation_result = self.priv_CreateSliver(slice_urn, creds, slice_of_rspec, user_info)
 
    #legacy save flowspace
    #for fs in all_efs:
    #  fs.save()     
    #self._log.info("Created slice with %s %s %s %s" % (
    #      e.get_fv_slice_name(), owner_password, controller_url, owner_email))
    #transaction.commit()
    
    #store updated dict as a json file in foam db folder
    filedir = './opt/foam/db'
    filename = os.path.join(filedir, 'expedient_slices_info.json')
    f = open(filename, 'w')
    json.dump(self.slice_info_dict, f)
    f.close()
    
    return {
          'error_msg': "",
          'switches': [],
      } 
    
  #coded from scratch, to be checked
  #@check_user
  #@check_fv_set
  #@rpcmethod(signature=['string', 'int'])
  def pub_delete_slice(self, slice_id, **kwargs):
    '''
    Delete the slice with id slice_id.
    
    @param slice_id: an int that uniquely identifies the slice at the 
        Clearinghouseclearinghouse.
    @type sliceid: int
    @param kwargs: will contain additional useful information about the request.
        Of most use are the items in the C{kwargs['request'].META} dict. These
        include 'REMOTE_USER' which is the username of the user connecting or
        if using x509 certs then the domain name.
    @return error message if there are any errors or "" otherwise.
    '''
    
    #legacy deletion (just for compatibility)
    '''  
    try:
      single_exp = Experiment.objects.get(slice_id = sliceid)
    except Experiment.DoesNotExist:
      return "Experiment Doesnot Exist"
    ofs = OptsFlowSpace.objects.filter(opt__experiment = single_exp)
    for fs in ofs:
      MatchStruct.objects.filter(optfs = fs).delete()
      # delete all flowspaces opted into this exp : not sure if this is still needed
      ofs.delete()
      UserOpts.objects.filter(experiment = single_exp).delete()
      ExperimentFLowSpace.objects.filter(exp = single_exp).delete()
      single_exp.delete()
    '''
    
    #FOAM deletion
    slice_urn = "urn:publicid:IDN+openflow:foam:fp7-ofelia.eu:ocf+slice+" + str(slice_id)
    creds = []
    deleted_slice_info = self.priv_DeleteSliver(slice_urn, creds, [])
    del self.slice_info_dict[slice_id]

    #store updated dict as a json file in foam db folder
    filedir = './opt/foam/db'
    filename = os.path.join(filedir, 'expedient_slices_info.json')
    f = open(filename, 'w')
    json.dump(self.slice_info_dict, f)
    f.close()
    
    return ""
  
  #@check_user
  #@rpcmethod(signature=['string', 'string', 'array'])
  def pub_change_slice_controller(self, slice_id, controller_url, **kwargs):
    '''
    Changes the slice controller url.
    '''
    if slice_id not in self.slice_info_dict:
      self._log.info("Slice is probably not started yet, doing nothing...")
      return ""
      #raise Exception("Something went wrong with the fs recovery")
    slice_of_rspec = create_ofv3_rspec(slice_id, self.slice_info_dict[slice_id]['project_name'], 
                                       self.slice_info_dict[slice_id]['project_desc'],
                                       self.slice_info_dict[slice_id]['slice_name'],
                                       self.slice_info_dict[slice_id]['slice_desc'], controller_url,
                                       self.slice_info_dict[slice_id]['owner_email'],
                                       self.slice_info_dict[slice_id]['owner_password'],
                                       self.slice_info_dict[slice_id]['switch_slivers'],
                                       self.create_slice_fs(self.slice_info_dict[slice_id]['switch_slivers']))
    self.slice_info_dict[slice_id]['controller_url'] = controller_url
    slice_urn = "urn:publicid:IDN+openflow:foam:fp7-ofelia.eu:ocf+slice+" + str(slice_id)
    creds = [] #creds are not needed at least for now: to be fixed
    user_info = {}
    user_info["urn"] = "urn:publicid:IDN+" + "openflow:fp7-ofelia.eu:ocf:ch+" + "user+" + str(self.slice_info_dict[slice_id]['owner_email']) #temp hack
    user_info["email"] = str(self.slice_info_dict[slice_id]['owner_email'])
    if GeniDB.sliceExists(slice_urn):
      sliv_urn = GeniDB.getSliverURN(slice_urn)
    else:
      raise Exception("Something went wrong with the fs recovery, slice does not exist!")
    sliver = GeniDB.getSliverObj(sliv_urn) 
    is_allocated_by_FV = GeniDB.getEnabled(sliv_urn)
    was_allocated_by_FV = is_allocated_by_FV
    try:
      #old_exp_shutdown_success = legexpgapi2_apih.pub_Shutdown(slice_urn, creds, [])
      old_exp_shutdown_success = self.priv_DeleteSliver(slice_urn, creds, [])
    except Exception, e:
      import traceback
      traceback.print_exc()
      raise Exception("Exception while trying to shutdown old slice!")
    if old_exp_shutdown_success == False:
      raise Exception("Old slice could not be shutdown")
    if was_allocated_by_FV == True:
      #create new slice and automatically approve since already approved (only controller changes)
      creation_result = self.priv_CreateSliver(slice_urn, creds, slice_of_rspec, user_info, True, None)
    else:
      creation_result = self.priv_CreateSliver(slice_urn, creds, slice_of_rspec, user_info, False, None)

    #store updated dict as a json file in foam db folder
    filedir = './opt/foam/db'
    filename = os.path.join(filedir, 'expedient_slices_info.json')
    f = open(filename, 'w')
    json.dump(self.slice_info_dict, f)
    f.close()
    
    return ""

  #modified, to be checked
  #@check_user
  #@check_fv_set
  #@rpcmethod(signature=['array'])
  def pub_get_switches(self, **kwargs):
    '''
    Return the switches that the FlowVisor gives. Change to CH format.
    '''
    complete_list = []
    try:
      dpids = FV.getDeviceList()
      for d in dpids:
        FV.log.debug("XMLRPC:getDeviceInfo (%s)" % (d))
      infos = [FV.xmlcall("getDeviceInfo", d) for d in dpids] #need to make it prettier :)
      switches = zip(dpids, infos)
    except Exception,e:
      import traceback
      traceback.print_exc()
      raise e 
    complete_list.extend(switches) 
    return complete_list
  
  #modified, to be checked
  #@check_user
  #@check_fv_set
  #@rpcmethod(signature=['array'])
  def pub_get_links(self, **kwargs):
    '''
    Return the links that the FlowVisor gives. Change to CH format.
    '''
    complete_list = []
    try:
      links = [(l.pop("srcDPID"),
                l.pop("srcPort"),
                l.pop("dstDPID"),
                l.pop("dstPort"),
                l) for l in FV.getLinkList()]
    except Exception,e:
      import traceback
      traceback.print_exc()
      raise e 
    complete_list.extend(links) 
    return complete_list

  #to be coded-----------------------------------------------------------------------  
  #@check_user
  #@rpcmethod(signature=['string', 'string', 'string'])
  def pub_register_topology_callback(self, url, cookie, **kwargs):
  #next step: see how this &*^&*$#@ information can be propagated to Expedient directly
  #we need the topology to be automatically updated (not only manually)
    '''  
    #legacy (Jose ETHZ code)  
    attrs = {'url': url, 'cookie': cookie}
    filter_attrs = {'username': kwargs['user'].username,'password':kwargs['password'].password}
    #filter_attrs = {'username': kwargs['user'].username}
    utils.create_or_update(CallBackServerProxy, filter_attrs, attrs)  
    '''  
    return ""


  #as is, probably needs changes because of DB refs  
  #@check_user
  #@rpcmethod(signature=['string', 'string'])
  def pub_change_password(self, new_password, **kwargs):
    '''
    Change the current password used for the clearinghouse to 'new_password'.
    
    @param new_password: the new password to use for authentication.
    @type new_password: random string of 1024 characters
    @param kwargs: will contain additional useful information about the request.
        Of most use are the items in the C{kwargs['request'].META} dict. These
        include 'REMOTE_USER' which is the username of the user connecting or
        if using x509 certs then the domain name.
    @return: Error message if there is any.
    @rtype: string
    '''
    
    #user = kwargs['user']
    #user.set_password(new_password)
    #user.save()
      
    return ""

  #modified, to be checked    
  #@check_user
  #@rpcmethod(signature=['string', 'string'])
  def pub_ping(self, data, **kwargs):
    if (FV.xmlconn is None):
      self._log.exception("No xlmlrpc connection with Flowvisor detected")
      raise Exception("No xlmlrpc connection with Flowvisor detected")
    try:
      FV.log.debug("XMLRPC:ping (%s)" % (str(data)))
      return FV.xmlcall("ping", " " + str(data)) #this will return a PONG is everything alright
    except Exception, e:
      import traceback
      traceback.print_exc()
      raise e

  #as is, to be checked    
  #@check_user
  #@check_fv_set
  #@rpcmethod()
  def pub_get_granted_flowspace(self, slice_id, **kwargs):
    '''
    Return FlowVisor Rules for the slice.
    '''
    def parse_granted_flowspaces(gfs):
      gfs_list=[] 
      for fs in gfs:
          fs_dict = dict(
              flowspace=dict(),
              openflow=dict()
          )
          fs_dict['openflow']=[]
          fs_dict['flowspace']=dict(
                                   mac_src_s=int_to_mac(fs.mac_src_s),
                                   mac_src_e=int_to_mac(fs.mac_src_e),
                                   mac_dst_s=int_to_mac(fs.mac_dst_s),
                                   mac_dst_e=int_to_mac(fs.mac_dst_e),
                                   eth_type_s=fs.eth_type_s,
                                   eth_type_e=fs.eth_type_e,
                                   vlan_id_s=fs.vlan_id_s,
                                   vlan_id_e=fs.vlan_id_e,
                                   ip_src_s=int_to_dotted_ip(fs.ip_src_s),
                                   ip_dst_s=int_to_dotted_ip(fs.ip_dst_s),
                                   ip_src_e=int_to_dotted_ip(fs.ip_src_e),
                                   ip_dst_e=int_to_dotted_ip(fs.ip_dst_e),
                                   ip_proto_s=fs.ip_proto_s,
                                   ip_proto_e=fs.ip_proto_e,
                                   tp_src_s=fs.tp_src_s,
                                   tp_dst_s=fs.tp_dst_s,
                                   tp_src_e=fs.tp_src_e,
                                   tp_dst_e=fs.tp_dst_e,
                               )
          openflow_dict=dict(
                                  dpid=fs.dpid, 
                                  direction=fs.direction, 
                                  port_number_s=fs.port_number_s, 
                                  port_number_e=fs.port_number_e, 
                             )
          existing_fs = False
          for prev_dict in gfs_list:
              if fs_dict['flowspace'] == prev_dict['flowspace']:
                  prev_dict['openflow'].append(openflow_dict)
                  existing_fs = True
                  break
          if not existing_fs:
              fs_dict['openflow'].append(openflow_dict) 
              gfs_list.append(fs_dict)
      
      return gfs_list

#    #legacy gfs parsing  
#    try:
#        exp = Experiment.objects.filter(slice_id = slice_id)
#        if exp and len(exp) == 1:
#            opts = exp[0].useropts_set.all()
#            if opts:
#                gfs = opts[0].optsflowspace_set.all()
#                gfs = parse_granted_flowspaces(gfs)
#            else:
#                gfs = []
#        else:
#            gfs = []			
#    except Exception,e:
#        import traceback
#        traceback.print_exc()
#        raise Exception(parseFVexception(e))

    slice_urn = "urn:publicid:IDN+openflow:foam:fp7-ofelia.eu:ocf+slice+" + str(slice_id)
    if GeniDB.sliceExists(slice_urn):
      sliv_urn = GeniDB.getSliverURN(slice_urn)
    else:
      return []
      #raise Exception(parseFVexception(e))
    sliver = GeniDB.getSliverObj(sliv_urn) 
    is_allocated_by_FV = GeniDB.getEnabled(sliv_urn)
    if is_allocated_by_FV == True:
      #that means that the flow space as requested was allocated
      #so retrieve the fs in the form Expedient understands
      #TODO: check that ecery time this corresponds to the actual flowspec that FOAM has
      if slice_id not in self.slice_info_dict:
        raise Exception("Something went wrong with the fs recovery")
      all_efs = self.create_slice_fs(self.slice_info_dict[slice_id]['switch_slivers']) 
      gfs = []    
      try:      
        gfs = parse_granted_flowspaces(all_efs)
      except Exception,e:
        import traceback
        traceback.print_exc()
        raise Exception(parseFVexception(e))
      return gfs
    else:
      return [] 
     

  #modified, to be checked
  #@check_user
  #@check_fv_set
  #@rpcmethod()
  def pub_get_offered_vlans(self, set=None):
    return admin_apih.adminOfferVlanTags(set, False)

  def pub_test_api_access(self, sayHello):
    if sayHello == 1:
      return "Hello"
    else:
      return "Bye"

  def successResult(self, value):
    code_dict = dict(geni_code=0)
    return dict(code=code_dict,
                value=value,
                output="")
          								
  def errorResult(self, code, output):
    code_dict = dict(geni_code=code)
    return dict(code=code_dict,
                value="",
                output=output)

#setup legacy API  
def setup (app):
  legexpapi = XMLRPCHandler('legacyexpedientapi')
  legexpapi.connect(app, '/core/legacyexpedientapi/xmlrpc/')
  #legexpapi = AMLegExpAPI(app)
  legexpapi.register_instance(AMLegExpAPI(app.logger))
  app.logger.info("[LegacyExpedientAPI] Loaded.")
  return legexpapi
