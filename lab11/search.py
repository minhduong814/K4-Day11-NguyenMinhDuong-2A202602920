"""Part C/D: search for failures with the cross-entropy method. TODO 5; the sampling helpers are given."""
from __future__ import annotations

import math

import numpy as np

from avsim import space


def cem_update(Z, Bn, score, prev: dict, rho: float = 0.1, smooth: float = 0.7, min_std: float = 0.25,
               p_clip=(0.03, 0.97)) -> dict:
    """TODO 5. One cross-entropy step. Keep the elite = the top ceil(rho * n) rows by score (at least 2;
    higher score = more dangerous; on equal scores the earlier row wins, i.e. np.argsort(-score, kind="stable")),
    then return a new proposal dict:

      mean  = smooth * elite mean + (1 - smooth) * prev["mean"]           (per continuous coordinate)
      std   = max(min_std, smooth * elite std + (1 - smooth) * prev["std"])
      p_bin = clip(smooth * elite frequency + (1 - smooth) * prev["p_bin"], *p_clip)  (per binary coordinate)
      level = the lowest score inside the elite (how dangerous the elite already is)

    Why the floors: a std that collapses to 0 or a probability of exactly 0/1 makes importance weights explode."""
    Z = np.asarray(Z)
    Bn = np.asarray(Bn)
    score = np.asarray(score)
    if Z.shape[0] == 0 or Bn.shape[0] != Z.shape[0] or score.shape[0] != Z.shape[0]:
        raise ValueError("Z, Bn, and score must contain the same non-zero number of rows")
    n_elite = max(2, int(math.ceil(rho * Z.shape[0])))
    n_elite = min(n_elite, Z.shape[0])
    elite = np.argsort(-score, kind="stable")[:n_elite]
    mean = smooth * Z[elite].mean(axis=0) + (1.0 - smooth) * prev["mean"]
    std = np.maximum(min_std, smooth * Z[elite].std(axis=0) + (1.0 - smooth) * prev["std"])
    freq = Bn[elite].mean(axis=0)
    p_bin = np.clip(smooth * freq + (1.0 - smooth) * prev["p_bin"], *p_clip)
    return dict(mean=mean, std=std, p_bin=p_bin, level=float(score[elite[-1]]))


# ---------------------------------------------------------------- given

def natural_proposal(nat: space.Natural) -> dict:
    return dict(mean=np.zeros(space.D), std=np.ones(space.D), p_bin=nat.p_bin.copy(), level=-math.inf)


def proposal_sample(prop, n, rng):
    Z = prop["mean"] + prop["std"] * rng.standard_normal((n, space.D))
    Bn = (rng.random((n, space.B)) < prop["p_bin"]).astype(int)
    return Z, Bn


def proposal_logpdf(prop, Z, Bn):
    lz = (-0.5 * np.sum(((Z - prop["mean"]) / prop["std"]) ** 2, 1) - np.sum(np.log(prop["std"]))
          - 0.5 * space.D * math.log(2 * math.pi))
    lb = np.sum(Bn * np.log(prop["p_bin"]) + (1 - Bn) * np.log1p(-prop["p_bin"]), 1)
    return lz + lb


def mixture_sample(prop, nat: space.Natural, n, rng, beta=0.2):
    """Draw n rows from the defensive mixture (1 - beta) * proposal + beta * natural."""
    Z, Bn = proposal_sample(prop, n, rng)
    m = rng.random(n) < beta
    Zn, Bnn = nat.sample(int(m.sum()), rng)
    Z[m], Bn[m] = Zn, Bnn
    return Z, Bn
