from django.db import models
from ordered_model.models import OrderedModel


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


class GroupedAnswer(OrderedModel):
    group = models.CharField(max_length=10, default='group1')
    question = models.ForeignKey(Question, related_name='grouped_answers')
    order_with_respect_to = ('question', 'group')

    class Meta:
        ordering = ('question', 'group', 'order')


class CustomItem(OrderedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
