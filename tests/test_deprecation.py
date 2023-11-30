# todo: add deprecations for types and for navigate args
import pytest

import navmazing


def test_navigate_to_class_warns() -> None:
    nav = navmazing.Navigate()

    @nav.register(int, "parse")
    class Step(navmazing.NavigateStep):
        def step(self, *k: object, **kw: object) -> None:
            print(self.obj)

    with pytest.warns(
        DeprecationWarning,
        match="navigation to types like .* is deprecated, please use instances",
    ):
        nav.navigate(int, "parse")


def test_navigate_warns_args():
    nav = navmazing.Navigate()

    @nav.register(int, "parse")
    class Step(navmazing.NavigateStep):
        def step(self, *k: object, **kw: object) -> None:
            print(self.obj)

    with pytest.warns(
        DeprecationWarning,
        match="additional navigation args are deprecated, .* was given\n"
        "use auxiliary classes to register configured locations",
    ):
        nav.navigate(1, "parse", "arg")
