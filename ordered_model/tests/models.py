from django.db import models
from ordered_model.models import OrderedModel


class Item(OrderedModel):
    name = models.CharField(max_length=100)


class Question(models.Model):
    pass


class User(models.Model):
    pass


class Answer(OrderedModel):
    question = models.ForeignKey(Question, related_name='answers')
    user = models.ForeignKey(User, related_name='answers')
    order_with_respect_to = ('question', 'user')

    class Meta:
        ordering = ('question', 'user', 'order')

    def __unicode__(self):
        return u"Answer #%d of question #%d for user #%d" % (self.order, self.question_id, self.user_id)


class CustomItem(OrderedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
