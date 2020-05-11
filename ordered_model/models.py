from functools import partial, reduce

from django.db import models
from django.db.models import Max, Min, F
from django.db.models.constants import LOOKUP_SEP
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


def get_lookup_value(obj, field):
    return reduce(lambda i, f: getattr(i, f), field.split(LOOKUP_SEP), obj)


class OrderedModelQuerySet(models.QuerySet):
    def _get_order_field_name(self):
        return self.model.order_field_name

    def _get_order_field_lookup(self, lookup):
        order_field_name = self._get_order_field_name()
        return LOOKUP_SEP.join([order_field_name, lookup])

    def _get_order_with_respect_to(self):
        model = self.model
        order_with_respect_to = model.order_with_respect_to
        if isinstance(order_with_respect_to, str):
            order_with_respect_to = (order_with_respect_to,)
        if order_with_respect_to is None:
            raise AssertionError(
                (
                    'ordered model admin "{0}" has not specified "order_with_respect_to"; note that this '
                    "should go in the model body, and is not to be confused with the Meta property of the same name, "
                    "which is independent Django functionality"
                ).format(model)
            )
        return order_with_respect_to

    def get_max_order(self):
        order_field_name = self._get_order_field_name()
        return self.aggregate(Max(order_field_name)).get(
            self._get_order_field_lookup("max")
        )

    def get_min_order(self):
        order_field_name = self._get_order_field_name()
        return self.aggregate(Min(order_field_name)).get(
            self._get_order_field_lookup("min")
        )

    def get_next_order(self):
        order = self.get_max_order()
        return order + 1 if order is not None else 0

    def above(self, order, inclusive=False):
        """Filter items above order."""
        lookup = "gte" if inclusive else "gt"
        return self.filter(**{self._get_order_field_lookup(lookup): order})

    def above_instance(self, ref, inclusive=False):
        """Filter items above ref's order."""
        order_field_name = self._get_order_field_name()
        order = getattr(ref, order_field_name)
        return self.above(order, inclusive=inclusive)

    def below(self, order, inclusive=False):
        """Filter items below order."""
        lookup = "lte" if inclusive else "lt"
        return self.filter(**{self._get_order_field_lookup(lookup): order})

    def below_instance(self, ref, inclusive=False):
        """Filter items below ref's order."""
        order_field_name = self._get_order_field_name()
        order = getattr(ref, order_field_name)
        return self.below(order, inclusive=inclusive)

    def decrease_order(self, **extra_kwargs):
        """Decrease `order_field_name` value by 1."""
        order_field_name = self._get_order_field_name()
        update_kwargs = {order_field_name: F(order_field_name) - 1}
        if extra_kwargs:
            update_kwargs.update(extra_kwargs)
        return self.update(**update_kwargs)

    def increase_order(self, **extra_kwargs):
        """Increase `order_field_name` value by 1."""
        order_field_name = self._get_order_field_name()
        update_kwargs = {order_field_name: F(order_field_name) + 1}
        if extra_kwargs:
            update_kwargs.update(extra_kwargs)
        return self.update(**update_kwargs)

    def bulk_create(self, objs, batch_size=None):
        order_field_name = self._get_order_field_name()
        order_with_respect_to = self.model.order_with_respect_to
        objs = list(objs)
        if order_with_respect_to:
            order_with_respect_to_mapping = {}
            order_with_respect_to = self._get_order_with_respect_to()
            for obj in objs:
                key = tuple(
                    get_lookup_value(obj, field) for field in order_with_respect_to
                )
                if key in order_with_respect_to_mapping:
                    order_with_respect_to_mapping[key] += 1
                else:
                    order_with_respect_to_mapping[
                        key
                    ] = self.filter_by_order_with_respect_to(obj).get_next_order()
                setattr(obj, order_field_name, order_with_respect_to_mapping[key])
        else:
            for order, obj in enumerate(objs, self.get_next_order()):
                setattr(obj, order_field_name, order)
        return super().bulk_create(objs, batch_size=batch_size)

    def _get_order_with_respect_to_filter_kwargs(self, ref):
        order_with_respect_to = self._get_order_with_respect_to()
        _get_lookup_value = partial(get_lookup_value, ref)
        return {field: _get_lookup_value(field) for field in order_with_respect_to}

    _get_order_with_respect_to_filter_kwargs.queryset_only = False

    def filter_by_order_with_respect_to(self, ref):
        order_with_respect_to = self.model.order_with_respect_to
        if order_with_respect_to:
            filter_kwargs = self._get_order_with_respect_to_filter_kwargs(ref)
            return self.filter(**filter_kwargs)
        return self


class OrderedModelManager(models.Manager.from_queryset(OrderedModelQuerySet)):
    pass


