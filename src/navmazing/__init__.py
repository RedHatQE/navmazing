"""A simplified navigation framework with prerequisite, object and intelligence support.

An example is below::

    from navmazing import Navigate, NavigateStep, NavigateToSibling

    navigate = Navigate()

    class Provider(object):
        def __init__(self, name):
            self.name = name


    @navigate.register(Provider, 'New')
    class AddANewProvider(NavigateStep)
        prerequisite = NavigateToSibling('All')

        def step(self):
            click('Add New Button')

    @navigate.register(Provider, 'All')
    class ShowAllProviders(NavigateStep)
        def am_i_here(self):
            return check_if_i_am_already_on_page()

        def step(self):
            click('All button')

"""
from __future__ import annotations
from ._errors import NavigationTriesExceeded
from ._navigator import Navigate
from ._step import NavigateStep
from ._shortcuts import NavigateToAttribute, NavigateToSibling, NavigateToObject

__all__ = [
    "Navigate",
    "NavigateStep",
    "NavigationTriesExceeded",
    "NavigateToObject",
    "NavigateToSibling",
    "NavigateToAttribute",
]
