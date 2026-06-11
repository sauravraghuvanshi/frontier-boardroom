"""Agent registry — in-memory map of role -> BaseAgent.

Mutable: /agent/{role}/swap-model writes here.

Two parallel registries:
- AGENT_REGISTRY  — debate-mode agents (5-seat boardroom).
- PREP_REGISTRY   — prep-mode agents (1:1 sparring with the human in that seat).

Both reuse the same MODEL_* env overrides; only the system prompt differs.
"""

from __future__ import annotations

from ..config import get_settings
from .base_agent import BaseAgent
from .personas import (
    ceo,
    ceo_prep,
    cfo,
    cfo_prep,
    cmo,
    cmo_prep,
    cto,
    cto_prep,
    legal,
    legal_prep,
)

_PERSONAS = {
    "CEO": ceo.PERSONA,
    "CFO": cfo.PERSONA,
    "CMO": cmo.PERSONA,
    "CTO": cto.PERSONA,
    "Legal": legal.PERSONA,
}

_PREP_PERSONAS = {
    "CEO": ceo_prep.PERSONA,
    "CFO": cfo_prep.PERSONA,
    "CMO": cmo_prep.PERSONA,
    "CTO": cto_prep.PERSONA,
    "Legal": legal_prep.PERSONA,
}


def _build_registry(personas: dict[str, object]) -> dict[str, BaseAgent]:
    # Honor env overrides from Settings.model_registry() (production secrets).
    settings_models = get_settings().model_registry()
    out: dict[str, BaseAgent] = {}
    for role, persona in personas.items():
        persona.model_ref = settings_models.get(role, persona.model_ref)
        out[role] = BaseAgent(persona)
    return out


AGENT_REGISTRY: dict[str, BaseAgent] = _build_registry(_PERSONAS)
PREP_REGISTRY: dict[str, BaseAgent] = _build_registry(_PREP_PERSONAS)
