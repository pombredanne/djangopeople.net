import re
import urllib

from openid.consumer.consumer import (Consumer, SUCCESS, CANCEL, FAILURE,
                                      SETUP_NEEDED)
from openid.consumer.discover import DiscoveryFailure
from openid.yadis import xri

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from django.utils.translation import ugettext as _

from .middleware import OpenIDMiddleware
from .util import DjangoOpenIDStore, from_openid_response

NEXT_URL_RE = re.compile('^/[-\w/]+$')


def get_url_host(request):
    protocol = 'https' if request.is_secure() else 'http'
    host = escape(request.get_host())
    return '%s://%s' % (protocol, host)


def get_full_url(request):
    return get_url_host(request) + request.get_full_path()


def is_valid_next_url(next):
    # When we allow this:
    #   /openid/?next=/welcome/
    # For security reasons we want to restrict the next= bit to being a local
    # path, not a complete URL.
    return bool(NEXT_URL_RE.match(next))


def begin(request, sreg=None, extension_args=None,
          redirect_to=None, on_failure=None):
    on_failure = on_failure or default_on_failure

    if request.GET.get('logo'):
        # Makes for a better demo
        return logo(request)

    extension_args = extension_args or {}
    if sreg:
        extension_args['sreg.optional'] = sreg
    trust_root = getattr(
        settings, 'OPENID_TRUST_ROOT', get_url_host(request) + '/'
    )
    redirect_to = redirect_to or getattr(
        settings, 'OPENID_REDIRECT_TO',
        # If not explicitly set, assume current URL with complete/ appended
        get_full_url(request).split('?')[0] + 'complete/'
    )
    # In case they were lazy...
    if not redirect_to.startswith('http://'):
        redirect_to = get_url_host(request) + redirect_to

    if request.GET.get('next') and is_valid_next_url(request.GET['next']):
        if '?' in redirect_to:
            join = '&'
        else:
            join = '?'
        redirect_to += join + urllib.urlencode({
            'next': request.GET['next']
        })

    user_url = request.POST.get('openid_url', None)
    if not user_url:
        request_path = request.path
        if request.GET.get('next'):
            request_path += '?' + urllib.urlencode({
                'next': request.GET['next']
            })

        return render(request, 'openid_signin.html', {
            'action': request_path,
            'logo': request.path + '?logo=1',
        })

    if xri.identifierScheme(user_url) == 'XRI' and getattr(
        settings, 'OPENID_DISALLOW_INAMES', False
    ):
        return on_failure(request, _('i-names are not supported'))

    consumer = Consumer(request.session, DjangoOpenIDStore())
    try:
        auth_request = consumer.begin(user_url)
    except DiscoveryFailure:
        return on_failure(request, _("The OpenID was invalid"))

    # Add extension args (for things like simple registration)
    for name, value in extension_args.items():
        namespace, key = name.split('.', 1)
        auth_request.addExtensionArg(namespace, key, value)

    redirect_url = auth_request.redirectURL(trust_root, redirect_to)
    return redirect(redirect_url)


def complete(request, on_success=None, on_failure=None, return_to=None):
    on_success = on_success or default_on_success
    on_failure = on_failure or default_on_failure
    return_to = return_to or get_url_host(request) + reverse('openid_complete')

    consumer = Consumer(request.session, DjangoOpenIDStore())
    # JanRain library raises a warning if passed unicode objects as the keys,
    # so we convert to bytestrings before passing to the library
    query_dict = dict((k, smart_unicode(v)) for k, v in request.GET.items())
    openid_response = consumer.complete(query_dict, return_to)

    if openid_response.status == SUCCESS:
        return on_success(request, openid_response.identity_url,
                          openid_response)
    elif openid_response.status == CANCEL:
        return on_failure(request, _('The request was cancelled'))
    elif openid_response.status == FAILURE:
        return on_failure(request, openid_response.message)
    elif openid_response.status == SETUP_NEEDED:
        return on_failure(request, _('Setup needed'))
    else:
        assert False, "Bad openid status: %s" % openid_response.status


def default_on_success(request, identity_url, openid_response):
    if 'openids' not in request.session.keys():
        request.session['openids'] = []

    # Eliminate any duplicates
    request.session['openids'] = [
        o for o in request.session['openids'] if o.openid != identity_url
    ]
    request.session['openids'].append(from_openid_response(openid_response))

    # Set up request.openids and request.openid, reusing middleware logic
    OpenIDMiddleware().process_request(request)

    next = request.GET.get('next', '').strip()
    if not next or not is_valid_next_url(next):
        next = getattr(settings, 'OPENID_REDIRECT_NEXT', '/')

    return redirect(next)


def default_on_failure(request, message):
    return render(request, 'openid_failure.html', {
        'message': message
    })


def signout(request):
    request.session['openids'] = []
    next = request.GET.get('next', '/')
    if not is_valid_next_url(next):
        next = '/'
    return redirect(next)


def logo(request):
    return HttpResponse(
        OPENID_LOGO_BASE_64.decode('base64'), content_type='image/gif'
    )

# Logo from http://openid.net/login-bg.gif
# Embedded here for convenience; you should serve this as a static file
OPENID_LOGO_BASE_64 = """
R0lGODlhEAAQAMQAAO3t7eHh4srKyvz8/P5pDP9rENLS0v/28P/17tXV1dHEvPDw8M3Nzfn5+d3d
3f5jA97Syvnv6MfLzcfHx/1mCPx4Kc/S1Pf189C+tP+xgv/k1N3OxfHy9NLV1/39/f///yH5BAAA
AAAALAAAAAAQABAAAAVq4CeOZGme6KhlSDoexdO6H0IUR+otwUYRkMDCUwIYJhLFTyGZJACAwQcg
EAQ4kVuEE2AIGAOPQQAQwXCfS8KQGAwMjIYIUSi03B7iJ+AcnmclHg4TAh0QDzIpCw4WGBUZeikD
Fzk0lpcjIQA7
"""
