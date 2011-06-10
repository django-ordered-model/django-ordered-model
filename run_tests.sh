#!/bin/sh
PYTHONPATH=. DJANGO_SETTINGS_MODULE="ordered_model.tests.settings" django-admin.py test tests

