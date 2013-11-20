from django.core.management.base import NoArgsCommand

from ...models import Country, Region


class Command(NoArgsCommand):
    """
    Countries and regions keep a denormalized count of people that gets out of
    sync during syncdb.  This updates it.
    """
    def handle_noargs(self, **options):
        for qs in (Country.objects.all(), Region.objects.all()):
            for geo in qs:
                qs.model.objects.filter(pk=geo.pk).update(
                    num_people=geo.djangoperson_set.count(),
                )
