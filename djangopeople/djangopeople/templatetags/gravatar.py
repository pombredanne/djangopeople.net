import hashlib
import urllib

from django import template

register = template.Library()


@register.simple_tag
def gravatar(email, size=48):
    """
    Generates an HTTPS gravatar link for a given email address.

    Usage (size is optional):

        {% gravatar email_var 24 %}
    """
    url = 'https://secure.gravatar.com/avatar/%s?%s' % (
        hashlib.md5(email).hexdigest(),
        urllib.urlencode({'s': str(size), 'd': 'mm'}),
    )
    return url
