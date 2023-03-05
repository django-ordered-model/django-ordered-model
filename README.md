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

Please install using Pip:

```bash
$ pip install django-ordered-model
```

Or if you have checked out the repository:

```bash
$ python setup.py install
```

Or to use the latest development code from our master branch:

```bash
$ pip uninstall django-ordered-model
$ pip install git+git://github.com/django-ordered-model/django-ordered-model.git
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

```

Then run the usual `$ ./manage.py makemigrations` and `$ ./manage.py migrate` to update your database schema.

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

For performance reasons, the `delete()`, `to()`, `below()`, `above()`, `top()`, and
`bottom()` methods use Django's `update()` method to change the order of other objects
that are shifted as a result of one of these calls. If the model has fields that
are typically updated in a customized save() method, or through other app level
functionality such as `DateTimeField(auto_now=True)`, you can add additional fields
to be passed through to `update()`. This will only impact objects where their order
is being shifted as a result of an operation on the target object, not the target
object itself.

```python
foo.to(12, extra_update={'modified': now()})
```

### Get the previous or next objects

```python
foo.previous()
foo.next()
```

The `previous()` and `next()` methods return the neighbouring objects directly above or below
within the ordered stack.

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
When your model your extends `OrderedModel`, it inherits a custom `ModelManager` instance which in turn provides additional operations on the resulting `QuerySet`. For example if `Item` is an `OrderedModel` subclass, the  queryset `Item.objects.all()` has functions:

* `above_instance(object)`,
* `below_instance(object)`,
* `get_min_order()`,
* `get_max_order()`,
* `above(index)`,
* `below(index)`

If your `Model` uses a custom `ModelManager` (such as `ItemManager` below) please have it extend `OrderedModelManager`.

If your `ModelManager` returns a custom `QuerySet` (such as `ItemQuerySet` below) please have it extend `OrderedModelQuerySet`.

```python
from ordered_model.models import OrderedModel, OrderedModelManager, OrderedModelQuerySet

class ItemQuerySet(OrderedModelQuerySet):
    pass

class ItemManager(OrderedModelManager):
    def get_queryset(self):
        return ItemQuerySet(self.model, using=self._db)

class Item(OrderedModel):
    objects = ItemManager()
```

