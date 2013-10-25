from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max


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
        self._move(direction == 'up', qs)

    def move_down(self):
        """
        Move this object down one position.
        """
        return self._move(up=False)

    def move_up(self):
        """
        Move this object up one position.
        """
        return self._move(up=True)
