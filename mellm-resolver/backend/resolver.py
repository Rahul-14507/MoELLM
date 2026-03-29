# backend/resolver.py

from dataclasses import dataclass, field
from typing import Any
from models_config import MODELS

TASK_LABELS = {
    "rag": "RAG / Document Retrieval",
    "code": "Code Generation",
    "reasoning": "Multi-step Reasoning",
    "creative": "Creative Generation",
    "summarize": "Summarization",
}

@dataclass
class Conflict:
    severity: str           # "hard" | "soft"
    dimension: str          # e.g. "latency", "task_fit", "privacy"
    description: str
    affected_model: str
    penalty: float

@dataclass
class DimensionScore:
    name: str
    raw_score: float        # model's capability on this dimension (1-10)
    weight: float           # user-configured priority weight (0-10)
    weighted_score: float
    color: str

@dataclass
class ResolutionResult:
    winner_id: str
    winner_name: str
    confidence: float
    preference_honoured: bool
    user_preferred_id: str
    conflicts: list[Conflict]
    dimension_scores: list[DimensionScore]
    verdict: str
    all_scores: dict[str, float]


DIMENSION_COLORS = {
    "Accuracy":        "#378ADD",
    "Speed":           "#1D9E75",
    "Cost efficiency": "#639922",
    "Privacy":         "#7F77DD",
}

# Hard penalty values
PENALTY_LATENCY_PER_TIER  = 35
PENALTY_PRIVACY_CLOUD     = 60
PENALTY_TASK_MISMATCH     = 25
BONUS_USER_PREFERENCE     = 20


def resolve(
    task: str,
    user_preferred_model: str,
    max_latency_tier: int,       # 1–5
    max_cost_tier: int,          # 1–5  (maps to actual $ elsewhere)
    privacy_required: bool,
    weight_accuracy: float,
    weight_speed: float,
    weight_cost: float,
    weight_privacy: float,
) -> ResolutionResult:

    conflicts: list[Conflict] = []
    raw_scores: dict[str, float] = {}

    for model_id, m in MODELS.items():
        score = (
            m["accuracy"]        * weight_accuracy +
            m["speed"]           * weight_speed +
            m["cost_efficiency"] * weight_cost +
            m["privacy"]         * weight_privacy
        )

        penalty = 0.0
        local_conflicts = []

        # Hard constraint: latency
        if m["latency_tier"] > max_latency_tier:
            over = m["latency_tier"] - max_latency_tier
            p = PENALTY_LATENCY_PER_TIER * over
            penalty += p
            local_conflicts.append(Conflict(
                severity="hard",
                dimension="latency",
                description=f"{m['display_name']} latency tier ({m['latency_tier']}) exceeds constraint ({max_latency_tier})",
                affected_model=model_id,
                penalty=p,
            ))

        # Hard constraint: privacy
        if privacy_required and m["privacy"] < 7:
            penalty += PENALTY_PRIVACY_CLOUD
            local_conflicts.append(Conflict(
                severity="hard",
                dimension="privacy",
                description=f"{m['display_name']} is cloud-hosted; privacy mode requires local/on-prem routing",
                affected_model=model_id,
                penalty=PENALTY_PRIVACY_CLOUD,
            ))

        # Soft constraint: task mismatch
        if task not in m["best_tasks"]:
            penalty += PENALTY_TASK_MISMATCH
            local_conflicts.append(Conflict(
                severity="soft",
                dimension="task_fit",
                description=f"{m['display_name']} is not optimized for '{TASK_LABELS.get(task, task)}'",
                affected_model=model_id,
                penalty=PENALTY_TASK_MISMATCH,
            ))

        # Preference bonus
        if model_id == user_preferred_model:
            score += BONUS_USER_PREFERENCE

        raw_scores[model_id] = max(0.0, score - penalty)
        conflicts.extend(local_conflicts)

    winner_id = max(raw_scores, key=lambda k: raw_scores[k])
    winner = MODELS[winner_id]
    max_score = max(raw_scores.values()) or 1

    # Confidence: how far ahead is the winner vs second place
    sorted_scores = sorted(raw_scores.values(), reverse=True)
    gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
    confidence = min(98.0, round(55 + (gap / max_score) * 43, 1))

    # Dimension breakdown for winner
    dim_scores = [
        DimensionScore("Accuracy",        winner["accuracy"],        weight_accuracy, winner["accuracy"] * weight_accuracy,        DIMENSION_COLORS["Accuracy"]),
        DimensionScore("Speed",           winner["speed"],           weight_speed,    winner["speed"] * weight_speed,           DIMENSION_COLORS["Speed"]),
        DimensionScore("Cost efficiency", winner["cost_efficiency"], weight_cost,     winner["cost_efficiency"] * weight_cost,  DIMENSION_COLORS["Cost efficiency"]),
        DimensionScore("Privacy",         winner["privacy"],         weight_privacy,  winner["privacy"] * weight_privacy,       DIMENSION_COLORS["Privacy"]),
    ]
    dim_scores.sort(key=lambda d: d.weighted_score, reverse=True)
    top_dim = dim_scores[0]

    # Build verdict string
    preference_honoured = winner_id == user_preferred_model
    preferred_name = MODELS.get(user_preferred_model, {}).get("display_name", user_preferred_model)

    override_text = ""
    if not preference_honoured:
        hard_conflicts_for_pref = [c for c in conflicts if c.affected_model == user_preferred_model and c.severity == "hard"]
        reasons = "; ".join(c.dimension for c in hard_conflicts_for_pref) or "constraint violations"
        override_text = (
            f" User preference for {preferred_name} was overridden — "
            f"it failed hard constraints: {reasons}."
        )

    verdict = (
        f"MELLM routed to {winner['display_name']} for this {TASK_LABELS.get(task, task)} request. "
        f"The dominant factor was {top_dim.name} (weighted score {top_dim.weighted_score:.0f}), "
        f"reflecting your priority configuration.{override_text}"
    )

    # Deduplicate conflicts for display (keep only those affecting preferred model or top-severity ones)
    display_conflicts = [c for c in conflicts if c.affected_model == user_preferred_model]
    if not display_conflicts:
        display_conflicts = conflicts[:3]

    return ResolutionResult(
        winner_id=winner_id,
        winner_name=winner["display_name"],
        confidence=confidence,
        preference_honoured=preference_honoured,
        user_preferred_id=user_preferred_model,
        conflicts=display_conflicts,
        dimension_scores=dim_scores,
        verdict=verdict,
        all_scores={k: round(v, 1) for k, v in raw_scores.items()},
    )
