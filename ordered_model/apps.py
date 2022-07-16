from django.apps import AppConfig


class OrderedModelConfig(AppConfig):
    name = "ordered_model"
    label = "ordered_model"

    def ready(self):
        from . import signals
