"""Part B: physics check. TODO 3."""
from __future__ import annotations

G = 9.81


def is_feasible(p: dict) -> bool:
    """TODO 3. False for scenarios no real road user could produce. Reject if ANY of:

    - the lane change needs more sideways grip than the road has: the cosine lane change of 3.5 m over
      p["cutDur"] seconds peaks at a_lat = (pi / cutDur)^2 * 3.5 / 2; reject if a_lat > mu * g;
    - the post-merge braking p["cutBrake"] exceeds mu * g;
    - the pedestrian runs: p["pedV"] > 2.5 m/s;
    - the cut-in speed p["cutV"] is not in (0, 22] m/s.
    mu is p["mu"]. A search that keeps infeasible scenarios reports failures that cannot happen.
    """
    mu = float(p["mu"])
    cut_dur = float(p["cutDur"])
    if cut_dur <= 0:
        return False
    lateral_accel = (3.141592653589793 / cut_dur) ** 2 * 3.5 / 2.0
    if lateral_accel > mu * G:
        return False
    if float(p["cutBrake"]) > mu * G:
        return False
    if float(p["pedV"]) > 2.5:
        return False
    return 0.0 < float(p["cutV"]) <= 22.0
