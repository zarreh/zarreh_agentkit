"""Versioned prompt files loaded by id.

Every consumer kept prompts as `<prompt_id>.md` files beside a byte-identical
cached loader -- never inline strings in a node or chain, so a prompt can be
diffed, versioned and later optimised without touching code.
"""

from __future__ import annotations

from pathlib import Path


class PromptLoader:
    """`PromptLoader(Path(__file__).parent).load("planner_v1")` reads
    `planner_v1.md`, stripped, once per id."""

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)
        self._cache: dict[str, str] = {}

    def load(self, prompt_id: str) -> str:
        if prompt_id not in self._cache:
            path = self.directory / f"{prompt_id}.md"
            if not path.exists():
                raise FileNotFoundError(f"No prompt file for id {prompt_id!r} at {path}")
            self._cache[prompt_id] = path.read_text().strip()
        return self._cache[prompt_id]

    def cache_clear(self) -> None:
        self._cache.clear()
