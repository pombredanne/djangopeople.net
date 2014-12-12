# -*- coding: utf-8 -*-
"""Custom JSON-based session serializer to take care of OpenID."""

from __future__ import absolute_import

from djangopeople.django_openidconsumer.util import OpenID
import json
from openid.consumer.discover import OpenIDServiceEndpoint
from openid.yadis.manager import YadisServiceManager


class JSONEncoder(json.JSONEncoder):

    """JSON encoder that handles OpenID-related objects."""

    def default(self, o):
        if isinstance(o, YadisServiceManager):
            return dict([(k, v) for k, v in o.__dict__.iteritems()
                         if not k.startswith('_')],
                        __class__='YadisServiceManager')
        elif isinstance(o, OpenIDServiceEndpoint):
            return dict([(k, v) for k, v in o.__dict__.iteritems()
                         if k != 'openid_type_uris'],
                        __class__='OpenIDServiceEndpoint')
        elif isinstance(o, OpenID):
            data = dict([(k, v) for k, v in o.__dict__.iteritems()
                         if k not in ('is_iname', 'ax', 'sreg')],
                        __class__='OpenID')
            data['sreg_'] = o.sreg
            data['ax_'] = o.ax
            return data
        else:
            return super(JSONEncoder, self).default(o)


class JSONSerializer(object):

    """
    Session serializer based on ``django.core.signing.JSONSerializer``.

    Handles OpenID-related objects.
    """

    def __init__(self):
        self.encoder = JSONEncoder(separators=(',', ':'))

    def dumps(self, obj):
        return self.encoder.encode(obj).encode('latin-1')

    def loads(self, data):
        return json.loads(data.decode('latin-1'),
                          object_hook=self._object_hook)

    def _object_hook(self, d):
        cls_name = d.pop('__class__', None)
        if cls_name in ('OpenID', 'YadisServiceManager'):
            return globals()[cls_name](**d)
        elif cls_name == 'OpenIDServiceEndpoint':
            endpoint = OpenIDServiceEndpoint()
            for k, v in d.iteritems():
                setattr(endpoint, k, v)
            return endpoint
        return d
