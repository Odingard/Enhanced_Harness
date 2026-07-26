"""Attack modules."""

from enhanced_harness.modules.base import Module, get_module, list_modules
from enhanced_harness.modules.m08_secret_exfiltration import M08SecretExfiltration

MODULE_REGISTRY: dict[str, type[Module]] = {
    "M08": M08SecretExfiltration,
}


def load_modules(enabled: list[str]) -> list[Module]:
    mods: list[Module] = []
    for mid in enabled:
        cls = MODULE_REGISTRY.get(mid)
        if cls is None:
            raise KeyError(f"Module not implemented in this build: {mid}")
        mods.append(cls())
    return mods


__all__ = ["Module", "get_module", "list_modules", "load_modules", "MODULE_REGISTRY"]
