import warnings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max, Min, F
from django.utils.translation import ugettext as _


class OrderedModel(models.Model):
    """
    An abstract model that allows objects to be ordered relative to each other.
    Provides an ``order`` field.
    """

    order = models.PositiveIntegerField(editable=False, db_index=True)
    order_with_respect_to = None

    class Meta:
        abstract = True
        ordering = ('order',)

    def _get_order_with_respect_to(self):
        return getattr(self, self.order_with_respect_to)

    def _valid_ordering_reference(self, reference):
        return self.order_with_respect_to is None or (
            self._get_order_with_respect_to() == reference._get_order_with_respect_to()
        )

    def get_ordering_queryset(self, qs=None):
        qs = qs or self.__class__.objects.all()
        order_with_respect_to = self.order_with_respect_to
        if order_with_respect_to:
            value = self._get_order_with_respect_to()
            qs = qs.filter((order_with_respect_to, value))
        return qs

    def save(self, *args, **kwargs):
        if self.order is None:
            c = self.get_ordering_queryset().aggregate(Max('order')).get('order__max')
            self.order = 0 if c is None else c + 1
        super(OrderedModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = self.get_ordering_queryset()
        qs.filter(order__gt=self.order).update(order=F('order')-1)
        super(OrderedModel, self).delete(*args, **kwargs)

    def _move(self, up, qs=None):
        qs = self.get_ordering_queryset(qs)

        if up:
            qs = qs.order_by('-order').filter(order__lt=self.order)
        else:
            qs = qs.filter(order__gt=self.order)
        try:
            replacement = qs[0]
        except IndexError:
            # already first/last
            return
        self.order, replacement.order = replacement.order, self.order
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
                "%r can only be swapped with instances of %r which %s equals %r." % (
                    self, self.__class__, self.order_with_respect_to,
                    self._get_order_with_respect_to()
                )
            )
        self.order, replacement.order = replacement.order, self.order
        self.save()
        replacement.save()

    def up(self):
        """
        Move this object up one position.
        """
        self.swap(self.get_ordering_queryset().filter(order__lt=self.order).order_by('-order'))

    def down(self):
        """
        Move this object down one position.
        """
        self.swap(self.get_ordering_queryset().filter(order__gt=self.order))

    def to(self, order):
        """
        Move object to a certain position, updating all affected objects to move accordingly up or down.
        """
        if order is None or self.order == order:
            # object is already at desired position
            return
        qs = self.get_ordering_queryset()
        if self.order > order:
            qs.filter(order__lt=self.order, order__gte=order).update(order=F('order') + 1)
        else:
            qs.filter(order__gt=self.order, order__lte=order).update(order=F('order') - 1)
        self.order = order
        self.save()

    def above(self, ref):
        """
        Move this object above the referenced object.
        """
        if not self._valid_ordering_reference(ref):
            raise ValueError(
                "%r can only be moved above instances of %r which %s equals %r." % (
                    self, self.__class__, self.order_with_respect_to,
                    self._get_order_with_respect_to()
                )
            )
        if self.order == ref.order:
            return
        if self.order > ref.order:
            o = ref.order
        else:
            o = self.get_ordering_queryset().filter(order__lt=ref.order).aggregate(Max('order')).get('order__max') or 0
        self.to(o)

    def below(self, ref):
        """
        Move this object below the referenced object.
        """
        if not self._valid_ordering_reference(ref):
            raise ValueError(
                "%r can only be moved below instances of %r which %s equals %r." % (
                    self, self.__class__, self.order_with_respect_to,
                    self._get_order_with_respect_to()
                )
            )
        if self.order == ref.order:
            return
        if self.order > ref.order:
            o = self.get_ordering_queryset().filter(order__gt=ref.order).aggregate(Min('order')).get('order__min') or 0
        else:
            o = ref.order
        self.to(o)

    def top(self):
        """
        Move this object to the top of the ordered stack.
        """
        o = self.get_ordering_queryset().aggregate(Min('order')).get('order__min')
        self.to(o)

    def bottom(self):
        """
        Move this object to the bottom of the ordered stack.
        """
        o = self.get_ordering_queryset().aggregate(Max('order')).get('order__max')
        self.to(o)
