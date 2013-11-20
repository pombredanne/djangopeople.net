import re

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.http import urlquote
from django.shortcuts import redirect

multislash_re = re.compile('/{2,}')


class NoDoubleSlashes:
    """
    123-reg redirects djangopeople.com/blah to djangopeople.net//blah - this
    middleware eliminates multiple slashes from incoming requests.
    """
    def process_request(self, request):
        if '//' in request.path:
            new_path = multislash_re.sub('/', request.path)
            return redirect(new_path)
        else:
            return None


class RemoveWWW(object):
    def process_request(self, request):
        host = request.get_host()
        if host and host.startswith('www.'):
            newurl = "%s://%s%s" % (request.is_secure() and 'https' or 'http',
                                    host[len('www.'):], request.path)
            if request.GET:
                newurl += '?' + request.GET.urlencode()
            return redirect(newurl, permaent=True)
        else:
            return None


class CanonicalDomainMiddleware(object):
    """
    Force-redirect to settings.CANONICAL_HOSTNAME if that's not the domain
    being accessed. If the setting isn't set, do nothing.
    """
    def __init__(self):
        try:
            self.canonical_hostname = settings.CANONICAL_HOSTNAME
        except AttributeError:
            raise MiddlewareNotUsed("settings.CANONICAL_HOSTNAME is undefined")

    def process_request(self, request):
        if request.get_host() == self.canonical_hostname:
            return

        # Domains didn't match, so do some fixups.
        new_url = [
            'https' if request.is_secure() else 'http',
            '://',
            self.canonical_hostname,
            urlquote(request.path),
            '?%s' % request.GET.urlencode() if request.GET else ''
        ]
        return redirect(''.join(new_url), permanent=True)
