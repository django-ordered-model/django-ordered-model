import warnings

from functools import reduce

from django.db import models
from django.db.models import Max, Min, F, signals
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


class OrderedModelMeta(models.base.ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        new_class = super().__new__(cls, name, bases, attrs, **kwargs)
        if new_class.order_with_respect_to is not None:
            if isinstance(new_class.order_with_respect_to, str):
                new_class.order_with_respect_to = (new_class.order_with_respect_to,)
            for wrt in new_class.order_with_respect_to:
                classes = wrt.split('__')
                if len(classes) == 1:
                    wrt_class = new_class
                else:
                    next_class = new_class
                    for field_name in classes[:-1]:
                        next_class = getattr(next_class, field_name).field.remote_field.model
                    wrt_class = next_class
                field_name = classes[-1]
                signals.pre_save.connect(cls.wrap_with_respect_to_change(new_class, wrt), weak=False, sender=wrt_class)

        return new_class

    @classmethod
    def wrap_with_respect_to_change(cls, new_class, wrt):
        def inner(*args, **kwargs):
            return new_class._with_respect_to_change(new_class, wrt, *args, **kwargs)

        return inner

class OrderedModelBase(models.Model, metaclass=OrderedModelMeta):
    """
    An abstract model that allows objects to be ordered relative to each other.
    Usage (See ``OrderedModel``):
     - create a model subclassing ``OrderedModelBase``
     - add an indexed ``PositiveIntegerField`` to the model
     - set ``order_field_name`` to the name of that field
     - use the same field name in ``Meta.ordering``
    [optional]
     - set ``order_with_respect_to`` to limit order to a subset
     - specify ``order_class_path`` in case of polymorpic classes
    """

    order_field_name = None
    order_with_respect_to = None
    order_class_path = None

    class Meta:
        abstract = True

    @classmethod
    def _with_respect_to_change(cls, for_model, wrt, sender, instance, raw, using, update_fields, **kwargs):
        if raw:
            return

        if instance._state.adding:
            return

        if update_fields is not None and 'field_name' not in update_fields:
            return

        fields = wrt.split('__')
        field_name = fields[-1]

        old_instance = sender.objects.get(pk=instance.pk)

        if getattr(instance, field_name) != getattr(old_instance, field_name):
            if sender == cls:
                c = instance.get_ordering_queryset().aggregate(
                    Max(instance.order_field_name)
                ).get(instance.order_field_name + '__max')
                setattr(instance, instance.order_field_name, 0 if c is None else c + 1)
            else:
                changing = for_model.objects.filter(**{'__'.join(fields[:-1]): instance})
                existing = for_model.objects.filter(**{wrt: getattr(instance, field_name)})
                max_existing = existing.aggregate(Max(for_model.order_field_name))[for_model.order_field_name + '__max']
                for to_reset in changing:
                    max_existing += 1
                    setattr(to_reset, for_model.order_field_name, max_existing)
                    to_reset.save()

    def _get_class_for_ordering_queryset(self):
        if self.order_class_path:
            return import_string(self.order_class_path)
        return self.__class__

    def _get_order_with_respect_to(self):
        if isinstance(self.order_with_respect_to, str):
            self.order_with_respect_to = (self.order_with_respect_to,)
        if self.order_with_respect_to is None:
            raise AssertionError(('ordered model admin "{0}" has not specified "order_with_respect_to"; note that this '
                'should go in the model body, and is not to be confused with the Meta property of the same name, '
                'which is independent Django functionality').format(self))

        def get_field_tuple(field):
            return (field, reduce(lambda i, f: getattr(i, f), field.split('__'), self))
        return list(map(get_field_tuple, self.order_with_respect_to))

    def _valid_ordering_reference(self, reference):
        return self.order_with_respect_to is None or (
            self._get_order_with_respect_to() == reference._get_order_with_respect_to()
        )

    def get_ordering_queryset(self, qs=None):
        qs = qs or self._get_class_for_ordering_queryset().objects.all()
        order_with_respect_to = self.order_with_respect_to
        if order_with_respect_to:
            order_values = self._get_order_with_respect_to()
            qs = qs.filter(**dict(order_values))
        return qs

    def previous(self):
        """
        Get previous element in this object's ordered stack.
        """
        return self.get_ordering_queryset().filter(
            **{self.order_field_name + '__lt': getattr(self, self.order_field_name)}
        ).order_by('-' + self.order_field_name).first()

    def next(self):
        """
        Get next element in this object's ordered stack.
        """
        return self.get_ordering_queryset().filter(
            **{self.order_field_name + '__gt': getattr(self, self.order_field_name)}
        ).first()

    def save(self, *args, **kwargs):
        if getattr(self, self.order_field_name) is None:
            c = self.get_ordering_queryset().aggregate(Max(self.order_field_name)).get(self.order_field_name + '__max')
            setattr(self, self.order_field_name, 0 if c is None else c + 1)
        super(OrderedModelBase, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = self.get_ordering_queryset()
        update_kwargs = {self.order_field_name: F(self.order_field_name) - 1}
        extra = kwargs.pop('extra_update', None)
        if extra:
            update_kwargs.update(extra) 
        qs.filter(**{self.order_field_name + '__gt': getattr(self, self.order_field_name)})\
          .update(**update_kwargs)
        super(OrderedModelBase, self).delete(*args, **kwargs)

    def swap(self, replacement):
        """
        Swap the position of this object with a replacement object.
        """
        if not self._valid_ordering_reference(replacement):
            raise ValueError(
                "{0!r} can only be swapped with instances of {1!r} with equal {2!s} fields.".format(
                    self, self._get_class_for_ordering_queryset(), ' and '.join(["'{}'".format(o[0]) for o in self._get_order_with_respect_to()])
                )
            )
        order, replacement_order = getattr(self, self.order_field_name), getattr(replacement, self.order_field_name)
        setattr(self, self.order_field_name, replacement_order)
        setattr(replacement, self.order_field_name, order)
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
            raise TypeError("Order value must be set using an 'int', not using a '{0}'.".format(type(order).__name__))

        if order is None or getattr(self, self.order_field_name) == order:
            # object is already at desired position
            return
        qs = self.get_ordering_queryset()
        if getattr(self, self.order_field_name) > order:
            update_kwargs = {self.order_field_name: F(self.order_field_name) + 1}
            if extra_update:
                update_kwargs.update(extra_update)
            qs.filter(**{self.order_field_name + '__lt': getattr(self, self.order_field_name),
                         self.order_field_name + '__gte': order})\
              .update(**update_kwargs)
        else:
            update_kwargs = {self.order_field_name: F(self.order_field_name) - 1}
            if extra_update:
                update_kwargs.update(extra_update)
            qs.filter(**{self.order_field_name + '__gt': getattr(self, self.order_field_name),
                         self.order_field_name + '__lte': order})\
              .update(**update_kwargs)
        setattr(self, self.order_field_name, order)
        self.save()

    def above(self, ref, extra_update=None):
        """
        Move this object above the referenced object.
        """
        if not self._valid_ordering_reference(ref):
            raise ValueError(
                "{0!r} can only be swapped with instances of {1!r} with equal {2!s} fields.".format(
                    self, self._get_class_for_ordering_queryset(), ' and '.join(["'{}'".format(o[0]) for o in self._get_order_with_respect_to()])
                )
            )
        if getattr(self, self.order_field_name) == getattr(ref, self.order_field_name):
            return
        if getattr(self, self.order_field_name) > getattr(ref, self.order_field_name):
            o = getattr(ref, self.order_field_name)
        else:
            o = self.get_ordering_queryset()\
                    .filter(**{self.order_field_name + '__lt': getattr(ref, self.order_field_name)})\
                    .aggregate(Max(self.order_field_name))\
                    .get(self.order_field_name + '__max') or 0
        self.to(o, extra_update=extra_update)

    def below(self, ref, extra_update=None):
        """
        Move this object below the referenced object.
        """
        if not self._valid_ordering_reference(ref):
            raise ValueError(
                "{0!r} can only be swapped with instances of {1!r} with equal {2!s} fields.".format(
                    self, self._get_class_for_ordering_queryset(), ' and '.join(["'{}'".format(o[0]) for o in self._get_order_with_respect_to()])
                )
            )
        if getattr(self, self.order_field_name) == getattr(ref, self.order_field_name):
            return
        if getattr(self, self.order_field_name) > getattr(ref, self.order_field_name):
            o = self.get_ordering_queryset()\
                    .filter(**{self.order_field_name + '__gt': getattr(ref, self.order_field_name)})\
                    .aggregate(Min(self.order_field_name))\
                    .get(self.order_field_name + '__min') or 0
        else:
            o = getattr(ref, self.order_field_name)
        self.to(o, extra_update=extra_update)

    def top(self, extra_update=None):
        """
        Move this object to the top of the ordered stack.
        """
        o = self.get_ordering_queryset().aggregate(Min(self.order_field_name)).get(self.order_field_name + '__min')
        self.to(o, extra_update=extra_update)

    def bottom(self, extra_update=None):
        """
        Move this object to the bottom of the ordered stack.
        """
        o = self.get_ordering_queryset().aggregate(Max(self.order_field_name)).get(self.order_field_name + '__max')
        self.to(o, extra_update=extra_update)


class OrderedModel(OrderedModelBase):
    """
    An abstract model that allows objects to be ordered relative to each other.
    Provides an ``order`` field.
    """

    order = models.PositiveIntegerField(_('order'), editable=False, db_index=True)
    order_field_name = 'order'

    class Meta:
        abstract = True
        ordering = ('order',)
