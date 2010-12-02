'''
Created on Aug 2, 2010

@author: jnaous
'''
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

def get_aggregate_classes():
    """
    Get the list of modules that are the aggregate classes
    of aggregate plugins.
    """
    agg_plugins = getattr(settings, "AGGREGATE_PLUGINS", [])
    agg_plugin_names = [agg[0] for agg in agg_plugins]
    if hasattr(get_aggregate_classes, "l"):
        return get_aggregate_classes.l
    l = []
    for n in agg_plugin_names:
        mod, _, name = n.rpartition(".")
        mod = __import__(mod, fromlist=[name])
        l.append(getattr(mod, name))

    get_aggregate_classes.l = l
    return l

def get_aggregate_types():
    """
    Return the ContentType queryset of installed plugin aggregate models.
    """
    l = get_aggregate_classes()
    l = [ContentType.objects.get_for_model(m).id for m in l]
    return ContentType.objects.filter(id__in=l)