django-ordered-model
====================

django-ordered-model allows models to be ordered and provides a simple admin 
interface for reordering them.

Based on http://www.djangosnippets.org/snippets/998/ and 
http://www.djangosnippets.org/snippets/259/

Requires:

  * Django 1.1

Installation
------------

    $ python setup.py install

Usage
-----

Inherit your model from `OrderedModel` to make it ordered:
    
    from django.db import models
    from ordered_model.models import OrderedModel

    class Item(OrderedModel):
        name = models.CharField(max_length=100)
    
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

