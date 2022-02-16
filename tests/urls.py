from django.urls import path, include
from django.contrib import admin

from tests.drf import router

admin.autodiscover()
admin.site.enable_nav_sidebar = False

urlpatterns = [path("admin/", admin.site.urls), path("api/", include(router.urls))]
