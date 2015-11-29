#!/usr/bin/env python

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from django.apps import apps
from ordered_model.models import OrderedModel
import importlib
import sys


class Command(BaseCommand):
    args = "<app_name>[:start_number] [<app_name>[:start_number] ...]"
    help = '''Reorder the numbering of an ordered model. `<app_name>` should \
be in the form `<app_label>.<model_name>`. An optional starting number can be \
added to the model name (e.g. `my_app.MyModel:1`). If a start number is given
then the model objects will be renumbered starting on that number.'''

    def is_number(self, s):
        try:
            return (len(str(int(s))) == len(s))
        except ValueError as ve:
            return False

    def reorder_model(self, full_model_name, start_number=0):
        (app_label, model_name) = full_model_name.split('.')
        ModelClass = apps.get_model(app_label=app_label, model_name=model_name)
        if (not issubclass(ModelClass, OrderedModel)):
            print("%s is not an OrderedModel", ModelClass.__name__)
            return
        print("Reordering model %s" % ModelClass)
        objects = ModelClass.objects.all().order_by('order')
        i = start_number
        for obj in objects:
            obj.order = i
            obj.save()
            i += 1
        for obj in objects:
            print("%d | %s" % (obj.order, str(obj)[:30]))

    def handle(self, *args, **options):
        start_number = 0
        model_name = None
        for arg in args:
            if (len(arg.split(':')) == 2):
                (model_name, start_number) = arg.split(':')
            else:
                model_name = arg
            self.reorder_model(model_name, int(start_number))
