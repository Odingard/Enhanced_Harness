"""Module contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from enhanced_harness.models import Hypothesis, Observation, OracleSpec, ProbeResult
from enhanced_harness.scope import Scope
from enhanced_harness.skills.loader import SkillRegistry


class Module(ABC):
    id: str
    name: str
    surfaces: list[str]

    @abstractmethod
    def enumerate_hypotheses(
        self, obs: Observation, scope: Scope, skills: SkillRegistry
    ) -> list[Hypothesis]:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, hyp: Hypothesis, ctx: dict[str, Any]) -> ProbeResult:
        raise NotImplementedError

    @abstractmethod
    def oracle_spec(self, hyp: Hypothesis) -> OracleSpec:
        raise NotImplementedError


def list_modules() -> list[dict[str, str]]:
    from enhanced_harness.modules import MODULE_REGISTRY

    out = []
    for mid, cls in MODULE_REGISTRY.items():
        out.append({"id": mid, "name": cls.name, "surfaces": ",".join(cls.surfaces)})
    return out


def get_module(module_id: str) -> Module:
    from enhanced_harness.modules import MODULE_REGISTRY

    cls = MODULE_REGISTRY[module_id]
    return cls()
