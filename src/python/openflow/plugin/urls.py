'''
@author: jnaous
'''
from django.conf.urls.defaults import patterns, url
from expedient.common.rpc4django.utils import rpc_url

urlpatterns = patterns('openflow.plugin.views',
#    url(r'^$', 'home', name='openflow_home'),
    url(r'^aggregate/create/$', 'aggregate_create', name='openflow_aggregate_create'),
    url(r'^aggregate/(?P<agg_id>\d+)/edit/$', 'aggregate_edit', name='openflow_aggregate_edit'),
    url(r'^aggregate/(?P<agg_id>\d+)/slice/(?P<slice_id>\d+)/add/$', 'aggregate_add_to_slice', name='openflow_aggregate_slice_add'),
    url(r'^aggregate/(?P<agg_id>\d+)/links/$', 'aggregate_add_links', name='openflow_aggregate_add_links'),
)

urlpatterns += patterns('',
    rpc_url(r'^gapi/$', name="openflow_gapi"),
    rpc_url(r'^xmlrpc/$', name="openflow_xmlrpc"),
    rpc_url(r'^open/xmlrpc/$', name="openflow_open_xmlrpc"),
)