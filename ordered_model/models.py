import warnings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max, Min, F
from django.utils.translation import ugettext as _
import six


"""
Convert a string containing module.submodule.classname to a Class.
"""
def _order_model_get_class( classpath ):
    parts = classpath.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)           
    return m


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
     - specify ``order_class_path`` in case of polymorpic classes
    """

    order_field_name = None
    order_with_respect_to = None
    order_class_path = None

    class Meta:
        abstract = True


    def _get_class_for_ordering_queryset(self):
        if self.order_class_path:
            return _order_model_get_class(self.order_class_path)
        return self.__class__


    def _get_order_with_respect_to(self):
        if isinstance(self.order_with_respect_to, six.string_types):
            self.order_with_respect_to = (self.order_with_respect_to,)
        if self.order_with_respect_to is None:
            raise AssertionError(('ordered model admin "{0}" has not specified "order_with_respect_to"; note that this '
                'should go in the model body, and is not to be confused with the Meta property of the same name, '
                'which is independent Django functionality').format(self))
        return [(field, getattr(self, field)) for field in self.order_with_respect_to]

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

    def _move(self, up, qs=None):
        qs = self.get_ordering_queryset(qs)

        if up:
            qs = qs.order_by('-' + self.order_field_name)\
                   .filter(**{self.order_field_name + '__lt': getattr(self, self.order_field_name)})
        else:
            qs = qs.filter(**{self.order_field_name + '__gt': getattr(self, self.order_field_name)})
        try:
            replacement = qs[0]
        except IndexError:
            # already first/last
            return
        order, replacement_order = getattr(self, self.order_field_name), getattr(replacement, self.order_field_name)
        setattr(self, self.order_field_name, replacement_order)
        setattr(replacement, self.order_field_name, order)
        self.save()
        replacement.save()

    def move(self, direction, qs=None):
        warnings.warn(
            _("The method move() is deprecated and will be removed in the next release."),
            DeprecationWarning
        )
        if direction == 'up':
            self.up()
        else:
            self.down()

    def move_down(self):
        """
        Move this object down one position.
        """
        warnings.warn(
            _("The method move_down() is deprecated and will be removed in the next release. Please use down() instead!"),
            DeprecationWarning
        )
        return self.down()

    def move_up(self):
        """
        Move this object up one position.
        """
        warnings.warn(
            _("The method move_up() is deprecated and will be removed in the next release. Please use up() instead!"),
            DeprecationWarning
        )
        return self.up()

    def swap(self, qs):
        """
        Swap the positions of this object with a reference object.
        """
        try:
            replacement = qs[0]
        except IndexError:
            # already first/last
            return
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
        self.swap(self.get_ordering_queryset()
                      .filter(**{self.order_field_name + '__lt': getattr(self, self.order_field_name)})
                      .order_by('-' + self.order_field_name))

    def down(self):
        """
        Move this object down one position.
        """
        self.swap(self.get_ordering_queryset().filter(**{self.order_field_name + '__gt': getattr(self, self.order_field_name)}))

    def to(self, order, extra_update=None):
        """
        Move object to a certain position, updating all affected objects to move accordingly up or down.
        """
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

    order = models.PositiveIntegerField(editable=False, db_index=True)
    order_field_name = 'order'

    class Meta:
        abstract = True
        ordering = ('order',)
