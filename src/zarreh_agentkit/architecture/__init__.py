"""Shipped import-linter contracts, so a written convention is checked in CI."""

from importlib import resources


def contracts_text() -> str:
    """Contents of the bundled `importlinter_contracts.toml`."""
    resource = resources.files("zarreh_agentkit.architecture") / "importlinter_contracts.toml"
    return resource.read_text(encoding="utf-8")
