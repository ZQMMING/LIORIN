"""Universal Signal Ontology (USO) — frozen in docs/signal_ontology.md v1.0.

Per architecture_decisions_v1.md DECISION-003, the 8 types are MECE across
命理 semantic space. Adding a 9th type requires DECISION-010 / 011.
"""

# 8 Universal Signal types per signal_ontology.md §3
USO_TYPES = frozenset({
    "ACTION",
    "OUTPUT",
    "CONSTRAINT",
    "RESOURCE",
    "SUPPORT",
    "RELATION",
    "REFLECTION",
    "CHANGE",
})

# signal_ontology.md §4.1
POLARITIES = frozenset({"active", "neutral", "restricted"})

# signal_ontology.md §4.2 — string enum, NEVER numeric
STRENGTHS = frozenset({"low", "moderate", "high"})

# DECISION-002: per-layer direction
DIRECTIONS = frozenset({"INCREASE", "STABLE", "DECREASE"})

# signal_ontology.md §7 Cross-Type Relationship Registry (DECISION-003.A).
# These are the ONLY cross-type pairs that may yield PARTIAL.
# Any other pair MUST yield INSUFFICIENT (DECISION-003.A).
ONTOLOGY_RELATIONSHIPS = (
    {
        "signal_a": "OUTPUT",
        "signal_b": "CHANGE",
        "relationship": "SHARED_ACTIVE",
        "allowed_cross_status": "PARTIAL",
        "authority": "SPEC",
    },
    {
        "signal_a": "RESOURCE",
        "signal_b": "SUPPORT",
        "relationship": "SHARED_INFLOW",
        "allowed_cross_status": "PARTIAL",
        "authority": "SPEC",
    },
    {
        "signal_a": "ACTION",
        "signal_b": "CHANGE",
        "relationship": "SHARED_INITIATION",
        "allowed_cross_status": "PARTIAL",
        "authority": "SPEC",
    },
    {
        "signal_a": "CONSTRAINT",
        "signal_b": "REFLECTION",
        "relationship": "SHARED_INWARD",
        "allowed_cross_status": "PARTIAL",
        "authority": "SPEC",
    },
)


def get_relationship(type_a: str, type_b: str) -> dict | None:
    """Look up a pre-registered ontology relationship.

    Per DECISION-003.A, runtime MUST NOT infer relationships.
    Returns None if not pre-registered.
    """
    for r in ONTOLOGY_RELATIONSHIPS:
        if (r["signal_a"] == type_a and r["signal_b"] == type_b) or (
            r["signal_a"] == type_b and r["signal_b"] == type_a
        ):
            return r
    return None
