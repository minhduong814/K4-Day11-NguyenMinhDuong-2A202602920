"""Reproduce a data-derived diagram of hazard.json (not a 3D viewer screenshot)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

from avsim import core, studio
from lab11 import feasible

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parity-fixture", action="store_true", help="also write .review_parity.json for a pure-JS comparison")
    args = parser.parse_args()
    doc = studio.load(ROOT / "hazard.json")
    assert feasible.is_feasible(doc["params"])
    assert studio.hazard_ok(doc["hazards"], doc["params"])
    assert not studio.check_space(doc)
    fix = json.loads((ROOT / "evidence/fix.json").read_text(encoding="utf-8"))
    policy = fix["chosen"]["policy"]
    baseline = core.rollout(doc["params"], policy=doc["policy"], hazards=doc["hazards"])
    chosen = core.rollout(doc["params"], policy=policy, hazards=doc["hazards"])
    avoid, f0, foreknown = studio.oracle_avoids([doc["params"]], baseline, doc["hazards"])
    oracle = core.rollout(doc["params"], hazards=doc["hazards"], brake_from=f0)
    hits = lambda r: [e for e in r.events[0] if "ego" in (e["a"], e["b"])]
    event = hits(baseline)[0]
    f = event["f"]
    summary = {
        "source": "hazard.json; core.rollout; no quick budgets",
        "baseline_events": hits(baseline), "chosen_events": hits(chosen),
        "oracle_events": hits(oracle), "oracle_brake_t": float(f0[0] * core.DT),
        "avoidable": bool(avoid[0]), "avoidable_foreknown": bool(foreknown[0]),
        "chosen_policy": policy,
        "frames": {"time": (np.arange(core.NF) * core.DT).tolist()},
    }
    for name, r in [("baseline", baseline), ("chosen", chosen), ("oracle", oracle)]:
        e = r.F[0, :, core.EGO]
        summary["frames"][name] = e[:, [0, 1, 4]].tolist()
    summary["frames"]["pedestrian"] = baseline.F[0, :, baseline.ids.index("H0"), :2].tolist()
    (ROOT / "evidence/hazard_scene.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    # Road coordinates use the same x and z convention as the simulation.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760">',
           '<rect width="1100" height="760" fill="#f7f9fc"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#172b42} .small{font-size:14px} .title{font-size:23px;font-weight:bold}</style>']
    def text(x, y, s, cls="small"):
        svg.append(f'<text x="{x}" y="{y}" class="{cls}">{escape(str(s))}</text>')
    text(45, 38, "H0: crossing beyond the marked crosswalk", "title")
    text(45, 65, f"Exact scene: x=145 m, v=2.2 m/s, trigger=30 m; baseline contact at {event['t']:.2f} s")
    text(45, 88, "Diagram generated from Python rollout data; not a screenshot of the 3D viewer.")
    X = lambda x: 65 + (x - 100) / 85 * 970
    Z = lambda z: 120 + (z + 10) / 20 * 240
    svg.append(f'<rect x="65" y="{Z(-7)}" width="970" height="{Z(7)-Z(-7)}" fill="#e1e7ee"/>')
    for z in [-7, -3.5, 0, 3.5, 7]:
        svg.append(f'<path d="M65,{Z(z)} H1035" stroke="#94a3b8" stroke-dasharray="8 7"/>')
    for x in range(100, 186, 10):
        text(X(x)-10, 388, str(x))
    text(930, 410, "world x (m)")
    for x in np.arange(120, 124, 0.7):
        svg.append(f'<rect x="{X(x)}" y="{Z(-7)}" width="4" height="{Z(7)-Z(-7)}" fill="white"/>')
    text(X(122)-65, 113, "crosswalk x=122")
    h = baseline.F[0, f, baseline.ids.index("H0")]
    svg.append(f'<path d="M{X(h[0])},{Z(9.2)} L{X(h[0])},{Z(h[1])}" stroke="#c38b13" stroke-width="4" stroke-dasharray="5 4"/>')
    svg.append(f'<circle cx="{X(h[0])}" cy="{Z(h[1])}" r="8" fill="#c38b13"/>')
    text(X(h[0])+12, Z(h[1])-12, "H0 pedestrian")
    colors = [("baseline", baseline, "#d94848", -10), ("chosen", chosen, "#168c82", 0), ("oracle", oracle, "#4877c8", 10)]
    for name, r, color, offset in colors:
        e = r.F[0, f, core.EGO]
        svg.append(f'<rect x="{X(e[0]-2.3)}" y="{Z(e[1]-0.95)+offset}" width="{X(e[0]+2.3)-X(e[0]-2.3)}" height="{Z(0.95)-Z(-0.95)}" rx="4" fill="{color}" fill-opacity="0.68" stroke="{color}" stroke-width="2"/>')
        text(70, 438 + 23 * list(c[0] for c in colors).index(name), f"{name}: x={e[0]:.2f} m; v={e[4]:.2f} m/s at baseline contact")
        svg.append(f'<rect x="48" y="{426 + 23 * list(c[0] for c in colors).index(name)}" width="12" height="12" fill="{color}"/>')
    text(550, 438, f"Oracle brakes at {f0[0]*core.DT:.2f} s: hazard active AND visible.")
    text(550, 461, "Vehicle boxes shifted slightly vertically for readability.")
    text(45, 521, "Ego speed over time (m/s)")
    tx = lambda t: 80 + t / 24 * 955
    vy = lambda v: 687 - v / 14 * 135
    for v in [0, 4, 8, 12]:
        svg.append(f'<path d="M80,{vy(v)} H1035" stroke="#d8e0e8"/>')
        text(50, vy(v)+5, str(v))
    for t in range(0, 25, 4):
        text(tx(t)-5, 713, str(t))
    for name, r, color, offset in colors:
        # Stop baseline/chosen traces at their first failure; post-crash motion is not meaningful progress.
        stop = hits(r)[0]["f"] + 1 if hits(r) else core.NF
        points = " ".join(f"{tx(i*core.DT):.2f},{vy(v):.2f}" for i, v in enumerate(r.F[0, :stop, core.EGO, 4]))
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    svg.append(f'<path d="M{tx(event["t"])},540 V690" stroke="#d94848" stroke-dasharray="4 4"/>')
    text(45, 748, "Source: hazard.json + evidence/fix.json. Reproduce: python make_hazard_figure.py. Time axis: seconds.")
    svg.append('</svg>')
    (ROOT / "evidence/shots/hazard_trajectory.svg").write_text("\n".join(svg), encoding="utf-8")
    # Numeric parity fixture for running the pure JS core without browser automation.
    if args.parity_fixture:
        jobs = [{"params": doc["params"], "policy": pol, "hazards": doc["hazards"], "ego": "planner", "others": "reactive"}
                for pol in [doc["policy"], policy]]
        v = json.loads((ROOT / "evidence/viewer.json").read_text(encoding="utf-8"))
        for run_id in ["B-01", "C-03"]:
            r = next(r for r in v["runs"] if r["id"] == run_id)
            jobs.append(dict(params=r["params"], policy=r["policy"], ego="planner", others="reactive"))
        expected = [core.rollout(j["params"], policy=j["policy"], hazards=j.get("hazards")).scenario(0) for j in jobs]
        (ROOT / ".review_parity.json").write_text(json.dumps(dict(jobs=jobs, expected=expected)), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "frames"}, indent=2))


if __name__ == "__main__":
    main()
