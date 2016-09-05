navmazing
=========

Introduction
------------

Simple navigation framework supporting complex designs

Usage
-----

An example is below

.. code-block:: python

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