If another Django plugin requires you to use specific `Model`, `QuerySet` or `ModelManager` classes, you might need to construct intermediate classes using multiple inheritance, [see an example in issue 270](https://github.com/django-ordered-model/django-ordered-model/issues/270).

Custom ordering field
---------------------
Extending `OrderedModel` creates a `models.PositiveIntegerField` field called `order` and the appropriate migrations. It customises the default `class Meta` to then order returned querysets by this field. If you wish to use an existing model field to store the ordering, subclass `OrderedModelBase` instead and set the attribute `order_field_name` to match your field name and the `ordering` attribute on `Meta`:

```python
class MyModel(OrderedModelBase):
    ...
    sort_order = models.PositiveIntegerField(editable=False, db_index=True)
    order_field_name = "sort_order"

    class Meta:
        ordering = ("sort_order",)
```
Setting `order_field_name` is specific for this library to know which field to change when ordering actions are taken. The `Meta` `ordering` line is existing Django functionality to use a field for sorting.
See `tests/models.py` object `CustomOrderFieldModel` for an example.


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

![ItemAdmin screenshot](./static/items.png)


For a many-to-many relationship you need one of the following inlines.

`OrderedTabularInline` or `OrderedStackedInline` just like the django admin.

For the `OrderedTabularInline` it will look like this:

```python
from django.contrib import admin
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin
from models import Pizza, PizzaToppingsThroughModel


class PizzaToppingsTabularInline(OrderedTabularInline):
    model = PizzaToppingsThroughModel
    fields = ('topping', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)
    extra = 1


class PizzaAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    model = Pizza
    list_display = ('name', )
    inlines = (PizzaToppingsTabularInline, )


admin.site.register(Pizza, PizzaAdmin)
```

![PizzaAdmin screenshot](./static/pizza.png)


For the `OrderedStackedInline` it will look like this:

```python
from django.contrib import admin
from ordered_model.admin import OrderedStackedInline, OrderedInlineModelAdminMixin
from models import Pizza, PizzaToppingsThroughModel


class PizzaToppingsStackedInline(OrderedStackedInline):
    model = PizzaToppingsThroughModel
    fields = ('topping', 'move_up_down_links',)
    readonly_fields = ('move_up_down_links',)
    ordering = ('order',)
    extra = 1


class PizzaAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', )
    inlines = (PizzaToppingsStackedInline, )


admin.site.register(Pizza, PizzaAdmin)
```

![PizzaAdmin screenshot](./static/pizza-stacked.png)

**Note:** `OrderedModelAdmin` requires the inline subclasses of `OrderedTabularInline` and `OrderedStackedInline` to be listed on `inlines` so that we register appropriate URL routes. If you are using Django 3.0 feature `get_inlines()` or `get_inline_instances()` to return the list of inlines dynamically, consider it a filter and still add them to `inlines` or you might encounter a “No Reverse Match” error when accessing model change view.

Re-ordering models
------------------

In certain cases the models will end up in a not properly ordered state. This can be caused
by bypassing the 'delete' / 'save' methods, or when a user changes a foreign key of a object
which is part of the 'order_with_respect_to' fields. You can use the following command to
re-order one or more models.

    $ ./manage.py reorder_model <app_name>.<model_name> \
            [<app_name>.<model_name> ... ]

    The arguments are as follows:
    - `<app_name>`: Name of the application for the model.
    - `<model_name>`: Name of the model that's an OrderedModel.


Django Rest Framework
---------------------

To support updating ordering fields by Django Rest Framework, we include a serializer `OrderedModelSerializer` that intercepts writes to the ordering field, and calls `OrderedModel.to()` method to effect a re-ordering:

    from rest_framework import routers, serializers, viewsets
    from ordered_model.serializers import OrderedModelSerializer
    from tests.models import CustomItem

    class ItemSerializer(serializers.HyperlinkedModelSerializer, OrderedModelSerializer):
        class Meta:
            model = CustomItem
            fields = ['pkid', 'name', 'modified', 'order']

    class ItemViewSet(viewsets.ModelViewSet):
        queryset = CustomItem.objects.all()
        serializer_class = ItemSerializer

    router = routers.DefaultRouter()
    router.register(r'items', ItemViewSet)

Note that you need to include the 'order' field (or your custom field name) in the `Serializer`'s `fields` list, either explicitly or using `__all__`. See [ordered_model/serializers.py](ordered_model/serializers.py) for the implementation.

Test suite
----------

To run the tests against your current environment, use:

```bash
$ pip install djangorestframework
$ django-admin test --pythonpath=. --settings=tests.settings
```

Otherwise please install `tox` and run the tests for a specific environment with `-e` or all environments:

```bash
$ tox -e py36-django30
$ tox
```

Compatibility with Django and Python
-----------------------------------------

|django-ordered-model version | Django version      | Python version    | DRF (optional)
|-----------------------------|---------------------|-------------------|----------------
| **3.6.x**                   | **3.x**, **4.x**    | **3.5** and above | 3.12 and above
| **3.5.x**                   | **3.x**, **4.x**    | **3.5** and above | -
| **3.4.x**                   | **2.x**, **3.x**    | **3.5** and above | -
| **3.3.x**                   | **2.x**             | **3.4** and above | -
| **3.2.x**                   | **2.x**             | **3.4** and above | -
| **3.1.x**                   | **2.x**             | **3.4** and above | -
| **3.0.x**                   | **2.x**             | **3.4** and above | -
| **2.1.x**                   | **1.x**             | **2.7** to 3.6    | -
| **2.0.x**                   | **1.x**             | **2.7** to 3.6    | -


Maintainers
-----------

 * [Ben Firshman](https://github.com/bfirsh)
 * [Chris Shucksmith](https://github.com/shuckc)
 * [Sardorbek Imomaliev](https://github.com/imomaliev)
