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
import inspect
from operator import attrgetter


class NavigationDestinationNotFound(Exception):
    """Simple Exception when navigations can't be found"""
    def __init__(self, name, cls, possibilities):
        self.name = name
        self.cls = cls
        self.possibilities = possibilities

    def __str__(self):
        return ("Couldn't find the destination [{}] with the given class [{}]"
            " the following were available [{}]").format(
            self.name, self.cls, ", ".join(sorted(list(self.possibilities))))


class NavigationTriesExceeded(Exception):
    """Simple Exception when navigations can't be found"""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Navigation failed to reach [{}] in the specificed tries".format(
            self.name)


class Navigate(object):
    def __init__(self):
        """Initializes the destination dictionary for the Navigate object """
        self.dest_dict = {}

    def register(self, cls, name=None):
        """Decorator that registers a class with an optional name"""
        def f(obj):
            """This is part of the decorator class

            This function is returned and run with the class it decorates as the obj argument.
            The destination name is either the supplied name, or the class name of the NavigateStep
            object.
            """
            destination_name = name or obj.__name__
            obj._name = destination_name
            self.dest_dict[cls, destination_name] = obj
            return obj
        return f

    def get_class(self, cls_or_obj, name):
        cls = type(cls_or_obj) if not inspect.isclass(cls_or_obj) else cls_or_obj
        for class_ in cls.__mro__:
            try:
                nav = self.dest_dict[class_, name]
            except KeyError:
                continue
            else:
                break
        else:
            raise NavigationDestinationNotFound(name, cls.__name__,
                self.list_destinations(cls))

        return nav

    def navigate(self, cls_or_obj, name, *args, **kwargs):
        """This function performs the navigation

        We first determine if we have a class of an instance and find the class
        either way. We then walk the MRO for the class and attempt to find a matching
        destination name in the dest_dict. KeyErrors are expected and accepted. This
        allows us to override a destination in a subclass if we so desire, as the MRO
        walk means we will always go to the overridden version first.

        In any case, we instantiate the NavigateStep object there and then with the
        information we have been given, namely the object that we are using as context
        and this Navigate object. We next try to run the .go() method of the NavigateStep object

        If we exhaust the MRO and we have still not found a match, we raise an exception.
        """
        nav = self.get_class(cls_or_obj, name)
        return nav(cls_or_obj, self).go(0, *args, **kwargs)

    def list_destinations(self, cls_or_obj):
        """Lists all available destinations for a given object

        This function lists all available destinations for a given object. If the object
        overrides a destination, only the overridden one will be displayed.
        """
        destinations = set()
        cls = type(cls_or_obj) if not isinstance(cls_or_obj, type) else cls_or_obj
        for _class in cls.__mro__[::-1]:
            for the_class, name in self.dest_dict:
                if the_class == _class:
                    destinations.add(name)
        return destinations


class NavigateToObject(object):
    """This is a helper descriptor for navigation destinations which are on another class/object.

    For instance, imagine you have a different object that has a 'ViewAll', destination that
    needs to be visited before you can click on 'New'. In this instance, you would need to make the
    'New' destination use 'ViewAll' as a prerequisite. As this would need no other special
    input, we can use NavigateToObject as a helper. This will set prerequisite to be a
    callable that will navigate to the prerequisite step on the other object.
    """
    def __init__(self, other_obj, target, obj=None):
        self.target = target
        self.obj = obj
        self.other_obj = other_obj

    def __get__(self, obj, owner):
        if self.obj is None:
            return type(self)(self.other_obj, self.target, obj or owner)
        else:
            return self

    def __call__(self):
        return self.obj.navigate_obj.navigate(self.other_obj, self.target)


class NavigateToSibling(object):
    """This is a helper descriptor for navigation destinations which are linked to the same class.

    For instance, imagine you have an object that has a 'ViewAll', destination that needs to
    be visited before you can click on 'New'. In this instance, you would need to make the
    'New' destination use 'ViewAll' as a prerequisite. As this would need no other special
    input, we can use NavigateToSibling as a helper. This will set prerequisite to be a
    callable that will navigate to the prerequisite step.
    """
    def __init__(self, target, obj=None):
        self.target = target
        self.obj = obj

    def __get__(self, obj, owner):
        if self.obj is None:
            return type(self)(self.target, obj or owner)
        else:
            return self

    def __call__(self):
        return self.obj.navigate_obj.navigate(self.obj.obj, self.target)


