#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

with open('requirements.txt') as f:
    requires = f.read().splitlines()

setup(
    name='django-ordered-model',
    version='1.4.2',
    description='Allows Django models to be ordered and provides a simple admin interface for reordering them.',
    author='Ben Firshman',
    author_email='ben@firshman.co.uk',
    url='http://github.com/bfirsh/django-ordered-model',
    packages=[
        'ordered_model',
        'ordered_model.tests',
    ],
    requires=requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    zip_safe = False,
    package_data={'ordered_model': ['static/ordered_model/arrow-up.gif',
                                    'static/ordered_model/arrow-down.gif',
                                    'locale/de/LC_MESSAGES/django.po',
                                    'locale/de/LC_MESSAGES/django.mo',
                                    'locale/pl/LC_MESSAGES/django.po',
                                    'locale/pl/LC_MESSAGES/django.mo',
                                    'templates/ordered_model/admin/order_controls.html']}
)
