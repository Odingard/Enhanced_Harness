"""Load skills/registry.yaml and resolve runtime skill callables."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Awaitable

import yaml
from pydantic import BaseModel, Field

SkillFn = Callable[..., Awaitable[dict[str, Any]]]


class SkillMeta(BaseModel):
    id: str
    module: str
    name: str
    surfaces: list[str] = Field(default_factory=list)
    requires_flags: list[str] = Field(default_factory=list)
    description: str = ""
    applicability: dict[str, Any] = Field(default_factory=dict)


class SkillRegistry:
    def __init__(self, skills: list[SkillMeta], root: Path) -> None:
        self.skills = {s.id: s for s in skills}
        self.root = root
        self._impls: dict[str, SkillFn] = {}

    def get(self, skill_id: str) -> SkillMeta:
        return self.skills[skill_id]

    def for_module(self, module_id: str) -> list[SkillMeta]:
        return [s for s in self.skills.values() if s.module == module_id]

    def register_impl(self, skill_id: str, fn: SkillFn) -> None:
        if skill_id not in self.skills:
            raise KeyError(f"Unknown skill_id: {skill_id}")
        self._impls[skill_id] = fn

    def impl(self, skill_id: str) -> SkillFn:
        if skill_id not in self._impls:
            raise KeyError(f"No runtime implementation for skill: {skill_id}")
        return self._impls[skill_id]

    def allowed(self, skill_id: str, flag_values: dict[str, bool]) -> bool:
        meta = self.get(skill_id)
        for flag in meta.requires_flags:
            if not flag_values.get(flag, False):
                return False
        return True


def default_registry_path() -> Path:
    # repo-root skills/registry.yaml (sibling of package)
    return Path(__file__).resolve().parents[2] / "skills" / "registry.yaml"


def load_registry(path: str | Path | None = None) -> SkillRegistry:
    p = Path(path) if path else default_registry_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    skills = [SkillMeta.model_validate(s) for s in data.get("skills", [])]
    reg = SkillRegistry(skills, p.parent)
    # Wire runtime implementations
    from enhanced_harness.skills import exfil as exfil_skills

    reg.register_impl("exfil.canary_direct_ask", exfil_skills.canary_direct_ask)
    reg.register_impl(
        "exfil.canary_tool_arg_smuggle", exfil_skills.canary_tool_arg_smuggle
    )
    reg.register_impl("exfil.encoding_base64", exfil_skills.encoding_base64)
    return reg
