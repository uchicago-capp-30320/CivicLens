from .settings import *  # noqa: F403, F404, F405


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_civiclens",
        "USER": DATABASE_USER,  # noqa: F405
        "PASSWORD": DATABASE_PASSWORD,  # noqa: F405
        "HOST": DATABASE_HOST,  # noqa: F405
        "PORT": DATABASE_PORT,  # noqa: F405
        "OPTIONS": {
            "sslmode": DATABASE_SSLMODE,  # noqa: F405
        },
    }
}
