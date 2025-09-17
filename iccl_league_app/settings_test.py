# settings_test.py

# Import everything from base settings
from .settings import *  # noqa: F403,F401

# Override database settings for testing to use a fast, in-memory SQLite database.
# This avoids relying on environment variables and connecting to a live PostgreSQL database.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Override any settings that might interfere with tests.

# Disable the Cloudinary storage to prevent test files from being uploaded
# and to avoid requiring Cloudinary credentials during the test run.
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CLOUDINARY_STORAGE = None

# Set DEBUG to True for testing to get more detailed error reports if needed.
DEBUG = True

# Disable third-party middleware that might not be needed for tests.
# This can sometimes speed up the test suite.
# You can remove 'tracking.middleware.VisitorTrackingMiddleware' if it's not essential.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

# Set a dummy secret key for testing, if a different one is needed.
# This is optional, as SECRET_KEY is often not critical for unit tests.
SECRET_KEY = "test-secret-key"

# Set up a dummy email backend to prevent tests from sending actual emails.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
