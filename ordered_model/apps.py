from django.apps import AppConfig


class OrderedModelConfig(AppConfig):
    name = "ordered_model"
    label = "ordered_model"

    def ready(self):
        # This import has side effects
        # noinspection PyUnresolvedReferences
        from .signals import on_ordered_model_delete
