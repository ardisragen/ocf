import os
import sys
from os.path import dirname, join
from django.conf import *

#configobj
try:
        from configobj import ConfigObj
except:
        #FIXME: ugly
        os.system("apt-get update && apt-get install python-configobj -y")
        from configobj import ConfigObj


PYTHON_DIR = join(dirname(__file__), '../../../../../src/python')
sys.path.insert(0,PYTHON_DIR)

# This is needed because wsgi disallows using stdout
sys.stdout = sys.stderr

from expedient.clearinghouse.settings import *
#os.environ['DJANGO_SETTINGS_MODULE'] = 'expedient.clearinghouse.settings'
##os.environ['DJANGO_SETTINGS_MODULE'] = sys.argv[2]

from vt_plugin.models import resourcesHash
for rhash in resourcesHash.objects.all():
	rhash.delete()

