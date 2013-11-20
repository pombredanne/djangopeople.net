import math
import json

from django.db.models import Q
from django.http import HttpResponse

from .models import DjangoPerson, ClusteredPoint
from ..clusterlizard.clusterer import Clusterer


def latlong_to_mercator(lat, long):
    x = long * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return x, y


def mercator_to_latlong(x, y):
    lon = (x / 20037508.34) * 180
    lat = (y / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(
        math.exp(lat * math.pi / 180)
    ) - math.pi / 2)
    return lat, lon


def input_generator():
    """
    The input to ClusterLizard should be a generator that yields
    (mx,my,id) tuples. This function reads them from the DjangoPeople models.
    """
    for person in DjangoPerson.objects.all():
        mx, my = latlong_to_mercator(person.latitude, person.longitude)
        yield (mx, my, person.id)


def save_clusters(clusters, zoom):
    """
    The output function provided to ClusterLizard should be a
    function that takes 'clusters', a set of clusters, and 'zoom',
    the integer Google zoom level.
    """
    for cluster in clusters:
        lat, long = mercator_to_latlong(*cluster.mean)
        ClusteredPoint.objects.create(
            latitude=lat,
            longitude=long,
            number=len(cluster),
            zoom=zoom,
            djangoperson_id=(len(cluster) == 1 and
                             list(cluster.points)[0][2] or None),
        )


def progress(done, left, took, zoom, eta):
    """
    You can also pass in an optional progress callback.
    """
    print "Iter %s (%s clusters) [%.3f secs] [zoom: %s] [ETA %s]" % (
        done, left, took, zoom, eta,
    )


def as_json(request, x2, y1, x1, y2, z):
    """
    View that returns clusters for the given zoom level as JSON.
    """
    x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))
    if y1 > y2:
        y1, y2 = y2, y1

    if x1 < x2:  # View not crossing the date line
        query = ClusteredPoint.objects.filter(latitude__gt=y1,
                                              latitude__lt=y2,
                                              longitude__gt=x1,
                                              longitude__lt=x2, zoom=z)
    else:  # View crossing the date line
        query = ClusteredPoint.objects.filter(
            Q(longitude__lt=x1) | Q(longitude__gt=x2,
                                    latitude__gt=y1,
                                    latitude__lt=y2),
            zoom=z)

    points = []
    for cluster in query:
        if cluster.djangoperson:
            points.append((cluster.longitude, cluster.latitude,
                           cluster.number,
                           cluster.djangoperson.get_absolute_url()))
        else:
            points.append((cluster.longitude, cluster.latitude,
                           cluster.number, None))
    return HttpResponse(json.dumps(points))


def run():
    """
    Runs the clustering, clearing the DB first.
    """
    ClusteredPoint.objects.all().delete()
    clusterer = Clusterer(
        input_generator(),
        save_clusters,
        progress,
    )
    clusterer.run()
