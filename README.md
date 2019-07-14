django-ordered-model
====================

[![Build Status](https://secure.travis-ci.org/bfirsh/django-ordered-model.png?branch=master)](https://travis-ci.org/bfirsh/django-ordered-model)
[![PyPI version](https://badge.fury.io/py/django-ordered-model.svg)](https://badge.fury.io/py/django-ordered-model)
[![codecov](https://codecov.io/gh/bfirsh/django-ordered-model/branch/master/graph/badge.svg)](https://codecov.io/gh/bfirsh/django-ordered-model)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

django-ordered-model allows models to be ordered and provides a simple admin
interface for reordering them.

Based on https://djangosnippets.org/snippets/998/ and
https://djangosnippets.org/snippets/259/

See our [compatability notes](#compatibility-with-django-and-python) for the appropriate version to use with older Django and Python releases.

Installation
------------

```bash
$ python setup.py install
```

You can use Pip:

```bash
$ pip install django-ordered-model
```

Usage
-----

Add `ordered_model` to your `SETTINGS.INSTALLED_APPS`.

Inherit your model from `OrderedModel` to make it ordered:

```python
from django.db import models
from ordered_model.models import OrderedModel


class Item(OrderedModel):
    name = models.CharField(max_length=100)

    class Meta(OrderedModel.Meta):
        pass
```

Model instances now have a set of methods to move them relative to each other.
To demonstrate those methods we create two instances of `Item`:

```python
foo = Item.objects.create(name="Foo")
bar = Item.objects.create(name="Bar")
```

### Swap positions

```python
foo.swap(bar)
```

This swaps the position of two objects.

### Move position up on position

```python
foo.up()
foo.down()
```

Moving an object up or down just makes it swap its position with the neighbouring
object directly above of below depending on the direction.

### Move to arbitrary position

```python
foo.to(12)
bar.to(13)
```

Move the object to an arbitrary position in the stack. This essentially sets the
order value to the specified integer. Objects between the original and the new
position get their order value increased or decreased according to the direction
of the move.

### Move object above or below reference

```python
foo.above(bar)
foo.below(bar)
```

Move the object directly above or below the reference object, increasing or
decreasing the order value for all objects between the two, depending on the
direction of the move.

### Move to top of stack

```python
foo.top()
```

This sets the order value to the lowest value found in the stack and increases
the order value of all objects that were above the moved object by one.

### Move to bottom of stack

```python
foo.bottom()
```

This sets the order value to the highest value found in the stack and decreases
the order value of all objects that were below the moved object by one.

### Updating fields that would be updated during save()

For performance reasons, the delete(), to(), below(), above(), top(), and bottom()
methods use Django's update() method to change the order of other objects that
are shifted as a result of one of these calls. If the model has fields that
are typically updated in a customized save() method, or through other app level
functionality such as DateTimeField(auto_now=True), you can add additional fields
to be passed through to update(). This will only impact objects where their order
is being shifted as a result of an operation on the target object, not the target
object itself.

```python
foo.to(12, extra_update={'modified': now()}
```

### Get the previous or next objects

```python
foo.previous()
foo.next()
```

previous() and next() get the neighbouring objects directly above of below
within the ordered stack depending on the direction.

## Subset Ordering

In some cases, ordering objects is required only on a subset of objects. For example,
an application that manages contact lists for users, in a many-to-one/many relationship,
would like to allow each user to order their contacts regardless of how other users
choose their order. This option is supported via the `order_with_respect_to` parameter.

A simple example might look like so:

```python
class Contact(OrderedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField()
    order_with_respect_to = 'user'
```

If objects are ordered with respect to more than one field, `order_with_respect_to` supports
tuples to define multiple fields:

```python
class Model(OrderedModel)
    # ...
    order_with_respect_to = ('field_a', 'field_b')
```

In a many-to-many relationship you need to use a separate through model which is derived from the OrderedModel.
For example, an application which manages pizzas with toppings.

A simple example might look like so:

```python
class Topping(models.Model):
    name = models.CharField(max_length=100)


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping, through='PizzaToppingsThroughModel')


class PizzaToppingsThroughModel(OrderedModel):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    order_with_respect_to = 'pizza'

    class Meta:
        ordering = ('pizza', 'order')
```

You can also specify `order_with_respect_to` to a field on a related model. An example use-case can be made with the following models:

```python
class ItemGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    general_info = models.CharField(max_length=100)

class GroupedItem(OrderedModel):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE)
    specific_info = models.CharField(max_length=100)
    order_with_respect_to = 'group__user'
```

Here items are put into groups that have some general information used by its items, but the ordering of the items is independent of the group the item is in.

When you want ordering on the baseclass instead of subclasses in an ordered list of objects of various classes, specify the full module path of the base class:

```python
class BaseQuestion(OrderedModel):
    order_class_path = __module__ + '.BaseQuestion'
    question = models.TextField(max_length=100)

    class Meta:
        ordering = ('order',)

class MultipleChoiceQuestion(BaseQuestion):
    good_answer = models.TextField(max_length=100)
    wrong_answer1 = models.TextField(max_length=100)
    wrong_answer2 = models.TextField(max_length=100)
    wrong_answer3 = models.TextField(max_length=100)

class OpenQuestion(BaseQuestion):
    answer = models.TextField(max_length=100)
```

Custom Manager and QuerySet
-----------------
```python
from ordered_model.models import OrderedModelManager, OrderedModel


class ItemManager(OrderedModelManager):
    pass


class Item(OrderedModel):
    objects = ItemManager()
```

Admin integration
-----------------

To add arrows in the admin change list page to do reordering, you can use the
`OrderedModelAdmin` and the `move_up_down_links` field:

```python
from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from models import Item


class ItemAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links')

admin.site.register(Item, ItemAdmin)
```

For a many-to-many relationship you need one of the following inlines.

`OrderedTabularInline` or `OrderedStackedInline` just like the django admin.

For the `OrderedTabularInline` it will look like this:

```python
from django.contrib import admin
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin
from models import Pizza, PizzaToppingsThroughModel


class PizzaToppingsThroughModelTabularInline(OrderedTabularInline):
    model = PizzaToppingsThroughModel
    fields = ('topping', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    extra = 1
    ordering = ('order',)


class PizzaAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', )
    inlines = (PizzaToppingsThroughModelTabularInline, )


admin.site.register(Pizza, PizzaAdmin)
```

For the `OrderedStackedInline` it will look like this:

```python
from django.contrib import admin
from ordered_model.admin import OrderedStackedInline, OrderedInlineModelAdminMixin
from models import Pizza, PizzaToppingsThroughModel


class PizzaToppingsThroughModelStackedInline(OrderedStackedInline):
    model = PizzaToppingsThroughModel
    fields = ('topping', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    extra = 1
    ordering = ('order',)


class PizzaAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', )
    inlines = (PizzaToppingsThroughModelStackedInline, )


admin.site.register(Pizza, PizzaAdmin)
```

Test suite
----------

Requires Docker.

```bash
$ script/test
```

Compatibility with Django and Python
-----------------------------------------

|django-ordered-model version | Django version      | Python version
|-----------------------------|---------------------|--------------------
| **3.3.x**                   | **2.x**             | **3.4** and above
| **3.2.x**                   | **2.x**             | **3.4** and above
| **3.1.x**                   | **2.x**             | **3.4** and above
| **3.0.x**                   | **2.x**             | **3.4** and above
| **2.1.x**                   | **1.x**             | **2.7** to **3.6**
| **2.0.x**                   | **1.x**             | **2.7** to **3.6**


Maintainers
-----------

 * [Ben Firshman](https://github.com/bfirsh)
 * [Chris Shucksmith](https://github.com/shuckc)
 * [Sardorbek Imomaliev](https://github.com/imomaliev)
