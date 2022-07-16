def pre_save_ordered_model(sender, instance, **kwargs):
    order_field_name = sender.order_field_name
    order = getattr(instance, order_field_name)
    max_order = None
    if instance.pk:
        try:
            instance.refresh_from_db(fields=[order_field_name])
            prev_order = getattr(instance, order_field_name)
        except instance.DoesNotExist:
            max_order = instance.get_ordering_queryset().get_next_order()
            prev_order = max_order
    else:
        max_order = instance.get_ordering_queryset().get_next_order()
        prev_order = max_order
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
