from navmazing import (Navigate, NavigateStep, NavigateToSibling,
    NavigationTriesExceeded, NavigationDestinationNotFound)
import pytest

navigate = Navigate()

state = []


class ObjectA(object):
    def __init__(self, name):
        self.name = name


class ObjectB(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


class ObjectC(object):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent


@navigate.register(ObjectB)
class StepTwoAgain(NavigateStep):
    def prerequisite(self):
        self.navigate_obj.navigate(self.obj.parent, 'StepOne')

    def step(self):
        state.append(self._name)


@navigate.register(ObjectB, 'StepTwo')
class StepTwoToo(NavigateStep):
    def prerequisite(self):
        self.navigate_obj.navigate(self.obj.parent, 'StepOne')

    def step(self):
        state.append(self._name)


@navigate.register(ObjectA, 'BadStep')
class BadStep(NavigateStep):
    prerequisite = NavigateToSibling('StepZero')

    def step(self):
        1 / 0


@navigate.register(ObjectA, 'BadStepReturn')
class BadStepReturn(NavigateStep):
    prerequisite = NavigateToSibling('StepZero')

    def am_i_here(self):
        1 / 0


@navigate.register(ObjectA, 'StepOne')
class StepOne(NavigateStep):
    prerequisite = NavigateToSibling('StepZero')

    def step(self):
        state.append(self._name)


@navigate.register(ObjectA, 'StepZero')
class StepZero(NavigateStep):

    def am_i_here(self):
        return bool(state)

    def step(self):
        state.append(self._name)


def test_navigation_to_instance():
    del state[:]
    a = ObjectA('ObjectA')
    b = ObjectB('ObjectB', a)
    navigate.navigate(b, 'StepTwo')
    assert state == ['StepZero', 'StepOne', 'StepTwo']


def test_navigation_to_class():
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    navigate.navigate(b, 'StepTwo')
    assert state == ['StepZero', 'StepOne', 'StepTwo']


def test_navigation_to_non_named_step():
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    navigate.navigate(b, 'StepTwoAgain')
    assert state == ['StepZero', 'StepOne', 'StepTwoAgain']


def test_bad_step_exception():
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    with pytest.raises(NavigationDestinationNotFound):
        navigate.navigate(b, 'Weird')


def test_bad_object_exception():
    c = ObjectC('ObjectC')
    with pytest.raises(NavigationDestinationNotFound):
        try:
            navigate.navigate(c, 'NotHere')
        except NavigationDestinationNotFound as e:
            print e
            raise


def test_bad_step():
    del state[:]
    a = ObjectA('ObjectA')
    with pytest.raises(NavigationTriesExceeded):
        try:
            navigate.navigate(a, 'BadStep')
        except NavigationTriesExceeded as e:
            print e
            raise


def test_no_nav():
    a = ObjectA
    b = ObjectB(ObjectA, a)
    navigate.navigate(b, 'StepTwo')
    assert state == ['StepZero', 'StepOne', 'StepTwo']


def test_bad_am_i_here():
    del state[:]
    a = ObjectA
    navigate.navigate(a, 'BadStepReturn')


def test_siebling_descriptor_access():
    assert StepOne.prerequisite.obj is None
