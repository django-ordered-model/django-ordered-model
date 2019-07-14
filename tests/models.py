from django.db import models

from ordered_model.models import OrderedModel, OrderedModelBase


class Item(OrderedModel):
    name = models.CharField(max_length=100)


class Question(models.Model):
    pass


class TestUser(models.Model):
    pass


class Answer(OrderedModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(TestUser, on_delete=models.CASCADE, related_name="answers")
    order_with_respect_to = ("question", "user")

    class Meta:
        ordering = ("question", "user", "order")

    def __unicode__(self):
        return "Answer #{0:d} of question #{1:d} for user #{2:d}".format(
            self.order, self.question_id, self.user_id
        )


class CustomItem(OrderedModel):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    modified = models.DateTimeField(null=True, blank=True)


class CustomOrderFieldModel(OrderedModelBase):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)
    name = models.CharField(max_length=100)
    order_field_name = "sort_order"

    class Meta:
        ordering = ("sort_order",)


class Topping(models.Model):
    name = models.CharField(max_length=100)


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping, through="PizzaToppingsThroughModel")


class PizzaToppingsThroughModel(OrderedModel):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    order_with_respect_to = "pizza"

    class Meta:
        ordering = ("pizza", "order")


class BaseQuestion(OrderedModel):
    order_class_path = __module__ + ".BaseQuestion"
    question = models.TextField(max_length=100)

    class Meta:
        ordering = ("order",)


class MultipleChoiceQuestion(BaseQuestion):
    good_answer = models.TextField(max_length=100)
    wrong_answer1 = models.TextField(max_length=100)
    wrong_answer2 = models.TextField(max_length=100)
    wrong_answer3 = models.TextField(max_length=100)


class OpenQuestion(BaseQuestion):
    answer = models.TextField(max_length=100)


class ItemGroup(models.Model):
    user = models.ForeignKey(
        TestUser, on_delete=models.CASCADE, related_name="item_groups"
    )


class GroupedItem(OrderedModel):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE, related_name="items")
    order_with_respect_to = "group__user"
