from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import tagging

from geopy import distance

from ..machinetags.models import MachineTaggedItem, add_machinetag


RESERVED_USERNAMES = set((
    # Trailing spaces are essential in these strings, or split() will be buggy
    'feed www help security porn manage smtp fuck pop manager api owner shit '
    'secure ftp discussion blog features test mail email administrator '
    'xmlrpc web xxx pop3 abuse atom complaints news information imap cunt rss '
    'info pr0n about forum admin weblog team feeds root about info news blog '
    'forum features discussion email abuse complaints map skills tags ajax '
    'comet poll polling thereyet filter search zoom machinetags search django '
    'people profiles profile person navigate nav browse manage static css img '
    'javascript js code flags flag country countries region place places '
    'photos owner maps upload geocode geocoding login logout openid openids '
    'recover lost signup reports report flickr upcoming mashups recent irc '
    'group groups bulletin bulletins messages message newsfeed events company '
    'companies active'
).split())


class CountryManager(models.Manager):
    def top_countries(self):
        return self.get_query_set().order_by('-num_people')


class Country(models.Model):
    # Longest len('South Georgia and the South Sandwich Islands') = 44
    name = models.CharField(_('Name'), max_length=50)
    iso_code = models.CharField(_('ISO code'), max_length=2, unique=True)
    iso_numeric = models.CharField(_('ISO numeric code'), max_length=3,
                                   unique=True)
    iso_alpha3 = models.CharField(_('ISO alpha-3'), max_length=3, unique=True)
    fips_code = models.CharField(_('FIPS code'), max_length=2, unique=True)
    continent = models.CharField(_('Continent'), max_length=2)
    # Longest len('Grand Turk (Cockburn Town)') = 26
    capital = models.CharField(_('Capital'), max_length=30, blank=True)
    area_in_sq_km = models.FloatField(_('Area in square kilometers'))
    population = models.IntegerField(_('Population'))
    currency_code = models.CharField(_('Currency code'), max_length=3)
    # len('en-IN,hi,bn,te,mr,ta,ur,gu,ml,kn,or,pa,as,ks,sd,sa,ur-IN') = 56
    languages = models.CharField(_('Languages'), max_length=60)
    geoname_id = models.IntegerField(_('Geonames ID'))

    # Bounding boxes
    bbox_west = models.FloatField()
    bbox_north = models.FloatField()
    bbox_east = models.FloatField()
    bbox_south = models.FloatField()

    # De-normalised
    num_people = models.IntegerField(_('Number of people'), default=0)

    objects = CountryManager()

    def top_regions(self):
        # Returns populated regions in order of population
        regions = self.region_set.order_by('-num_people')
        return regions.select_related('country')

    class Meta:
        ordering = ('name',)
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

    def __unicode__(self):
        return u'%s' % self.name

    @property
    def flag_url(self):
        return 'djangopeople/img/flags/%s.gif' % self.iso_code.lower()


class Region(models.Model):
    code = models.CharField(_('Code'), max_length=20)
    name = models.CharField(_('Name'), max_length=50)
    country = models.ForeignKey(Country, verbose_name=_('Country'))
    flag = models.CharField(_('Flag'), max_length=100, blank=True)
    bbox_west = models.FloatField()
    bbox_north = models.FloatField()
    bbox_east = models.FloatField()
    bbox_south = models.FloatField()

    # De-normalised
    num_people = models.IntegerField(_('Number of people'), default=0)

    def get_absolute_url(self):
        return reverse('country_region', args=[self.country.iso_code.lower(),
                                               self.code.lower()])

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ('name',)
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')

    @property
    def flag_url(self):
        return 'djangopeople/%s' % self.flag

    @property
    def small_flag_url(self):
        return 'djangopeople/img/regions/%s/%s.png' % (
            self.country.iso_code.lower(),
            self.code.lower(),
        )


