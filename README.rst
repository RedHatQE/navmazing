.. image:: https://travis-ci.org/RedHatQE/navmazing.svg
   :scale: 50 %
   :alt: Build Status
   :align: left
   :target: https://travis-ci.org/RedHatQE/navmazing
.. image:: https://coveralls.io/repos/RedHatQE/navmazing/badge.svg?branch=master&service=github
   :scale: 50 %
   :alt: Coverage Status
   :align: left
   :target: https://coveralls.io/github/RedHatQE/navmazing?branch=master

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
