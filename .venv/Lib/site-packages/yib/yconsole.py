"""yconsole extends rich.console to provide extra functions."""

import sys
from typing import Any, overload

import rich.console
from rich.console import JustifyMethod, OverflowMethod
from rich.style import Style


class Console(rich.console.Console):
    @overload
    def fatal(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | Style | None = None,
        justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        no_wrap: bool | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        crop: bool = True,
        soft_wrap: bool | None = None,
        new_line_start: bool = False,
    ) -> None: ...
    def fatal(self, *args, **kwargs) -> None:
        """Print the message then exit with code 1."""
        self.print(*args, **kwargs)
        sys.exit(1)

    @overload
    def warning(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | Style | None = None,
        justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        no_wrap: bool | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        crop: bool = True,
        soft_wrap: bool | None = None,
        new_line_start: bool = False,
    ) -> None: ...
    def warning(self, *args, **kwargs) -> None:
        """Print the message prefixed a yellow ``WARNING:``."""
        self.print(*["[yellow]WARNING:[/yellow]", *args], **kwargs)

    @overload
    def error(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | Style | None = None,
        justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        no_wrap: bool | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        crop: bool = True,
        soft_wrap: bool | None = None,
        new_line_start: bool = False,
    ) -> None: ...
    def error(self, *args, **kwargs) -> None:
        """Print the message prefixed a red ``ERROR:``."""
        self.print(*["[red]ERROR:[/red]", *args], **kwargs)
