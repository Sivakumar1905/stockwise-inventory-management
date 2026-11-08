import tempfile

from .settings import *

_test_media = tempfile.TemporaryDirectory()
MEDIA_ROOT = _test_media.name

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]