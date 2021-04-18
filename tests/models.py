from django.db import models

from ordered_model.models import OrderedModel, OrderedModelBase


# test simple automatic ordering
class Item(OrderedModel):
    name = models.CharField(max_length=100)


# test Answer.order_with_respect_to being a tuple
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


# test ordering whilst overriding the automatic primary key (ie. not models.Model.id)
class CustomItem(OrderedModel):
    pkid = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    modified = models.DateTimeField(null=True, blank=True)


# test ordering over custom ordering field (ie. not OrderedModel.order)
class CustomOrderFieldModel(OrderedModelBase):
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)
    name = models.CharField(max_length=100)
    order_field_name = "sort_order"

    class Meta:
        ordering = ("sort_order",)


# test ThroughModel ordering with Pizzas/Topping
class Topping(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping, through="PizzaToppingsThroughModel")

    def __str__(self):
        return self.name


class PizzaToppingsThroughModel(OrderedModel):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    order_with_respect_to = "pizza"

    class Meta:
        ordering = ("pizza", "order")


# Admin only allows each model class to be registered once. However you can register a proxy class,
# and (for presentation purposes only) rename it to match the existing in Admin
class PizzaProxy(Pizza):
    class Meta:
        proxy = True
        verbose_name = "Pizza"
        verbose_name_plural = "Pizzas"


# test many-one where the item has custom PK
class CustomPKGroup(models.Model):
    name = models.CharField(max_length=100)


class CustomPKGroupItem(OrderedModel):
    group = models.ForeignKey(CustomPKGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, primary_key=True)
    order_with_respect_to = "group"


# test ordering on a base class (with order_class_path)
# ie. OpenQuestion and GroupedItem can be ordered wrt each other
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


# test grouping by a foreign model field (group__user)
class ItemGroup(models.Model):
    user = models.ForeignKey(
        TestUser, on_delete=models.CASCADE, related_name="item_groups"
    )


class GroupedItem(OrderedModel):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE, related_name="items")
    order_with_respect_to = "group__user"