class DjangoPerson(models.Model):
    user = models.OneToOneField(User, verbose_name=_('User'))
    bio = models.TextField(_('Bio'), blank=True)

    # Location stuff - all location fields are required
    country = models.ForeignKey(Country, verbose_name=_('Country'))
    region = models.ForeignKey(Region, verbose_name=_('Region'), blank=True,
                               null=True)
    latitude = models.FloatField(_('Latitude'))
    longitude = models.FloatField(_('Longitude'))
    location_description = models.CharField(_('Location'), max_length=50)

    # Profile photo -- FIXME remove when we have migrations, now using gravatar
    photo = models.FileField(blank=True, upload_to='profiles')

    # Stats
    profile_views = models.IntegerField(_('Profile views'), default=0)

    # Machine tags
    machinetags = generic.GenericRelation(MachineTaggedItem)
    add_machinetag = add_machinetag

    # OpenID delegation
    openid_server = models.URLField(_('OpenID server'), max_length=255,
                                    blank=True)
    openid_delegate = models.URLField(_('OpenID delegate'), max_length=255,
                                      blank=True)

    # Last active on IRC
    last_active_on_irc = models.DateTimeField(_('Last active on IRC'),
                                              blank=True, null=True)

    @property
    def latitude_str(self):
        return str(self.latitude)

    @property
    def longitude_str(self):
        return str(self.longitude)

    def irc_nick(self):
        try:
            return self.machinetags.filter(namespace='im',
                                           predicate='django')[0].value
        except IndexError:
            return _('<none>')

    def get_nearest(self, num=5):
        "Returns the nearest X people, but only within the same continent"
        # TODO: Add caching

        people = list(self.country.djangoperson_set.select_related().exclude(
            pk=self.id,
        ))
        if len(people) <= num:
            # Not enough in country
            # use people from the same continent instead
            people = list(DjangoPerson.objects.filter(
                country__continent=self.country.continent,
            ).exclude(pk=self.id).select_related())

        # Sort and annotate people by distance
        for person in people:
            person.distance_in_miles = int(distance.VincentyDistance(
                (self.latitude, self.longitude),
                (person.latitude, person.longitude)
            ).miles)

        # Return the nearest X
        people.sort(key=lambda x: x.distance_in_miles)
        return people[:num]

    def location_description_html(self):
        region = ''
        if self.region:
            region = '<a href="%s">%s</a>' % (
                self.region.get_absolute_url(), self.region.name
            )
            bits = self.location_description.split(', ')
            if len(bits) > 1 and bits[-1] == self.region.name:
                bits[-1] = region
            else:
                bits.append(region)
                bits[:-1] = map(escape, bits[:-1])
            return mark_safe(', '.join(bits))
        else:
            return self.location_description

    def __unicode__(self):
        return u'%s' % self.user.get_full_name()

    def get_absolute_url(self):
        return reverse('user_profile', args=[self.user.username])

    # TODO: Put in transaction
    def save(self, force_insert=False, force_update=False, **kwargs):
        # Update country and region counters
        super(DjangoPerson, self).save(force_insert=False, force_update=False,
                                       **kwargs)
        self.country.num_people = self.country.djangoperson_set.count()
        self.country.save()
        if self.region:
            self.region.num_people = self.region.djangoperson_set.count()
            self.region.save()

    class Meta:
        verbose_name = _('Django person')
        verbose_name_plural = _('Django people')

    def irc_tracking_allowed(self):
        return not self.machinetags.filter(
            namespace='privacy', predicate='irctrack', value='private',
        ).count()

tagging.register(DjangoPerson, tag_descriptor_attr='skilltags',
                 tagged_item_manager_attr='skilltagged')


class PortfolioSite(models.Model):
    title = models.CharField(_('Title'), max_length=100)
    url = models.URLField(_('URL'), max_length=255)
    contributor = models.ForeignKey(DjangoPerson,
                                    verbose_name=_('Contributor'))

    def __unicode__(self):
        return u'%s <%s>' % (self.title, self.url)

    class Meta:
        verbose_name = _('Portfolio site')
        verbose_name_plural = _('Portfolio sites')


class CountrySite(models.Model):
    "Community sites for various countries"
    title = models.CharField(_('Title'), max_length=100)
    url = models.URLField(_('URL'), max_length=255)
    country = models.ForeignKey(Country, verbose_name=_('Country'))

    def __unicode__(self):
        return u'%s <%s>' % (self.title, self.url)

    class Meta:
        verbose_name = _('Country site')
        verbose_name_plural = _('Country sites')

#class ClusteredPoint(models.Model):
#
#    """
#    Represents a clustered point on the map. Each cluster is at a lat/long,
#    is only for one zoom level, and has a number of people.
#    If it is only one person, it is also associated with a DjangoPerson ID.
#    """
#
#    latitude = models.FloatField()
#    longitude = models.FloatField()
#    zoom = models.IntegerField()
#    number = models.IntegerField()
#    djangoperson = models.ForeignKey(DjangoPerson, blank=True, null=True)
#
#    def __unicode__(self):
#        return "%s people at (%s,%s,z%s)" % (self.number, self.longitude,
#                                             self.latitude, self.zoom)
#
#    class Admin:
#        list_display = ("zoom", "latitude", "longitude", "number")
#        ordering = ("zoom",)
