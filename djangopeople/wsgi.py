from django.core.handlers.wsgi import WSGIHandler
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangopeople.settings")

application = WSGIHandler()
