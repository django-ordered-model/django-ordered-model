#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
 
setup(
    name='django-ordered-model',
    version='1.2.1',
    description='Allows Django models to be ordered and provides a simple admin interface for reordering them.',
    author='Ben Firshman',
    author_email='ben@firshman.co.uk',
    url='http://github.com/bfirsh/django-ordered-model',
    packages=[
        'ordered_model',
        'ordered_model.tests',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    package_data={'ordered_model': ['static/ordered_model/arrow-up.gif',
                                    'static/ordered_model/arrow-down.gif',
                                    'locale/de/LC_MESSAGES/django.po',
                                    'locale/de/LC_MESSAGES/django.mo',
                                    'locale/pl/LC_MESSAGES/django.po',
                                    'locale/pl/LC_MESSAGES/django.mo',
                                    'templates/ordered_model/admin/order_controls.html']}
)
