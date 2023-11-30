from __future__ import annotations
import logging
from typing import Mapping

import pytest
from navmazing import (
    Navigate,
    NavigateStep,
    NavigationTriesExceeded,
)
from navmazing._shortcuts import (
    NavigateToObject,
    NavigateToSibling,
    NavigateToAttribute,
)
from navmazing._errors import NavigationDestinationNotFound

state: list[str] = []
arg_store: list[str] = []

logger = logging.getLogger("navmazing_null")
for handler in logger.handlers:
    logger.removeHandler(handler)

file_formatter = logging.Formatter("%(asctime)-15s [%(levelname).1s] %(message)s")
file_handler = logging.FileHandler("navmazing.log")
file_handler.setFormatter(file_formatter)

logger.addHandler(file_handler)
logger.setLevel(10)

navigate = Navigate(logger)


class ObjectA:
    name: str
    margs: tuple[object, ...] | None
    kwargs: Mapping[str, object] | None

    def __init__(self, name: str) -> None:
        self.name = name
        self.margs = None
        self.kwargs = None


class ObjectB:
    name: str | type
    parent: object

    def __init__(self, name: str | type, parent: object) -> None:
        self.name = name
        self.parent = parent


class ObjectC:
    name: str
    parent: ObjectB | None

    def __init__(self, name: str, parent: ObjectB | None = None) -> None:
        self.name = name
        self.parent = parent


@navigate.register(ObjectB)
class StepTwoAgain(NavigateStep):
    prerequisite = NavigateToAttribute("parent", "StepOne")

    def step(self, *args: object, **kwargs: object) -> None:
        state.append(self._name)


@navigate.register(ObjectB, "StepTwo")
class StepTwoToo(NavigateStep):
    obj: ObjectB

    def prerequisite(self, *args: object, **kwargs: object) -> None:
        self.navigate_obj.navigate(self.obj.parent, "StepOne")

    def step(self, *args: object, **kwargs: object) -> None:
        state.append(self._name)


@navigate.register(ObjectA, "BadStep")
class BadStep(NavigateStep):
    prerequisite = NavigateToSibling("StepZero")

    def step(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("bad function")


@navigate.register(ObjectA, "BadStepReturn")
class BadStepReturn(NavigateStep):
    prerequisite = NavigateToSibling("StepZero")

    def am_i_here(self, *args: object, **kwargs: object) -> bool:
        raise RuntimeError("bad function")


@navigate.register(ObjectA, "StepOne")
class StepOne(NavigateStep):
    prerequisite = NavigateToSibling("StepZero")

    def step(self, *args: object, **kwargs: object) -> None:
        state.append(self._name)


@navigate.register(ObjectA, "StepZero")
class StepZero(NavigateStep):
    def am_i_here(self, *args: object, **kwargs: object) -> bool:
        return bool(state)

    def step(self, *args: object, **kwargs: object) -> None:
        state.append(self._name)


@navigate.register(ObjectB, "NeedA")
class NeedA(NavigateStep):
    prerequisite = NavigateToObject(ObjectA, "StepOne")

    def step(self, *args: object, **kwargs: object) -> None:
        state.append(self._name)


@navigate.register(ObjectA, "StepZeroArgs")
class StepZeroArgs(NavigateStep):
    obj: ObjectA

    def am_i_here(self, *args: object, **kwargs: object) -> bool:
        return bool(state)

    def step(self, *args: object, **kwargs: object) -> None:
        self.obj.margs = args
        self.obj.kwargs = kwargs


def test_navigation_to_instance() -> None:
    del state[:]
    a = ObjectA("ObjectA")
    b = ObjectB("ObjectB", a)
    navigate.navigate(b, "StepTwo")
    assert state == ["StepZero", "StepOne", "StepTwo"]


def test_navigation_to_class() -> None:
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    navigate.navigate(b, "StepTwo")
    assert state == ["StepZero", "StepOne", "StepTwo"]


def test_navigation_to_non_named_step() -> None:
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    navigate.navigate(b, "StepTwoAgain")
    assert state == ["StepZero", "StepOne", "StepTwoAgain"]


def test_bad_step_exception() -> None:
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    with pytest.raises(NavigationDestinationNotFound):
        navigate.navigate(b, "Weird")


def test_navigate_unknown() -> None:
    with pytest.raises(NavigationDestinationNotFound):
        navigate.navigate("omg", "Wrong")


def test_bad_step_multi() -> None:
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    with pytest.raises(NavigationDestinationNotFound):
        try:
            navigate.navigate(b, "Whoop")
        except NavigationDestinationNotFound as e:
            assert str(e) == (
                "Couldn't find the destination [{}] with the given class [{}] "
                "the following were available [{}]"
            ).format(
                "Whoop",
                "ObjectB",
                ", ".join(sorted(["NeedA", "StepTwo, StepTwoAgain"])),
            )
            raise


def test_bad_object_exception() -> None:
    c = ObjectC("ObjectC")
    with pytest.raises(NavigationDestinationNotFound):
        try:
            navigate.navigate(c, "NotHere")
        except NavigationDestinationNotFound as e:
            assert str(e) == (
                "Couldn't find the destination [{}] with the given class [{}] "
                "the following were available [{}]"
            ).format("NotHere", "ObjectC", "")
            raise


def test_bad_step() -> None:
    del state[:]
    a = ObjectA("ObjectA")
    with pytest.raises(NavigationTriesExceeded):
        try:
            navigate.navigate(a, "BadStep")
        except NavigationTriesExceeded as e:
            assert str(
                e
            ) == "Navigation failed to reach [{}] in the specified tries".format(
                "BadStep"
            )
            raise


def test_no_nav() -> None:
    a = ObjectA
    b = ObjectB(ObjectA, a)
    navigate.navigate(b, "StepTwo")
    assert state == ["StepZero", "StepOne", "StepTwo"]


def test_bad_am_i_here() -> None:
    del state[:]
    a = ObjectA
    navigate.navigate(a, "BadStepReturn")


def test_list_destinations() -> None:
    dests = navigate.list_destinations(ObjectA)
    assert {"StepZero", "BadStepReturn", "BadStep", "StepOne", "StepZeroArgs"} == dests


def test_navigate_to_object() -> None:
    del state[:]
    b = ObjectB("a", "a")
    navigate.navigate(b, "NeedA")
    assert state == ["StepZero", "StepOne", "NeedA"]


def test_navigate_wth_args() -> None:
    del state[:]
    a = ObjectA
    args = (1, 2, 3)
    kwargs = {"a": "A", "b": "B"}
    navigate.navigate(a, "StepZeroArgs", *args, **kwargs)
    assert a.margs == args


def test_get_name() -> None:
    a = ObjectA
    nav = navigate.get_class(a, "BadStep")
    assert nav == BadStep
