import json

from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from .models import Country, DjangoPerson
from ..machinetags.models import MachineTaggedItem


def irc_lookup(request, irc_nick):
    try:
        person = MachineTaggedItem.objects.get(
            namespace='im',
            predicate='django',
            value=irc_nick,
        ).content_object
    except MachineTaggedItem.DoesNotExist:
        return HttpResponse('no match', content_type='text/plain')
    scheme = 'https' if request.is_secure() else 'http'
    url = '%s://%s%s' % (scheme,
                         RequestSite(request).domain,
                         reverse('user_profile', args=[person.user.username]))
    return HttpResponse(
        u'%s, %s, %s, %s' % (person, person.location_description,
                             person.country, url),
        content_type='text/plain',
    )


def irc_redirect(request, irc_nick):
    try:
        person = MachineTaggedItem.objects.get(
            namespace='im',
            predicate='django',
            value=irc_nick,
        ).content_object
    except MachineTaggedItem.DoesNotExist:
        return HttpResponse('no match', content_type='text/plain')
    scheme = 'https' if request.is_secure() else 'http'
    url = '%s://%s%s' % (scheme, RequestSite(request).domain,
                         reverse('user_profile', args=[person.user.username]))
    return redirect(url)


def irc_spotted(request, irc_nick):
    if request.POST.get('sekrit', '') != settings.API_PASSWORD:
        return api_response('BAD_SEKRIT')

    try:
        person = MachineTaggedItem.objects.get(
            namespace='im', predicate='django', value=irc_nick
        ).content_object
    except MachineTaggedItem.DoesNotExist:
        return api_response('NO_MATCH')

    if not person.irc_tracking_allowed():
        return api_response('TRACKING_FORBIDDEN')

    first_time_seen = not person.last_active_on_irc

    person.last_active_on_irc = timezone.now()
    person.save()

    if first_time_seen:
        return api_response('FIRST_TIME_SEEN')
    else:
        return api_response('TRACKED')


def api_response(code):
    return HttpResponse(code, content_type='text/plain')


def stats(request):
    payload = {
        'people': DjangoPerson.objects.count(),
        'countries': Country.objects.filter(num_people__gt=0).count(),
    }
    return HttpResponse(json.dumps(payload),
                        content_type='application/json')
