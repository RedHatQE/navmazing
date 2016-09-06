from navmazing import Navigate, NavigateStep, NavigateToSibling, NavigationException
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
    with pytest.raises(NavigationException):
        navigate.navigate(b, 'Weird')


def test_bad_object_exception():
    c = ObjectC('ObjectC')
    with pytest.raises(NavigationException):
        navigate.navigate(c, 'NotHere')
