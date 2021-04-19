from django.urls import path
from django.contrib import admin

admin.autodiscover()
admin.site.enable_nav_sidebar = False

urlpatterns = [path("admin/", admin.site.urls)]
