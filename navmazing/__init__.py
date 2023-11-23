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
import inspect
import logging
from operator import attrgetter
from typing import Callable, TypeVar, ClassVar
from typing_extensions import Self

from copy import copy as _copy

null_logger = logging.getLogger("navmazing_null")
null_logger.addHandler(logging.NullHandler())
T = TypeVar("T")


class NavigationDestinationNotFound(Exception):
    """Simple Exception when navigations can't be found"""

    name: str
    cls: type | str
    possibilities: set[str]

    def __init__(self, name: str, cls: type | str, possibilities: set[str]) -> None:
        self.name = name
        self.cls = cls
        self.possibilities = possibilities

    def __str__(self) -> str:
        return (
            "Couldn't find the destination [{}] with the given class [{}]"
            " the following were available [{}]"
        ).format(self.name, self.cls, ", ".join(sorted(list(self.possibilities))))


class NavigationTriesExceeded(Exception):
    """Simple Exception when navigations can't be found"""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"Navigation failed to reach [{self.name}] in the specified tries"


class Navigate:
    dest_dict: dict[tuple[type, str], type[NavigateStep]]
    logger: logging.Logger

    def __init__(self, logger: logging.Logger = null_logger) -> None:
        """Initializes the destination dictionary for the Navigate object"""
        self.dest_dict = {}
        self.logger = logger

    def register(
        self, cls: type, name: str | None = None
    ) -> Callable[[type[NavigateStep]], type[NavigateStep]]:
        """Decorator that registers a class with an optional name"""

        def f(obj: type[NavigateStep]) -> type[NavigateStep]:
            """This is part of the decorator class

            This function is returned and run with the class it decorates as the obj argument.
            The destination name is either the supplied name, or the class name of the NavigateStep
            object.
            """
            destination_name: str = name or obj.__name__
            obj._name = destination_name
            self.dest_dict[cls, destination_name] = obj
            return obj

        return f

    def get_class(self, cls_or_obj: type | object, name: str) -> type[NavigateStep]:
        cls: type = type(cls_or_obj) if not inspect.isclass(cls_or_obj) else cls_or_obj
        for class_ in cls.__mro__:
            try:
                nav = self.dest_dict[class_, name]
            except KeyError:
                continue
            else:
                break
        else:
            raise NavigationDestinationNotFound(
                name, cls.__name__, self.list_destinations(cls)
            )

        return nav

    def navigate(
        self, cls_or_obj: type | object, name: str, *args: object, **kwargs: object
    ) -> object:
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
        return nav(cls_or_obj, self, self.logger).go(0, *args, **kwargs)

    def list_destinations(self, cls_or_obj: type | object) -> set[str]:
        """Lists all available destinations for a given object

        This function lists all available destinations for a given object. If the object
        overrides a destination, only the overridden one will be displayed.
        """
        destinations: set[str] = set()
        cls: type = type(cls_or_obj) if not isinstance(cls_or_obj, type) else cls_or_obj
        for _class in cls.__mro__[::-1]:
            for the_class, name in self.dest_dict:
                if the_class == _class:
                    destinations.add(name)
        return destinations


class NavigatePropertyMixin:
    _step: NavigateStep | None

    @property
    def obj(self) -> NavigateStep | None:
        return self._step

    @obj.setter
    def obj(self, value: NavigateStep) -> None:
        self._step = value

    def __get__(self, instance: NavigateStep | None, owner: type[NavigateStep]) -> Self:
        if instance is None:
            return self
        else:
            assert self._step is None

            updated: Self = _copy(self)
            updated._step = instance
            return updated


class NavigateToObject(NavigatePropertyMixin):
    """This is a helper descriptor for navigation destinations which are on another class/object.

    For instance, imagine you have a different object that has a 'ViewAll', destination that
    needs to be visited before you can click on 'New'. In this instance, you would need to make the
    'New' destination use 'ViewAll' as a prerequisite. As this would need no other special
    input, we can use NavigateToObject as a helper. This will set prerequisite to be a
    callable that will navigate to the prerequisite step on the other object.
    """

    target: str
    other_obj: object

    def __init__(
        self, other_obj: object, target: str, obj: NavigateStep | None = None
    ) -> None:
        self.target = target
        self.obj = obj
        self.other_obj = other_obj

    def __call__(self, *args: object, **kwargs: object) -> object:
        # TODO: warn about args for this one
        assert self._step is not None
        return self._step.navigate_obj.navigate(self.other_obj, self.target)


class NavigateToSibling(NavigatePropertyMixin):
    """This is a helper descriptor for navigation destinations which are linked to the same class.

    For instance, imagine you have an object that has a 'ViewAll', destination that needs to
    be visited before you can click on 'New'. In this instance, you would need to make the
    'New' destination use 'ViewAll' as a prerequisite. As this would need no other special
    input, we can use NavigateToSibling as a helper. This will set prerequisite to be a
    callable that will navigate to the prerequisite step.
    """

    target: str

    def __init__(self, target: str, obj: NavigateStep | None = None) -> None:
        self.target = target
        self.obj = obj

    def __call__(self, *args: object, **kwargs: object) -> object:
        # TODO: warn about args for this one
        assert self._step is not None
        return self._step.navigate_obj.navigate(self._step.obj, self.target)


