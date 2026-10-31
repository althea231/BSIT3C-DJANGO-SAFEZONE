"""SafeZone Django project package.

Python 3.14 + Django 5.0 compatibility shim
-------------------------------------------
Django 5.0 implements ``django.template.context.BaseContext.__copy__`` as
``copy(super())``. Python 3.14 no longer lets an attribute be set on the copied
``super`` proxy, so copying a template context raises::

    AttributeError: 'super' object has no attribute 'dicts'
                    and no __dict__ for setting new attributes

Django's test client copies the render context of every rendered response
(``django.test.client.store_rendered_templates``), which made *every*
template-rendering test fail in this environment, independent of application
code. The replacement below keeps the original semantics: a shallow duplicate
of the same context class with a new list of context layers.

This shim is a no-op on Python <= 3.13 and can be deleted once the project is
upgraded to a Django release that supports Python 3.14 (Django >= 6.0).
"""

import sys

if sys.version_info >= (3, 14):
    from django.template.context import BaseContext

    def _compatible_context_copy(self):
        duplicate = object.__new__(type(self))
        duplicate.__dict__ = self.__dict__.copy()
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _compatible_context_copy
