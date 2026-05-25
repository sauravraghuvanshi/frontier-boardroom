"""Agent registry — in-memory map of role -> BaseAgent.

Mutable: /agent/{role}/swap-model writes here.
"""

from __future__ import annotations

from ..config import get_settings
from .base_agent import BaseAgent
from .personas import ceo, cfo, cmo, cto, legal

_PERSONAS = {
    "CEO": ceo.PERSONA,
    "CFO": cfo.PERSONA,
    "CMO": cmo.PERSONA,
    "CTO": cto.PERSONA,
    "Legal": legal.PERSONA,
}


def _build_registry() -> dict[str, BaseAgent]:
    # Honor env overrides from Settings.model_registry() (production secrets).
    settings_models = get_settings().model_registry()
    out: dict[str, BaseAgent] = {}
    for role, persona in _PERSONAS.items():
        persona.model_ref = settings_models.get(role, persona.model_ref)
        out[role] = BaseAgent(persona)
    return out


AGENT_REGISTRY: dict[str, BaseAgent] = _build_registry()
