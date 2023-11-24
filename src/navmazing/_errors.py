from __future__ import annotations


class NavigationTriesExceeded(Exception):
    """Simple Exception when navigations can't be found"""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"Navigation failed to reach [{self.name}] in the specified tries"


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
        ).format(self.name, self.cls, ", ".join(sorted(self.possibilities)))
