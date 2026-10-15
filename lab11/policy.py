"""Part E: choose a policy honestly. TODO 10."""
from __future__ import annotations


def choose_policy(table: list[dict], baseline_progress: float, max_loss: float = 0.05):
    """TODO 10. table rows: dict(policy=..., fail_hi=upper 95% bound of the failure rate on the TRAIN sample,
    progress=mean distance on the natural progress sample). Return the row with the lowest fail_hi among rows that
    keep at least (1 - max_loss) of the baseline's progress; break ties by higher progress. None if no row qualifies.

    Ranking by the UPPER bound, not the point estimate, stops you picking a policy that only looks safe
    because its few test crashes happened not to be drawn."""
    if baseline_progress <= 0:
        return None
    minimum = (1.0 - max_loss) * baseline_progress
    eligible = [row for row in table if row["progress"] >= minimum]
    if not eligible:
        return None
    return min(eligible, key=lambda row: (row["fail_hi"], -row["progress"]))
