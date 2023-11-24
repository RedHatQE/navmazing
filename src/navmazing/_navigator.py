from __future__ import annotations

import logging
import warnings
from itertools import chain
from typing import Callable

from ._step import NavigateStep
from ._errors import NavigationDestinationNotFound
from ._logging import null_logger as _null_logger


class Navigate:
    dest_dict: dict[tuple[type, str], type[NavigateStep]]
    logger: logging.Logger

    def __init__(self, logger: logging.Logger = _null_logger) -> None:
        """Initializes the destination dictionary for the Navigate object"""
        self.dest_dict = {}
        self.logger = logger

    def register(
        self, cls: type, name: str | None = None
    ) -> Callable[[type[NavigateStep]], type[NavigateStep]]:
        """Decorator that registers a class with an optional name"""

        def f(obj: type[NavigateStep]) -> type[NavigateStep]:
            """
            registers the decorated class as a naviation target and sets its _name
            """
            destination_name: str = name or obj.__name__
            obj._name = destination_name
            self.dest_dict[cls, destination_name] = obj
            return obj

        return f

    def get_class(self, cls_or_obj: type | object, name: str) -> type[NavigateStep]:
        cls: type = type(cls_or_obj) if not isinstance(cls_or_obj, type) else cls_or_obj

        for base in cls.__mro__:
            maybe_step = self.dest_dict.get((base, name))
            if maybe_step is not None:
                return maybe_step
        else:
            raise NavigationDestinationNotFound(
                name, cls.__name__, self.list_destinations(cls)
            )

    def navigate(
        self, cls_or_obj: type | object, name: str, *args: object, **kwargs: object
    ) -> object:
        """performs the navigation

        first the final target navigation step type is searched
        when it is found, it is instantiated for this navigator

        then its go method will be used for doing the actual steps
        """
        if isinstance(cls_or_obj, type):
            warnings.warn(
                f"navigation to types like {cls_or_obj!r} is deprecated,"
                " please use instances",
                category=DeprecationWarning,
                stacklevel=2,
            )

        if args or kwargs:
            args_str = ", ".join(
                chain(
                    map(repr, args),
                    (f"{key}={value!r}" for key, value in kwargs.items()),
                )
            )
            warnings.warn(
                f"additional navigation args are deprecated, ({args_str}) was given\n"
                "use auxiliary classes to register configured locations",
                category=DeprecationWarning,
                stacklevel=2,
            )
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
