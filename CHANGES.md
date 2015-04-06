Change log
==========

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