class OrderedModelBase(models.Model):
    """
    An abstract model that allows objects to be ordered relative to each other.
    Usage (See ``OrderedModel``):
     - create a model subclassing ``OrderedModelBase``
     - add an indexed ``PositiveIntegerField`` to the model
     - set ``order_field_name`` to the name of that field
     - use the same field name in ``Meta.ordering``
    [optional]
     - set ``order_with_respect_to`` to limit order to a subset
     - specify ``order_class_path`` in case of polymorphic classes
    """

    objects = OrderedModelManager()

    order_field_name = None
    order_with_respect_to = None
    order_class_path = None

    class Meta:
        abstract = True

    def _validate_ordering_reference(self, ref):
        if self.order_with_respect_to is not None:
            self_kwargs = self._meta.default_manager._get_order_with_respect_to_filter_kwargs(self)
            ref_kwargs = ref._meta.default_manager._get_order_with_respect_to_filter_kwargs(ref)
            if self_kwargs != ref_kwargs:
                raise ValueError(
                    "{0!r} can only be swapped with instances of {1!r} with equal {2!s} fields.".format(
                        self,
                        self._meta.default_manager.model,
                        " and ".join(
                            [
                                "'{}'".format(o)
                                for o in self_kwargs
                            ]
                        ),
                    )
                )

    def get_ordering_queryset(self, qs=None):
        if qs is None:
            if self.order_class_path:
                model = import_string(self.order_class_path)
                qs = model._meta.default_manager.all()
            else:
                qs = self._meta.default_manager.all()
        return qs.filter_by_order_with_respect_to(self)

    def previous(self):
        """
        Get previous element in this object's ordered stack.
        """
        return self.get_ordering_queryset().below_instance(self).last()

    def next(self):
        """
        Get next element in this object's ordered stack.
        """
        return self.get_ordering_queryset().above_instance(self).first()

    def save(self, *args, **kwargs):
        order_field_name = self.order_field_name
        if getattr(self, order_field_name) is None:
            order = self.get_ordering_queryset().get_next_order()
            setattr(self, order_field_name, order)
        super().save(*args, **kwargs)

    def delete(self, *args, extra_update=None, **kwargs):
        qs = self.get_ordering_queryset()
        extra_update = {} if extra_update is None else extra_update
        qs.above_instance(self).decrease_order(**extra_update)
        super().delete(*args, **kwargs)

    def swap(self, replacement):
        """
        Swap the position of this object with a replacement object.
        """
        self._validate_ordering_reference(replacement)

        order_field_name = self.order_field_name
        order, replacement_order = (
            getattr(self, order_field_name),
            getattr(replacement, order_field_name),
        )
        setattr(self, order_field_name, replacement_order)
        setattr(replacement, order_field_name, order)
        self.save()
        replacement.save()

    def up(self):
        """
        Move this object up one position.
        """
        previous = self.previous()
        if previous:
            self.swap(previous)

    def down(self):
        """
        Move this object down one position.
        """
        _next = self.next()
        if _next:
            self.swap(_next)

    def to(self, order, extra_update=None):
        """
        Move object to a certain position, updating all affected objects to move accordingly up or down.
        """
        if not isinstance(order, int):
            raise TypeError(
                "Order value must be set using an 'int', not using a '{0}'.".format(
                    type(order).__name__
                )
            )

        order_field_name = self.order_field_name
        if order is None or getattr(self, order_field_name) == order:
            # object is already at desired position
            return
        qs = self.get_ordering_queryset()
        extra_update = {} if extra_update is None else extra_update
        if getattr(self, order_field_name) > order:
            qs.below_instance(self).above(order, inclusive=True).increase_order(
                **extra_update
            )
        else:
            qs.above_instance(self).below(order, inclusive=True).decrease_order(
                **extra_update
            )
        setattr(self, order_field_name, order)
        self.save()

    def above(self, ref, extra_update=None):
        """
        Move this object above the referenced object.
        """
        self._validate_ordering_reference(ref)
        order_field_name = self.order_field_name
        if getattr(self, order_field_name) == getattr(ref, order_field_name):
            return
        if getattr(self, order_field_name) > getattr(ref, order_field_name):
            o = getattr(ref, order_field_name)
        else:
            o = self.get_ordering_queryset().below_instance(ref).get_max_order() or 0
        self.to(o, extra_update=extra_update)

    def below(self, ref, extra_update=None):
        """
        Move this object below the referenced object.
        """
        self._validate_ordering_reference(ref)
        order_field_name = self.order_field_name
        if getattr(self, order_field_name) == getattr(ref, order_field_name):
            return
        if getattr(self, order_field_name) > getattr(ref, order_field_name):
            o = self.get_ordering_queryset().above_instance(ref).get_min_order() or 0
        else:
            o = getattr(ref, order_field_name)
        self.to(o, extra_update=extra_update)

    def top(self, extra_update=None):
        """
        Move this object to the top of the ordered stack.
        """
        o = self.get_ordering_queryset().get_min_order()
        self.to(o, extra_update=extra_update)

    def bottom(self, extra_update=None):
        """
        Move this object to the bottom of the ordered stack.
        """
        o = self.get_ordering_queryset().get_max_order()
        self.to(o, extra_update=extra_update)


class OrderedModel(OrderedModelBase):
    """
    An abstract model that allows objects to be ordered relative to each other.
    Provides an ``order`` field.
    """

    order = models.PositiveIntegerField(_("order"), editable=False, db_index=True)
    order_field_name = "order"

    class Meta:
        abstract = True
        ordering = ("order",)
