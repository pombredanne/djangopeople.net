from collections import defaultdict


def tagdict(queryset):
    """
    Returns a nested dictionary of machine tags,
    suitable for template languge.
    """
    d = defaultdict(lambda: defaultdict(lambda: ''))
    for mtag in queryset:
        d[mtag.namespace][mtag.predicate] = mtag.value
    return d
