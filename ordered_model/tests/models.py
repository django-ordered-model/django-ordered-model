from django.db import models
from ordered_model.models import OrderedModel, OrderedModelBase


class Item(OrderedModel):
    name = models.CharField(max_length=100)


class Question(models.Model):
    pass


class TestUser(models.Model):
    pass


class Answer(OrderedModel):
    question = models.ForeignKey(Question, related_name='answers')
    user = models.ForeignKey(TestUser, related_name='answers')
    order_with_respect_to = ('question', 'user')

    class Meta:
        ordering = ('question', 'user', 'order')

    def __unicode__(self):
        return u"Answer #%d of question #%d for user #%d" % (self.order, self.question_id, self.user_id)


class CustomItem(OrderedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)


class CustomOrderFieldModel(OrderedModelBase):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)
    name = models.CharField(max_length=100)
    order_field_name = 'sort_order'

    class Meta:
        ordering = ('sort_order',)


class Topping(models.Model):
    name = models.CharField(max_length=100)


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping, through='PizzaToppingsThroughModel')


class PizzaToppingsThroughModel(OrderedModel):
    pizza = models.ForeignKey(Pizza)
    topping = models.ForeignKey(Topping)
    order_with_respect_to = 'pizza'

    class Meta:
        ordering = ('pizza', 'order')
