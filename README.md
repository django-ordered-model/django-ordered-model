django-ordered-model
====================

[![Build Status](https://secure.travis-ci.org/bfirsh/django-ordered-model.png?branch=master)](https://travis-ci.org/bfirsh/django-ordered-model)

django-ordered-model allows models to be ordered and provides a simple admin
interface for reordering them.

Based on https://djangosnippets.org/snippets/998/ and
https://djangosnippets.org/snippets/259/

Requires:

  * Django >=1.5

Installation
------------

    $ python setup.py install

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


Renumbering Models
------------------

The admin interface will not renumber entries after deletion. Therefore, to
sync up the changes, use the Django management command:

    $ ./manage.py renumber <app_name>.<model_name>[:<start_number>] \
        [<app_name>.<model_name>[:<start_number>] ... ]

The arguments are as follows:

- `<app_name>`: Name of the application for the model.
- `<model_name>`: Name of the model that's an OrderedModel.
- `<start_number>`: Optionally, a start number. For example, if the
  `<start_number>` is `5`, then renumbering will start "5, 6, 7, ..."


Test suite
----------

Requires Docker.

    $ script/test

