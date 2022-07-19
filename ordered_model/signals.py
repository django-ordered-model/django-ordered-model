import sys

from django.db.models.signals import pre_save
from django.db.models.constants import LOOKUP_SEP


def pre_save_ordered_model(sender, instance, update_fields=None, **kwargs):
    from ordered_model.models import OrderedModelBase

    if not issubclass(sender, OrderedModelBase):
        return
    order_field_name = sender.order_field_name
    order_with_respect_to = sender.get_order_with_respect_to()
    order_with_respect_to = [f.split(LOOKUP_SEP, 1)[0] for f in order_with_respect_to]
    if update_fields and not set(update_fields).intersection(
        order_with_respect_to + [order_field_name]
    ):
        return
    order = getattr(instance, order_field_name)
    order_with_respect_to_values = {
        field: getattr(instance, field) for field in order_with_respect_to
    }
    max_order = None
    if instance.pk:
        try:
            instance.refresh_from_db(fields=order_with_respect_to + [order_field_name])
            prev_order = getattr(instance, order_field_name)
            prev_order_with_respect_to_values = {
                field: getattr(instance, field) for field in order_with_respect_to
            }
        except instance.DoesNotExist:
            max_order = instance.get_ordering_queryset().get_next_order()
            prev_order = max_order
            prev_order_with_respect_to_values = order_with_respect_to_values
    else:
        max_order = instance.get_ordering_queryset().get_next_order()
        prev_order = max_order
        prev_order_with_respect_to_values = order_with_respect_to_values
    if prev_order_with_respect_to_values != order_with_respect_to_values:
        extra_update = instance._extra_update or {}
        instance.get_ordering_queryset().above_instance(instance).decrease_order(
            **extra_update
        )
        for k, v in order_with_respect_to_values.items():
            setattr(instance, k, v)
        prev_order = max_order = instance.get_ordering_queryset().get_next_order()
    if order != prev_order:
        if max_order is None:
            max_order = instance.get_ordering_queryset().get_max_order()
        if order is None or order > max_order:
            order = max_order
        setattr(instance, order_field_name, order)
        extra_update = instance._extra_update or {}
        qs = instance.get_ordering_queryset()
        if prev_order > order:
            qs.below(prev_order).above(order, inclusive=True).increase_order(
                **extra_update
            )
        elif prev_order < order:
            qs.above(prev_order).below(order, inclusive=True).decrease_order(
                **extra_update
            )
        instance._extra_update = None


if sys.version_info < (3, 6):
    pre_save.connect(pre_save_ordered_model, dispatch_uid="pre_save_ordered_model")
