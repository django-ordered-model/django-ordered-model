# Django < 1.3
DATABASE_ENGINE = 'sqlite3'
# Django >= 1.3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}
ROOT_URLCONF = 'ordered_model.tests.urls'
INSTALLED_APPS = [
    'ordered_model',
    'ordered_model.tests',
]
SECRET_KEY = 'topsecret'
