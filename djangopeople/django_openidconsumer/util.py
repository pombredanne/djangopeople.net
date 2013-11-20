import base64
import hashlib
import operator
import time

import openid.store

from openid.association import Association as OIDAssociation
from openid.extensions import sreg, ax
from openid.store.interface import OpenIDStore
from openid.yadis import xri

from django.conf import settings
from django.db.models.query import Q

from .models import Association, NewNonce as Nonce


class OpenID(object):
    def __init__(self, openid, issued, attrs=None, sreg_=None, ax_=None):
        self.openid = openid
        self.issued = issued
        self.attrs = attrs or {}
        self.sreg = sreg_ or {}
        self.ax = ax_ or {}
        self.is_iname = (xri.identifierScheme(openid) == 'XRI')

    def __repr__(self):
        return '<OpenID: %s>' % self.openid

    def __str__(self):
        return self.openid


class DjangoOpenIDStore(OpenIDStore):
    def __init__(self):
        self.max_nonce_age = 6 * 60 * 60  # Six hours

    def storeAssociation(self, server_url, association):  # noqa
        Association.objects.create(
            server_url=server_url,
            handle=association.handle,
            secret=base64.encodestring(association.secret),
            issued=association.issued,
            lifetime=association.issued,
            assoc_type=association.assoc_type
        )

    def getAssociation(self, server_url, handle=None):  # noqa
        assocs = []
        if handle is not None:
            assocs = Association.objects.filter(
                server_url=server_url, handle=handle
            )
        else:
            assocs = Association.objects.filter(
                server_url=server_url
            )
        if not assocs:
            return None
        associations = []
        expired = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, base64.decodestring(assoc.secret), assoc.issued,
                assoc.lifetime, assoc.assoc_type
            )
            if association.getExpiresIn() == 0:
                expired.append(assoc)
            else:
                associations.append((association.issued, association))

        for assocc in expired:
            assoc.delete()

        if not associations:
            return None
        associations.sort()
        return associations[-1][1]

    def removeAssociation(self, server_url, handle):  # noqa
        assocs = list(Association.objects.filter(
            server_url=server_url, handle=handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist

    def storeNonce(self, nonce):  # noqa
        nonce, created = Nonce.objects.get_or_create(
            nonce=nonce, defaults={'expires': int(time.time())}
        )

    def useNonce(self, server_url, timestamp, salt):  # noqa
        if abs(timestamp - time.time()) > openid.store.nonce.SKEW:
            return False

        query = [
            Q(server_url__exact=server_url),
            Q(timestamp__exact=timestamp),
            Q(salt__exact=salt),
        ]
        try:
            Nonce.objects.get(reduce(operator.and_, query))
        except Nonce.DoesNotExist:
            Nonce.objects.create(
                server_url=server_url,
                timestamp=timestamp,
                salt=salt,
            )
            return True
        return False

    def getAuthKey(self):  # noqa
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        return hashlib.md5(settings.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]

    def isDumb(self):  # noqa
        return False


def from_openid_response(openid_response):
    issued = int(time.time())
    sreg_resp = sreg.SRegResponse.fromSuccessResponse(openid_response) or []
    ax_resp = ax.FetchResponse.fromSuccessResponse(openid_response)
    ax_args = {}
    if ax_resp is not None:
        ax_args = ax_resp.getExtensionArgs()
        ax_resp.parseExtensionArgs(ax_args)
        ax_args = ax_resp.data

    return OpenID(
        openid_response.identity_url, issued, openid_response.signed_fields,
        dict(sreg_resp), ax_args,
    )
