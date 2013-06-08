django-ordered-model
====================

[![Build Status](https://secure.travis-ci.org/bfirsh/django-ordered-model.png?branch=master)](https://travis-ci.org/bfirsh/django-ordered-model)

django-ordered-model allows models to be ordered and provides a simple admin 
interface for reordering them.

Based on http://www.djangosnippets.org/snippets/998/ and 
http://www.djangosnippets.org/snippets/259/

Requires:

  * Django 1.4

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

If you have a manytomany relationship derive the `through` model from OrderedModel 
and set group_m2m_by to the field name by which to group the entries:

    class Item(models.Model):
        name = models.CharField(max_length=100)
        other_items = models.ManyToManyField(OtherItem, through='ThroughModel')

    class ThroughModel(OrderedModel):
        item = models.ForeignKey(Item)
        other_item = models.ForeignKey(OtherItem)
        group_m2m_by = 'item'
        
And add the following to the admin.py:

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

Model instances now have `move_up()` and `move_down()` methods to move them 
relative to each other.

To add arrows in the admin change list page to do reordering, you can use the 
`OrderedModelAdmin` and the `move_up_down_links` field:
    
    from django.contrib import admin
    from ordered_model.admin import OrderedModelAdmin
    from models import Item
    
    class ItemAdmin(OrderedModelAdmin):
        list_display = ('name', 'move_up_down_links')
    
    admin.site.register(Item, ItemAdmin)


Test suite
----------

    $ ./run_tests.sh

