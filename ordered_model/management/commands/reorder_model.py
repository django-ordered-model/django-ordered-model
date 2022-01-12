from django.apps import apps
from django.core.management import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from ordered_model.models import OrderedModelBase


def get_order_with_respect_to(model):
    if not model.order_with_respect_to:
        return None
    if isinstance(model.order_with_respect_to, str):
        return model.order_with_respect_to
    assert (
        len(model.order_with_respect_to) <= 1
    ), "re-ordering with more than 1 fields in order_with_respect_to is not supported"
    return model.order_with_respect_to[0]


class Command(BaseCommand):
    help = "Re-do the ordering of a certain Model"

    def add_arguments(self, parser):
        parser.add_argument("model_name", type=str, nargs="*")

    def handle(self, *args, **options):
        """
        Sometimes django-ordered-models ordering goes wrong, for various reasons,
        try re-ordering to a working state.
        """
        self.verbosity = options["verbosity"]
        orderedmodels = [
            m._meta.label for m in apps.get_models() if issubclass(m, OrderedModelBase)
        ]
        candidates = "\n   {}".format("\n   ".join(orderedmodels))
        if not options["model_name"]:
            return self.stdout.write("No model specified, try: {}".format(candidates))

        for model_name in options["model_name"]:
            if model_name not in orderedmodels:
                self.stdout.write(
                    "Model '{}' is not an ordered model, try: {}".format(
                        model_name, candidates
                    )
                )
                break
            model = apps.get_model(model_name)
            if not issubclass(model, OrderedModelBase):
                raise CommandError(
                    "{} does not inherit from OrderedModel or OrderedModelBase".format(
                        str(model)
                    )
                )

            self.reorder(model)

    def reorder(self, model):
        if model.order_with_respect_to:
            order_with_respect_to = get_order_with_respect_to(model)
            rel_kwargs = {"{}__isnull".format(order_with_respect_to): False}
            relation_to_list = (
                model.objects.order_by(order_with_respect_to)
                .values_list(order_with_respect_to, flat=True)
                .filter(**rel_kwargs)
                .distinct()
            )
            for relation_to in relation_to_list:
                kwargs = {order_with_respect_to: relation_to}
                self.reorder_queryset(model.objects.filter(**kwargs))
        else:
            self.reorder_queryset(model.objects.all())

    @transaction.atomic
    def reorder_queryset(self, queryset):
        model = queryset.model
        order_field_name = model.order_field_name

        for order, obj in enumerate(queryset):
            if getattr(obj, order_field_name) != order:
                if self.verbosity:
                    self.stdout.write(
                        "changing order of {} ({}) from {} to {}".format(
                            model._meta.label,
                            obj.pk,
                            getattr(obj, order_field_name),
                            order,
                        )
                    )
                setattr(obj, order_field_name, order)
                obj.save()