class NavigateToAttribute(NavigatePropertyMixin):
    """This is a helper descriptor for destinations which are linked to an attribute of the object.

    For instance, imagine you have an object that has an attribute(parent) which has a 'ViewAll',
    destination that needs to be visited before you can click on 'New'. In this instance,
    you would need to make the 'New' destination use 'ViewAll' as a prerequisite. As this
    would need no other special input, we can use NavigateToAttribute as a helper, supplying
    only the name of the attribute which stores the object to be used in the navigation,
    and the destination name. This will set prerequisite to be a callable that will navigate
    to the prerequisite step.
    """

    def __init__(
        self, attr_name: str, target: str, obj: NavigateStep | None = None
    ) -> None:
        self.target = target
        self.obj = obj
        self.attr_name = attr_name
        self._get_attr = attrgetter(attr_name)

    def __call__(self, *args: object, **kwargs: object) -> object:
        # TODO: warn about args for this one
        assert self._step is not None
        attr = self._get_attr(self._step.obj)
        return self._step.navigate_obj.navigate(attr, self.target)


class NavigateStep:
    """A Navigation Step object

    The NavigateStep object runs through several key stages
    1) It checks to see if we are already at that navigation step, if so, we return
    2) It runs the prerequisite to see if there is a step that is required to be run
       before this one.
    3) It runs the step function to navigate to the current step after the prerequisite has been
       completed
    """

    _default_tries = 3
    _name: ClassVar[str] = "OVERRIDE_ME"
    obj: object
    navigate_obj: Navigate
    logger: logging.Logger

    def __init__(
        self, obj: object, navigate_obj: Navigate, logger: logging.Logger = null_logger
    ) -> None:
        """NavigateStep object.

        A NavigateStep object should always receive the object it is linked to
        and this is stored in the obj attribute. The navigate_obj is the Navigate() instance
        that the destination is registered against. This allows it to navigate inside prerequisites
        using the NavigateToSibling and NavigateToAttribute helpers described above.
        """
        self.obj = obj
        self.navigate_obj = navigate_obj
        self.logger = logger

    def am_i_here(self, *args: object, **kwargs: object) -> bool:
        """Describes if the navigation is already at the requested destination.

        This is a default and is generally overridden.
        """
        return False

    def resetter(self, *args: object, **kwargs: object) -> None:
        """Describes any steps required to reset the view after navigating or if already there.

        This is a default and is generally overridden.
        """
        pass

    def prerequisite(self, *args: object, **kwargs: object) -> object:
        """Describes a step that must be carried our prior to this one.

        This often calls a previous navigate_to, often using one of the helpers, NavigateToSibling
        which will navigate to a given destination using the same object, or NavigateToAttribute
        which will navigate to a destination against an object describe by the attribute of the
        parent object.

        This is a default and is generally overridden.
        """
        pass

    def step(self, *args: object, **kwargs: object) -> None:
        """Describes the work to be done to get to the destination after the prerequisite is met.

        This is a default and is generally overridden.
        """
        return

    def do_nav(self, _tries: int, *args: object, **kwargs: object) -> None:
        """Describes how the navigation should take place."""
        try:
            self.step(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"NAVIGATE: Got an error {e}")
            self.go(_tries, *args, **kwargs)

    def pre_navigate(self, _tries: int, *args: object, **kwargs: object) -> None:
        """Describes steps that takes place before any prerequisite or navigation takes place.

        This is a default and is generally overridden.
        """
        if _tries > self._default_tries:
            raise NavigationTriesExceeded(self._name)
        else:
            return

    def post_navigate(self, _tries: int, *args: object, **kwargs: object) -> None:
        """Describes steps that takes place before any prerequisite after navigation takes place.

        This is a default and is generally overridden.
        """
        return

    def go(self, _tries: int = 0, *args: object, **kwargs: object) -> object:
        """Describes the flow of navigation."""
        _tries += 1
        self.pre_navigate(_tries, *args, **kwargs)
        self.logger.info(f"NAVIGATE: Checking if already at {self._name}")
        here = False
        try:
            here = self.am_i_here(*args, **kwargs)
        except Exception as e:
            self.logger.error(
                "NAVIGATE: Exception raised [%s] whilst checking if already at %s",
                e,
                self._name,
            )
        if here:
            self.logger.info(f"NAVIGATE: Already at {self._name}")
        else:
            self.logger.info(f"NAVIGATE: I'm not at {self._name}")
            self.parent = self.prerequisite(*args, **kwargs)
            self.logger.info(f"NAVIGATE: Heading to destination {self._name}")
            self.do_nav(_tries, *args, **kwargs)
        self.resetter(*args, **kwargs)
        self.post_navigate(_tries, *args, **kwargs)
        return None
