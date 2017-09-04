Change log
==========

1.4.3 - 2017-08-29
------------------

- Fix a problem with links in the admin when using multiple threads.

1.4.2 - 2017-08-18
------------------

- Use Django's version of `six`
- Fix various deprecations
- Fix missing up/down links with custom primary key

1.4.1 - 2017-04-16
------------------

### Fixed

- `pip install` not working due to missing `requirements.txt`

1.4.0 - 2017-04-14
------------------

### Added

- Support for ordering using a specified base class when using Multi-table inheritance
- Suport for Python 3.6, Django 1.10 and 1.11.

### Fixed

- The move up/down links in OrderedTabularInline
- Passing args to `filter()` which broke django-polymorphic.


1.3.0 – 2016-10-08
------------------

 - Add `extra_update` argument to various methods.
 - Fix bug in `order_with_respect_to` when using string in Python 3.

1.2.1 – 2016-07-12
------------------

 - Various bug fixes in admin
 - Add support for URL namespaces other than "admin"

1.2.0 – 2016-07-08
------------------

 - Remove support for Django <1.8 and Python 2.6
 - Support for multiple order_with_respect_to fields
 - Remove usage of deprecated django.conf.urls.patterns

1.1.0 – 2016-01-15
------------------

 - Add support for many-to-many models.
 - Add Italian translations.

1.0.0 – 2015-11-24
------------------

1.0, because why not. Seems to be working alright for everyone. Some little things in this release:

 - Add support for custom order field by inheriting from `OrderedModelBase` and setting `order_field_name`.
 - Add support for Python 3.
 - Drop support for Django 1.4.

0.4.2 – 2015-06-02
------------------

 - Fix admin buttons not working with custom primary keys.
 - Fix admin using deprecated `get_query_set` method.

0.4.1 – 2015-04-06
------------------

 - Add support for Django 1.7 and 1.8.
 - Fix deprecation warning about module\_name.
 - Add French translations.

0.4.0 – 2014-07-31
------------------

 - Models can now be moved to any position, not just up and down. `move_up()` and `move_down()` are replaced by `up()` and `down()`. See the readme for the full set of new methods.
 - Add `order_with_respect_to` option so models can be ordered based on another field.
 - The admin ordering controls are now rendered using templates.
 - Ordering now always starts from 0 and has no gaps. Previously, gaps in the ordering numbers could appear when models were deleted, etc.
 - Fix bug where objects always get the order of "0".
 - Models with custom primary keys can now be used as ordered models.


0.3.0 – 2013-10-25
------------------

 - Support for Django 1.4, 1.5 and 1.6.
 - Fix list_filter being deselected when moving in admin
 - Improve performance of ordering by adding index and using Max aggregate

0.2.0 – 2012-11-14
------------------

 - First release
