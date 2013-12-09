django-ordered-model
====================

[![Build Status](https://secure.travis-ci.org/bfirsh/django-ordered-model.png?branch=master)](https://travis-ci.org/bfirsh/django-ordered-model)

django-ordered-model allows models to be ordered and provides a simple admin
interface for reordering them.

Based on http://www.djangosnippets.org/snippets/998/ and
http://www.djangosnippets.org/snippets/259/

Requires:

  * Django >=1.4

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


ManyToMany relationships
----------------------


If you have a manytomany relationship derive the `through` model from OrderedModel 
and set order_with_respect_to to the field name by which to group the entries:

    class Item(models.Model):
        name = models.CharField(max_length=100)
        other_items = models.ManyToManyField(OtherItem, through='ThroughModel')

    class ThroughModel(OrderedModel):
        item = models.ForeignKey(Item)
        other_item = models.ForeignKey(OtherItem)
        order_with_respect_to = 'item'
        
        class Meta:
            ordering = ('item', 'order')

The `through` model instances now have the same set of methods as the regular ordered models to move them
relative to each other.

In case of the manytomany relationship add the following to the admin.py:

    class ThroughModelInline(OrderedTabularInline):
        model = ThroughModel
        fields = ('item', 'other_item', 'order', 'move_up_down_links', )
        readonly_fields = ('order', 'move_up_down_links',)
        extra = 1

    class ItemAdmin(admin.ModelAdmin):
        list_display = ('name', )
        filter_vertical = ('other_items', )
        inlines = (ThroughModelInline, )

        def get_urls(self):
            urls = super(ItemAdmin, self).get_urls()
            return ThroughModelInline.get_urls(self) + urls

    admin.site.register(Item, ItemAdmin)

Test suite
----------

    $ ./run_tests.sh