class NavigateToAttribute(object):
    """This is a helper descriptor for destinations which are linked to an attribute of the object.

    For instance, imagine you have an object that has an attribute(parent) which has a 'ViewAll',
    destination that needs to be visited before you can click on 'New'. In this instance,
    you would need to make the 'New' destination use 'ViewAll' as a prerequisite. As this
    would need no other special input, we can use NavigateToAttribute as a helper, supplying
    only the name of the attribute which stores the object to be used in the navigation,
    and the destination name. This will set prerequisite to be a callable that will navigate
    to the prerequisite step.
    """
    def __init__(self, attr_name, target, obj=None):
        self.target = target
        self.obj = obj
        self.attr_name = attr_name
        self._get_attr = attrgetter(attr_name)

    def __get__(self, obj, owner):
        if self.obj is None:
            return type(self)(self.attr_name, self.target, obj or owner)
        else:
            return self

    def __call__(self):
        attr = self._get_attr(self.obj.obj)
        return self.obj.navigate_obj.navigate(attr, self.target)


class NavigateStep(object):
    """A Navigation Step object

    The NavigateStep object runs through several key stages
    1) It checks to see if we are already at that navigation step, if so, we return
    2) It runs the prerequisite to see if there is a step that is required to be run
       before this one.
    3) It runs the step function to navigate to the current step after the prerequisite has been
       completed
    """
    _default_tries = 3

    def __init__(self, obj, navigate_obj):
        """ NavigateStep object.

        A NavigateStep object should always recieve the object it is linked to
        and this is stored in the obj attribute. The navigate_obj is the Navigate() instance
        that the destination is registered against. This allows it to navigate inside pre-requisites
        using the NavigateToSibling and NavigateToAttribute helpers described above.
        """
        self.obj = obj
        self.navigate_obj = navigate_obj

    def am_i_here(self, *args, **kwargs):
        """Describes if the navigation is already at the requested destination.

        This is a default and is generally overridden.
        """
        return False

    def resetter(self, *args, **kwargs):
        """Describes any steps required to reset the view after navigating or if already there.

        This is a default and is generally overridden.
        """
        pass

    def prerequisite(self, *args, **kwargs):
        """Describes a step that must be carried our prior to this one.

        This often calls a previous navigate_to, often using one of the helpers, NavigateToSibling
        which will navigate to a given destination using the same object, or NavigateToAttribute
        which will navigate to a destination against an object describe by the attribute of the
        parent object.

        This is a default and is generally overridden.
        """
        pass

    def step(self, *args, **kwargs):
        """Describes the work to be done to get to the destination after the prequisite is met.

        This is a default and is generally overridden.
        """
        return

    def do_nav(self, _tries, *args, **kwargs):
        """Describes how the navigation should take place."""
        try:
            self.step(*args, **kwargs)
        except:
            self.go(_tries, *args, **kwargs)

    def pre_navigate(self, _tries, *args, **kwargs):
        """Describes steps that takes place before any prerequisite or navigation takes place.

        This is a default and is generally overridden.
        """
        if _tries > self._default_tries:
            raise NavigationTriesExceeded(self._name)
        else:
            return

    def post_navigate(self, _tries, *args, **kwargs):
        """Describes steps that takes place before any prerequisite after navigation takes place.

        This is a default and is generally overridden.
        """
        return

    def go(self, _tries=0, *args, **kwargs):
        """Describes the flow of navigation."""
        _tries += 1
        self.pre_navigate(_tries, *args, **kwargs)
        print("NAVIGATE: Checking if already at {}".format(self._name))
        here = False
        try:
            here = self.am_i_here(*args, **kwargs)
        except Exception as e:
            print("NAVIGATE: Exception raised [{}] whilst checking if already at {}".format(
                e, self._name))
        if here:
            print("NAVIGATE: Already at {}".format(self._name))
        else:
            print("NAVIGATE: I'm not at {}".format(self._name))
            self.parent = self.prerequisite(*args, **kwargs)
            print("NAVIGATE: Heading to destination {}".format(self._name))
            self.do_nav(_tries, *args, **kwargs)
        self.resetter(*args, **kwargs)
        self.post_navigate(_tries, *args, **kwargs)


navigate = Navigate()
