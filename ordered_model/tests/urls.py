try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]
