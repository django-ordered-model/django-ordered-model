django-ordered-model
====================

[![Build Status](https://secure.travis-ci.org/bfirsh/django-ordered-model.png?branch=master)](https://travis-ci.org/bfirsh/django-ordered-model)

django-ordered-model allows models to be ordered and provides a simple admin
interface for reordering them.

Based on https://djangosnippets.org/snippets/998/ and
https://djangosnippets.org/snippets/259/

Requires:

  * Django >=1.8
  * Python 2.7 or >=3.3

Installation
------------

    $ python setup.py install

You can use Pip:

    $ pip install django-ordered-model

Usage
-----

Add `ordered_model` to your `SETTINGS.INSTALLED_APPS`.

Inherit your model from `OrderedModel` to make it ordered:

    from django.db import models
    from ordered_model.models import OrderedModel

    class Item(OrderedModel):
        name = models.CharField(max_length=100)

        class Meta(OrderedModel.Meta):
            pass

Model instances now have a set of methods to move them relative to each other.
To demonstrate those methods we create two instances of `Item`:

    foo = Item.objects.create(name="Foo")
    bar = Item.objects.create(name="Bar")

### Swap positions

    foo.swap(bar)

This swaps the position of two objects.

### Move position up on position

    foo.up()
    foo.down()

Moving an object up or down just makes it swap its position with the neighouring
object directly above of below depending on the direction.

### Move to arbitrary position

    foo.to(12)
    bar.to(13)

Move the object to an arbitrary position in the stack. This essentially sets the
order value to the specified integer. Objects between the original and the new
position get their order value increased or decreased according to the direction
of the move.

### Move object above or below reference

    foo.above(bar)
    foo.below(bar)

Move the object directly above or below the reference object, increasing or
decreasing the order value for all objects between the two, depending on the
direction of the move.

### Move to top of stack

    foo.top()

This sets the order value to the lowest value found in the stack and increases
the order value of all objects that were above the moved object by one.

### Move to bottom of stack

    foo.bottom()

This sets the order value to the highest value found in the stack and decreases
the order value of all objects that were below the moved object by one.

## Subset Ordering

In some cases, ordering objects is required only on a subset of objects. For example,
an application that manages contact lists for users, in a many-to-one/many relationship,
would like to allow each user to order their contacts regardless of how other users
choose their order. This option is supported via the `order_with_respect_to` parameter.

A simple example might look like so:

    class Contact(OrderedModel):
        user = models.ForeignKey(User)
        phone = models.CharField()
        order_with_respect_to = 'user'

If objects are ordered with respect to more than one field, `order_with_respect_to` supports
tuples to define multiple fields:

    class Model(OrderedModel)
        # ...
        order_with_respect_to = ('field_a', 'field_b')

In a many-to-many relationship you need to use a seperate through model which is derived from the OrderedModel.
For example, an application which manages pizzas with toppings.

A simple example might look like so:

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

Admin integration
-----------------

To add arrows in the admin change list page to do reordering, you can use the
`OrderedModelAdmin` and the `move_up_down_links` field:

    from django.contrib import admin
    from ordered_model.admin import OrderedModelAdmin
    from models import Item

    class ItemAdmin(OrderedModelAdmin):
        list_display = ('name', 'move_up_down_links')

    admin.site.register(Item, ItemAdmin)


For a many-to-many relationship you need the following in the admin.py file:

    from django.contrib import admin
    from ordered_model.admin import OrderedTabularInline
    from models import Pizza, PizzaToppingsThroughModel

    class PizzaToppingsThroughModelInline(OrderedTabularInline):
        model = PizzaToppingsThroughModel
        fields = ('topping', 'order', 'move_up_down_links',)
        readonly_fields = ('order', 'move_up_down_links',)
        extra = 1
        ordering = ('order',)

    class PizzaAdmin(admin.ModelAdmin):
        list_display = ('name', )
        inlines = (PizzaToppingsThroughModelInline, )

        def get_urls(self):
            urls = super(PizzaAdmin, self).get_urls()
            for inline in self.inlines:
                if hasattr(inline, 'get_urls'):
                    urls = inline.get_urls(self) + urls
            return urls

    admin.site.register(Pizza, PizzaAdmin)

Test suite
----------

Requires Docker.

    $ script/test
