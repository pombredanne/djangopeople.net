from storages.backends.s3boto import S3BotoStorage
from django.contrib.staticfiles.storage import CachedFilesMixin


class S3HashedFilesStorage(CachedFilesMixin, S3BotoStorage):
    pass
