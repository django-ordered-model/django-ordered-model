from django.db import models
from ordered_model.models import OrderedModel

class Item(OrderedModel):
    name = models.CharField(max_length=100)


class ItemRight(models.Model):
    name = models.CharField(max_length=100)

class ItemLeft(models.Model):
    name = models.CharField(max_length=100)
    items_right = models.ManyToManyField(ItemRight, through='ItemsLeftRight')


class ItemsLeftRight(OrderedModel):
    item_left = models.ForeignKey(ItemLeft)
    item_right = models.ForeignKey(ItemRight)
    group_m2m_by = 'item_left'
