'''
@author: jnaous
'''
from django.conf.urls.defaults import *
from common.rpc4django.utils import rpc_url

urlpatterns = patterns("",
    rpc_url(r"^tests/RPC2/$", name="dummy_gopenflow"),
    url(r'^', include("urls")),
)