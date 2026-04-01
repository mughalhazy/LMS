from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Template:
    template_id: str
    type: str
    channel: str
    variables: list[str] = field(default_factory=list)
    content: str | dict[str, str] = ""

    def render(self, *, payload: dict[str, Any], locale: str | None = None) -> str:
        localized_content = self._resolve_content(locale=locale)
        values = {name: payload.get(name, "") for name in self.variables}
        return localized_content.format(**values)

    def _resolve_content(self, *, locale: str | None = None) -> str:
        if isinstance(self.content, str):
            return self.content
        if not self.content:
            return ""
        if locale and locale in self.content:
            return self.content[locale]
        if "default" in self.content:
            return self.content["default"]
        return next(iter(self.content.values()))
