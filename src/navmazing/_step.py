from __future__ import annotations

import logging
from typing import ClassVar

from . import _navigator
from ._errors import NavigationTriesExceeded
from ._logging import null_logger as _null_logger


class NavigateStep:
    """A Navigation Step object

    A NavigateStep runs through several key stages
    1) validate if the navigation target has been reached and exit early in that case
    2) navigate to the prerequisite
    3) run the step function to go from the prerequisite to the target
    """

    _default_tries = 3
    _name: ClassVar[str] = "OVERRIDE_ME"
    obj: object
    navigate_obj: _navigator.Navigate
    logger: logging.Logger

    def __init__(
        self,
        obj: object,
        navigate_obj: _navigator.Navigate,
        logger: logging.Logger = _null_logger,
    ) -> None:
        """NavigateStep object.

        A NavigateStep object should always receive the object it is linked to
        and this is stored in the obj attribute.
        The navigate_obj is the Navigate() instance
        that the destination is registered against.
        This allows it to navigate inside prerequisites
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
        """steps required to reset the view after navigating or if already there.

        This is a default and is generally overridden.
        """
        pass

    def prerequisite(self, *args: object, **kwargs: object) -> object:
        """Describes a step that must be carried our prior to this one.

        This often calls a previous navigate_to, often using one of the helpers,
        NavigateToSibling which will navigate to a given destination
        using the same object, or NavigateToAttribute which will navigate
        to a destination against an object describe by the attribute of the
        parent object.

        This is a default and is generally overridden.
        """
        pass

    def step(self, *args: object, **kwargs: object) -> None:
        """work to be done to get to the destination after the prerequisite is met.

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
        """steps  before any prerequisite or navigation

        the default implementation just exits after hitting the number of tries
        use this to error when the application under test
        hits a unrecoverable state
        """
        if _tries > self._default_tries:
            raise NavigationTriesExceeded(self._name)
        else:
            return

    def post_navigate(self, _tries: int, *args: object, **kwargs: object) -> None:
        """steps taken after the navigation is complete

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
