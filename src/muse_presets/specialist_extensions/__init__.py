"""Four portable specialist toolkits; no provider or operating-system effects.

`evaluate(skill_id, inputs)` validates bounded JSON, performs the declared
calculation or review and returns new JSON data. The toolkit never treats a
supplied approval flag, receipt or success declaration as authenticated authority.
"""
from __future__ import annotations
from decimal import Context, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_EVEN, localcontext
from .common import bounded_json, require
from .data import schema_evolution, incremental_pipeline, query_plan_review
from .reliability import service_objectives, capacity_planning, incident_triage
from .automation import automation_contract, selector_resilience, effect_reconciliation
from .interface import design_token_audit, interaction_state_coverage

TOOLS = {
    'schema-evolution': schema_evolution,
    'incremental-pipeline': incremental_pipeline,
    'query-plan-review': query_plan_review,
    'service-objectives': service_objectives,
    'capacity-planning': capacity_planning,
    'incident-triage': incident_triage,
    'automation-contract': automation_contract,
    'selector-resilience': selector_resilience,
    'effect-reconciliation': effect_reconciliation,
    'design-token-audit': design_token_audit,
    'interaction-state-coverage': interaction_state_coverage,
}
SPECIALIST_TOOLS = {
    'data-engineer': ('schema-evolution', 'incremental-pipeline', 'query-plan-review'),
    'reliability-engineer': ('service-objectives', 'capacity-planning', 'incident-triage'),
    'automation-engineer': ('automation-contract', 'selector-resilience', 'effect-reconciliation'),
    'product-interface-designer': ('design-token-audit', 'interaction-state-coverage'),
}


def evaluate(skill_id: str, inputs: dict) -> dict:
    require(type(skill_id) is str and skill_id in TOOLS, 'UNKNOWN_SPECIALIST_TOOL')
    require(type(inputs) is dict, 'INPUT_OBJECT_REQUIRED')
    bounded_json(inputs)
    # A host may use different rounding, exponent limits or Decimal traps.
    # Tool results must follow one policy without changing that host context.
    policy = Context(prec=64, rounding=ROUND_HALF_EVEN,
                     Emin=-999999, Emax=999999, capitals=1, clamp=0,
                     flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])
    with localcontext(policy):
        result = TOOLS[skill_id](inputs)
    bounded_json(result)
    return result
