DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}
ROOT_URLCONF = 'ordered_model.tests.urls'
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'ordered_model',
    'ordered_model.tests',
]
SECRET_KEY = 'topsecret'
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
