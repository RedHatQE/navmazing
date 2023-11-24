from __future__ import annotations

from _operator import attrgetter
from copy import copy as _copy
import typing

if typing.TYPE_CHECKING:
    from typing_extensions import Self

from ._step import NavigateStep


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
    """deprecated helper descriptor for concrete navigation

    as this can only be used for types and not for instances,
    it's to be avoided in new code

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
    """descriptor for navigation destinations which are linked to the same class.



    this makes it easy to have::
        class MyStep(...):
          prerequisite = NavigateToSibling("ViewAll")

    instead of::
        class MyStep(...):
          def prerequisite(self, *k, **kw):
            return self.navigate_obj.navigate(self.obj, "ViewAll")


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
    """helper descriptor that triggers the navigation to an attribute of the step target


    this makes it easy to have::
        class MyStep(...):
          prerequisite = NavigateToAttribute("parent", "ViewAll")

    instead of::
        class MyStep(...):
          def prerequisite(self, *k, **kw):
            return self.navigate_obj.navigate(self.obj.parent, "ViewAll")

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
