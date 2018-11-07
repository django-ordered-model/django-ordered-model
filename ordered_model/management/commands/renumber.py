#!/usr/bin/env python

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from django.apps import apps
from ordered_model.models import OrderedModel, OrderedModelBase
import importlib
import sys


class Command(BaseCommand):
    help = '''Reorder the numbering of an ordered model. `<app_name>` should \
be in the form `<app_label>.<model_name>`. '''

    def add_arguments(self, parser):
        parser.add_argument('<app_name>', nargs='+')

    def reorder_model(self, full_model_name):
        print('stdout is\n')

        (app_label, model_name) = full_model_name.rsplit('.', 1)
        ModelClass = apps.get_model(app_label=app_label, model_name=model_name)
        if not issubclass(ModelClass, OrderedModelBase):
            raise CommandError('Model %s is not an OrderedModel' % ModelClass.__name__)

        self.stdout.write("Reordering model %s" % (ModelClass))
        objects = ModelClass.objects.all().order_by('sort_order')
        for i, obj in enumerate(objects):
            old = obj.sort_order
            if not i == old:
                obj.sort_order = i
                obj.save()
                self.stdout.write("%d -> %d | %s" % (old, i, str(obj)[:30]))

    def handle(self, *args, **options):
        for model_name in args:
            self.reorder_model(model_name)
