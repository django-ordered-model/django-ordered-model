from django.db import models
from ordered_model.models import OrderedModel, OrderedModelBase


class Item(OrderedModel):
    name = models.CharField(max_length=100)


class Question(models.Model):
    pass


class Answer(OrderedModel):
    question = models.ForeignKey(Question, related_name='answers')
    order_with_respect_to = 'question'

    class Meta:
        ordering = ('question', 'order')

    def __unicode__(self):
        return u"Answer #%d of question #%d" % (self.order, self.question_id)


class CustomItem(OrderedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)


class CustomOrderFieldModel(OrderedModelBase):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)
    name = models.CharField(max_length=100)
    order_field_name = 'sort_order'

    class Meta:
        ordering = ('sort_order',)
