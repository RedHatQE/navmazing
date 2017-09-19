from navmazing import (
    Navigate, NavigateStep, NavigateToSibling,
    NavigationTriesExceeded, NavigationDestinationNotFound, NavigateToAttribute,
    NavigateToObject)
import pytest

navigate = Navigate()

state = []
arg_store = []


class ObjectA(object):
    def __init__(self, name):
        self.name = name
        self.margs = None
        self.kwargs = None


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
    prerequisite = NavigateToAttribute('parent', 'StepOne')

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


@navigate.register(ObjectB, 'NeedA')
class NeedA(NavigateStep):

    prerequisite = NavigateToObject(ObjectA, 'StepOne')

    def step(self):
        state.append(self._name)


@navigate.register(ObjectA, 'StepZeroArgs')
class StepZeroArgs(NavigateStep):

    def am_i_here(self, *args, **kwargs):
        return bool(state)

    def step(self, *args, **kwargs):
        self.obj.margs = list(args)
        self.obj.kwargs = kwargs


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


def test_bad_step_multi():
    del state[:]
    a = ObjectA
    b = ObjectB(ObjectA, a)
    with pytest.raises(NavigationDestinationNotFound):
        try:
            navigate.navigate(b, 'Whoop')
        except NavigationDestinationNotFound as e:
            assert str(e) == ("Couldn't find the destination [{}] with the given class [{}] "
                "the following were available [{}]").format(
                    'Whoop', 'ObjectB', ", ".join(sorted(["NeedA", "StepTwo, StepTwoAgain"])))
            raise


def test_bad_object_exception():
    c = ObjectC('ObjectC')
    with pytest.raises(NavigationDestinationNotFound):
        try:
            navigate.navigate(c, 'NotHere')
        except NavigationDestinationNotFound as e:
            assert str(e) == ("Couldn't find the destination [{}] with the given class [{}] "
                "the following were available [{}]").format(
                    'NotHere', 'ObjectC', "")
            raise


def test_bad_step():
    del state[:]
    a = ObjectA('ObjectA')
    with pytest.raises(NavigationTriesExceeded):
        try:
            navigate.navigate(a, 'BadStep')
        except NavigationTriesExceeded as e:
            assert str(e) == "Navigation failed to reach [{}] in the specificed tries".format(
                'BadStep')
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


def test_list_destinations():
    dests = navigate.list_destinations(ObjectA)
    assert set(['StepZero', 'BadStepReturn', 'BadStep', 'StepOne', 'StepZeroArgs']) == dests


def test_navigate_to_object():
    del state[:]
    b = ObjectB('a', 'a')
    navigate.navigate(b, 'NeedA')
    assert state == ['StepZero', 'StepOne', 'NeedA']


def test_navigate_wth_args():
    del state[:]
    a = ObjectA
    args = [1, 2, 3]
    kwargs = {'a': 'A', 'b': 'B'}
    navigate.navigate(a, 'StepZeroArgs', *args, **kwargs)
    assert a.margs == args


def test_get_name():
    a = ObjectA
    nav = navigate.get_class(a, 'BadStep')
    assert nav == BadStep
