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

Design
------

navmazing is based around a number of navigation steps which subclass the NavigateStep object. These step objects have a relationship by defining a prerequisite method which can go to the previous step if it is determined that we are not current on the requested step. This chaining of steps starting at a first and visiting all the prerequisites in the chain until they are resolved constitutes a complete navigation.

Usage
-----

An example is below. This creates a simple class modelling some Provider object that has three destinations or pages in the UI, a **New** page, a **Details** page and an **All** page. The **New** page is where a new Provider would be added, and the **All** page is where you could view a list of all of them. To get to the **New** page, you must first visit the **All** page. The **Details** page is where a specific provider would be displayed. In the example below you can see that we model some very simple steps and register them to the class.

.. code-block:: python

  from navmazing import Navigate, NavigateStep, NavigateToSibling

  navigator = Navigate()

  class Provider(object):
      def __init__(self, name):
          self.name = name

  @navigator.register(Provider, 'Details')
  class ProviderDetails(NavigateStep):
      prerequisite = NavigateToSibling('All')

      def step(self):
          click(self.obj.name)

  @navigator.register(Provider, 'New')
  class AddANewProvider(NavigateStep):
      prerequisite = NavigateToSibling('All')

      def step(self):
          click('Add New Button')

  @navigator.register(Provider, 'All')
  class ShowAllProviders(NavigateStep):
      def am_i_here(self):
          return check_if_i_am_already_on_page()

      def step(self):
          click('All button')

The class ``ShowAllProviders`` represents the step of getting to the **All** page. This class has two methods, ``am_i_here()`` and ``step()``. The ``step()`` method describes how we should perform the step of getting to the **All** page. It is assumed in this particular UI that the *All button* is always visible. The ``am_i_here()`` method is a way to query to see if we are already on this page. This is used to shortcut navigation if it can be determined that we are already on a page that we have requested to visit.

The class ``AddANewProvider`` represents the step of getting to the **New** page. This class has an attribute and a method. The ``prerequisite`` is actually a python descriptor. It uses the ``NavigateToSibling`` helper to navigate to the **All** destination on the same object that it has been requested to visit the **New** page on. One could simply make ``prerequisite`` a function that calls ``navigate_to`` with ``self.obj`` and the ``All`` destination. However the helper is much nicer and makes defining prerequisite steps a little more cleaner.

The class ``ProviderDetails`` represents the step of getting to a specific providers page, its **Details** page. This class is the same as the ``AddANewProvider`` class in that it first requires the All button to be pressed. Notice in the ``step()`` method, that there is a reference to ``self.obj``. This object is the object that is passed to navigation step as can be seen below. In the example below this object is called ``prov``.

.. code-block:: python

  # Non helper method
  def prerequisite(self):
      navigator.navigate(self.obj, 'All')

  # Using helper method
  prerequisite = NavigateToSibling('All')

To use the code above, one would instantiate a Provider object and then use the navigate method like so:

.. code-block:: python


  prov = Provider('name')
  navigator.navigate(prov, 'Details')

Navigation Helpers
------------------

navmazing has a few helpers to make prerequisites easier to define

* ``NavigateToSibling`` - Navigates to a destination that is registered to the same object as the current request.
* ``NavigateToAttribute`` - Navigates to a destination that is registered to an attribute of the same object as the current request. This is useful if there is some kind of hierarcy to your objects and you wish to navigate to a step that is registered against an attribute rather than the object itself
* ``NavigateToObject`` - Navigates to a destination that is registered to the supplied object, it could be argued that NavigateToAttribute could be implemented with a NavigateToObject call, by simply offering the attribute object as the object. It feels more dynamic and cleaner to use NavigateToAttribute in these cases, there the attribute is a string that is looked up, rather than an object which is static.

Flowchart
---------

The diagram below shows the flowchart of the process of resolving a navigation using the stock navmazing library. As the methods are overridable, the flow can be altered, but should suffice for most usages.

.. image:: https://github.com/psav/navmazing/raw/master/flowchart.png

Advanced Usage
--------------

navmazing also allows parameters to be passed at the navigate call. This means you can allow for some level of dynamic nature or choice in your navigation destinations. Let's say for example you have a step that usually works one way, but there are certain times when you need to overide that behaviour and make it work a different way.

.. code-block:: python

  @navigator.register(Provider, 'Details')
  class ProviderDetails(NavigateStep)
      prerequisite = NavigateToSibling('All')

      def step(self, active=True):
          if choice:
              click(self.obj.name)
          else:
              click(self.obj.name + " - inactive")

  # Call by default
  navigate(obj, 'Details')

  # Call, passing in a parameter for choice
  navigate(obj, 'Details', active=False)

In the example above, passing the ``active`` parameter changes the behaviour of the step.
