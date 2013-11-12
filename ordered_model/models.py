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

    class Meta:
        abstract = True
        ordering = ('order',)

    def save(self, *args, **kwargs):
        if not self.id:
            c = self.__class__.objects.all().aggregate(Max('order')).get('order__max')
            self.order = c and c + 1 or 0
        super(OrderedModel, self).save(*args, **kwargs)

    def _move(self, up, qs=None):
        if qs is None:
            qs = self.__class__._default_manager

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
        self.order, replacement.order = replacement.order, self.order
        self.save()
        replacement.save()

    def up(self):
        """
        Move this object up one position.
        """
        self.swap(self.__class__.objects.filter(order__lt=self.order).order_by('-order'))

    def down(self):
        """
        Move this object down one position.
        """
        self.swap(self.__class__.objects.filter(order__gt=self.order))

    def to(self, order):
        """
        Move object to a certain position, updating all affected objects to move accordingly up or down.
        """
        if order is None or self.order == order:
            # object is already at desired position
            return
        if self.order > order:
            m = self.__class__.objects.filter(order__lt=self.order, order__gte=order).update(order=F('order') + 1)
        else:
            m = self.__class__.objects.filter(order__gt=self.order, order__lte=order).update(order=F('order') - 1)
        self.order = order
        self.save()

    def above(self, ref):
        """
        Move this object above the referenced object.
        """
        if self.order == ref.order:
            return
        if self.order > ref.order:
            o = ref.order
        else:
            o = self.__class__.objects.filter(order__lt=ref.order).aggregate(Max('order')).get('order__max') or 0
        self.to(o)

    def below(self, ref):
        """
        Move this object below the referenced object.
        """
        if self.order == ref.order:
            return
        if self.order > ref.order:
            o = self.__class__.objects.filter(order__gt=ref.order).aggregate(Min('order')).get('order__min') or 0
        else:
            o = ref.order
        self.to(o)

    def top(self):
        """
        Move this object to the top of the ordered stack.
        """
        o = self.__class__.objects.all().aggregate(Min('order')).get('order__min')
        self.to(o)

    def bottom(self):
        """
        Move this object to the bottom of the ordered stack.
        """
        o = self.__class__.objects.all().aggregate(Max('order')).get('order__max')
        self.to(o)
