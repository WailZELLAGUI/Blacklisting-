"""Synthetic multi-exchange world for Fraudster +1 experiments.

Every actor has a known role, so detection can be scored exactly.
Times are in hours, values in EUR. The model is chain-agnostic
(account-based): a transfer from a seed-cluster address to an exchange
deposit address is credited to one KYC account.

Roles of (seed, account) pairs:
  positives (proceeds handlers): SELF, MULE, FACILITATOR
  secondary target:              ACCOMPLICE
  negatives:                     SERVICE, P2P, VICTIM, DUST, FRAMED
P2P counterparties buy crypto from the fraudster for cash and, like many
ordinary "on/off-ramp" users, sell it again within hours: the hardest
negatives for any behaviour-based indicator.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Optional

import numpy as np

DAY = 24.0
POSITIVE_ROLES = ("SELF", "MULE", "FACILITATOR")
NEGATIVE_ROLES = ("SERVICE", "P2P", "VICTIM", "DUST", "FRAMED", "BAIT", "LANDLORD")
import json as _json, os as _os
_BLTE_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "realdata", "out", "blte_params.json")
BLTE = _json.load(open(_BLTE_PATH)) if _os.path.exists(_BLTE_PATH) else None
# measured blacklisting delays and pay-out lags (realdata/timing/build_timing_params.py)
_TIMING_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "realdata", "out", "timing_params.json")
TIMING = _json.load(open(_TIMING_PATH)) if _os.path.exists(_TIMING_PATH) else None


@dataclass
class Config:
    n_exchanges: int = 5
    n_seeds: int = 40
    horizon_days: float = 70.0
    typologies: tuple = ("T1", "T2", "T3", "T4", "T5")
    # fraud size
    F_median: float = 15_000.0
    F_sigma: float = 1.2
    F_fixed: float | None = None
    F_known_frac: tuple = (1.0, 1.0)      # share of F known to the authority
    k_fixed: int | None = None
    k_range: tuple = (2, 10)
    handler_share: tuple = (0.80, 0.95)   # share of F sent to proceeds handlers
    # identities and linkage
    p_doc: float = 0.2                    # extra registration uses another document
    p_second_key_match: float = 0.95      # name+birth-date key matches
    # tracing
    p_cluster_miss: float = 0.3           # trace stops at the collector; 0.3 = pilot value kept so old results reproduce,
                                          # measured value 0.089 (BigQuery) is set in webapp/configs.py and experiments6.py
    # noise roles
    p_inducement: float = 0.3
    p_ponzi: float = 0.15
    p_dust: float = 0.3
    p_framing: float = 0.1
    framing_share: tuple = (0.05, 0.15)
    p_victim_pays_from_account: float = 0.7
    p_p2p: float = 0.4                    # seed sells part of the proceeds peer-to-peer
    p2p_amount: tuple = (300.0, 3000.0)
    p_ramp: float = 0.25                  # legit users who cash out every deposit quickly
    ramp_exit_mean_h: float = 6.0
    # population
    n_services_per_exchange: int = 4
    n_facilitators: int = 3
    legit_rate_scale: float = 1.0
    legit_amount_scale: float = 1.0
    n_popular_dest: int = 20
    p_popular_dest: float = 0.3
    p_popular_labelled: float = 0.8
    # mule behaviour
    mule_exit_mean_h: float = 4.0
    self_exit_mean_h: float = 12.0
    cover_exit_mean_h: float = 48.0
    p_mule_crypto_exit: float = 0.5
    p_new_mule_account: float = 0.7
    # "what if he keeps only a little in his own account" experiment
    self_share: float | None = None       # share of F sent to his own account (rest untraced)
    self_busy: bool = False               # his own account has normal everyday activity
    # ---- second test: realistic parameters (defaults keep the pilot behaviour) ----
    mule_exit_model: str = "exp"          # "rusi": empirical curve from RUSI/Lloyds mule data
    mule_tail_max_h: float = 168.0        # where the last 15% of mule money leaves (assumption)
    self_exit_model: str = "exp"          # "blte": holding times of 129 real scam addresses
    p_self_busy: float = 0.0              # fraudster's own account is an old, active account
    refund_model: str = "pilot"           # "blte": number and size of victim refunds from real data
    cex_share: float = 1.0                # share of handler money that reaches participating exchanges
    p_collector: float = 0.0              # seed first sends to a collector wallet
    p_collector_range: Optional[Tuple[float, float]] = None   # if set, each world draws its own p_collector, U(lo, hi)
    drip_amount: tuple = (400.0, 400.0)   # T9: monthly payment to the fraudster's own busy account
    drip_months: tuple = (3, 6)
    p_salary: float = 0.0                 # seed pays monthly salaries to 1-3 accomplices
    salary_amount: tuple = (200.0, 800.0)
    p_bait: float = 0.0                   # seed sends monthly baits to 1-3 innocent accounts
    bait_amount: tuple = (100.0, 300.0)
    p_landlord: float = 0.0               # seed pays monthly rent to an innocent landlord
    rent_amount: tuple = (500.0, 1500.0)
    p_plus2: float = 0.0                  # fraudster's own account pays accomplices onwards (+2)
    plus2_share: tuple = (0.10, 0.30)     # share of what it received, sent to 1-3 accomplices
    plus2_spend_share: tuple = (0.05, 0.20)  # ordinary spending to 2-5 innocent customers
    # ---- revision 3: how one fraud's money is split between handlers (no quantitative source) ----
    split_spread: float = 0.2             # handler amounts drawn as weights U(1-s, 1+s) (pilot value 0.2)
    send_window_scale: float = 1.0        # multiplies the 24 h / 48 h / 72 h windows in which handlers are paid
    split_random: bool = False            # draw split_spread and send_window_scale per fraud from the ranges below
    split_spread_range: tuple = (0.0, 0.8)
    send_window_scale_range: tuple = (1.0 / 24.0, 7.0)   # mule window from 1 h to 7 days (log-uniform)
    # ---- blacklisting date and pay-out timing ----
    # "old"   : hand-set (revisions 1-4): collection 2-10 days, tau 0-10 days after it, payouts in one burst
    # "alert" : measured on ScamSniffer seeds (early-warning list): delay and pay-out lags of one real seed
    # "freeze": measured on Tether's USDT blacklist (late freeze): delay; pay-out lags as in "alert"
    blacklist_model: str = "old"

    def with_(self, **kw) -> "Config":
        return replace(self, **kw)


def lognormal(rng, median, sigma, size=None):
    return median * np.exp(sigma * rng.standard_normal(size))


@dataclass
class World:
    cfg: Config
    accounts: dict = field(default_factory=dict)
    identities: dict = field(default_factory=dict)
    events: dict = field(default_factory=lambda: defaultdict(list))
    seeds: dict = field(default_factory=dict)
    truth: dict = field(default_factory=dict)       # (seed, aid) -> role
    services: list = field(default_factory=list)
    facilitators: list = field(default_factory=list)
    popular: list = field(default_factory=list)     # (label, is_labelled)
    plus2: list = field(default_factory=list)       # onward payments from own accounts (+2)
    self_accounts: dict = field(default_factory=dict)  # seed -> list of own-account ids
    p_collector: float = 0.0                           # value used in this world (drawn if cfg.p_collector_range)
    trng: Optional[np.random.Generator] = None         # separate stream for measured timing draws
    _order: int = 0

    # ------------------------------------------------------------ helpers
    def tick(self) -> int:
        self._order += 1
        return self._order

    def add_event(self, aid, t, kind, amount, info=None):
        if 0.0 <= t <= self.cfg.horizon_days * DAY:
            # inflows sort before exits at equal times
            prio = 0 if kind in ("in", "in_seed") else 1
            self.events[aid].append((t, prio, self.tick(), kind, float(amount), info))

    def new_identity(self) -> int:
        iid = len(self.identities)
        self.identities[iid] = {"n_accounts": 0}
        return iid

    def new_account(self, rng, iid, exch, profile, open_t=None, **params) -> int:
        cfg = self.cfg
        aid = len(self.accounts)
        ident = self.identities[iid]
        doc = f"E{iid}" if (ident["n_accounts"] > 0 and rng.random() < cfg.p_doc) else f"D{iid}"
        ident["n_accounts"] += 1
        key2 = f"K{iid}" if rng.random() < cfg.p_second_key_match else f"K?{aid}"
        if open_t is None:
            open_t = -rng.uniform(30, 1000) * DAY
        self.accounts[aid] = dict(aid=aid, iid=iid, exch=exch, profile=profile,
                                  open_t=open_t, pid=doc, key2=key2, **params)
        return aid


# ---------------------------------------------------------------- streams
def _crypto_dest(world, rng, aid, n):
    cfg = world.cfg
    if rng.random() < cfg.p_popular_dest:
        return world.popular[rng.integers(len(world.popular))][0]
    return f"x{aid}_{n}"


def legit_profile(world, rng, aid, prior_scale=5.0, allow_ramp=True):
    cfg = world.cfg
    a = world.accounts[aid]
    med = lognormal(rng, 300 * cfg.legit_amount_scale, 0.7)
    rate = lognormal(rng, 0.02 * cfg.legit_rate_scale, 0.8)
    ramp = allow_ramp and rng.random() < cfg.p_ramp
    a.update(rate=rate, med=med, ramp=ramp,
             prior=float(lognormal(rng, med * (0.3 if ramp else prior_scale), 1.0)))
    H = cfg.horizon_days * DAY
    n_in = rng.poisson(rate * H)
    for t in rng.uniform(0, H, n_in):
        world.add_event(aid, t, "in", lognormal(rng, med, 1.0))
        if ramp:
            world.add_event(aid, t + rng.exponential(cfg.ramp_exit_mean_h), "exit_frac", 0.95, (None, "fiat"))
    if ramp:
        return
    n_out = rng.poisson(rate * rng.uniform(0.7, 1.3) * H)
    for i, t in enumerate(rng.uniform(0, H, n_out)):
        if rng.random() < 0.5:
            info = (_crypto_dest(world, rng, aid, i), "crypto")
        else:
            info = (None, "fiat")
        world.add_event(aid, t, "exit_frac", rng.uniform(0.3, 0.9), info)


def service_profile(world, rng, aid):
    cfg = world.cfg
    a = world.accounts[aid]
    H = cfg.horizon_days * DAY
    rate, med = 1.0 * cfg.legit_rate_scale, 500 * cfg.legit_amount_scale
    settle = float(rng.choice([24.0, 72.0, 168.0]))
    a.update(rate=rate, med=med, prior=rate * med * 12, settle=settle)
    n_in = rng.poisson(rate * H)
    for t in rng.uniform(0, H, n_in):
        world.add_event(aid, t, "in", lognormal(rng, med, 1.0))
    t = rng.uniform(0, settle)
    while t < H:
        world.add_event(aid, t, "exit_frac", 0.95, (None, "fiat"))
        t += settle


def facilitator_profile(world, rng, aid):
    cfg = world.cfg
    a = world.accounts[aid]
    H = cfg.horizon_days * DAY
    rate, med = 0.3, 1500.0
    a.update(rate=rate, med=med, prior=rate * med * 6)
    for t in rng.uniform(0, H, rng.poisson(rate * H)):
        world.add_event(aid, t, "in", lognormal(rng, med, 1.0))
    t = rng.uniform(0, 6.0)
    while t < H:
        world.add_event(aid, t, "exit_frac", 0.95, (f"fac{aid}", "crypto"))
        t += 6.0


def quiet_profile(world, rng, aid):
    """Fresh mule or fraudster-owned account: almost no own activity."""
    a = world.accounts[aid]
    H = world.cfg.horizon_days * DAY
    a.update(rate=0.003, med=100.0, prior=float(rng.uniform(0, 50)))
    for t in rng.uniform(0, H, rng.poisson(0.003 * H)):
        world.add_event(aid, t, "in", lognormal(rng, 100.0, 0.8))


# ---------------------------------------------------------------- builders
def legit_account(world, rng, exch=None, prior_scale=5.0):
    exch = int(rng.integers(world.cfg.n_exchanges)) if exch is None else exch
    iid = world.new_identity()
    aid = world.new_account(rng, iid, exch, "legit")
    legit_profile(world, rng, aid, prior_scale)
    return aid


def seed_transfer(world, s, aid, t, amount, detected=True, counted=True, rng=None):
    world.add_event(aid, t, "in_seed", amount, (s, detected))
    if counted:
        world.seeds[s]["out"] += amount
        world.seeds[s].setdefault("out_ev", []).append((float(t), float(amount)))
    a = world.accounts[aid]
    if a.get("ramp") and rng is not None:      # ramp users cash out every deposit
        world.add_event(aid, t + rng.exponential(world.cfg.ramp_exit_mean_h), "exit_frac", 0.95, (None, "fiat"))


def add_lump(world, s, amount):
    """Money that leaves the seed through routes we do not follow (no time of its own: at evaluation it is
    counted in proportion to the traced payments already made)."""
    world.seeds[s]["out"] += amount
    world.seeds[s]["out_lump"] = world.seeds[s].get("out_lump", 0.0) + amount


def payout_shift(world, s):
    """Hours added to one payment to an exchange account (handler, P2P buyer, accomplice, framed customer):
    measured lag of a payment, minus the seed's first lag (alert / freeze). The measured lags cover every
    deposit account the seed reached, not only handlers. Victim refunds already spread over t_col0..t_col1."""
    lags = world.seeds[s].get("lags")
    if not lags:
        return 0.0
    return (float(lags[int(world.trng.integers(len(lags)))]) - min(lags)) * DAY


def mule_delay(rng, cfg):
    """Hours before a mule moves the money on."""
    if cfg.mule_exit_model == "rusi":
        # RUSI/Lloyds: ~28% within 15 min, +25% within 1 h, <15% left after 24 h
        u = rng.random()
        if u < 0.28:
            return float(rng.uniform(0.0, 0.25))
        if u < 0.53:
            return float(rng.uniform(0.25, 1.0))
        if u < 0.85:
            return float(np.exp(rng.uniform(0.0, np.log(24.0))))
        return float(np.exp(rng.uniform(np.log(24.0), np.log(cfg.mule_tail_max_h))))
    return float(rng.exponential(cfg.mule_exit_mean_h))


def self_delay(rng, cfg):
    """Hours before the fraudster moves money out of his own account."""
    if cfg.self_exit_model == "blte" and BLTE is not None:
        h = BLTE["self_holding_h"]
        return float(h[int(rng.integers(len(h)))] * rng.uniform(0.8, 1.25))
    return float(rng.exponential(cfg.self_exit_mean_h))


def schedule_exit(world, rng, aid, t, kind, s):
    cfg = world.cfg
    if kind == "mule":
        d = mule_delay(rng, cfg)
        info = (f"col{s}", "crypto") if rng.random() < cfg.p_mule_crypto_exit else (None, "fiat")
        world.add_event(aid, t + d, "exit_frac", 1.0, info)
    elif kind == "self":
        d = self_delay(rng, cfg)
        info = (f"own{s}", "crypto") if rng.random() < 0.2 else (None, "fiat")
        world.add_event(aid, t + d, "exit_frac", 0.95, info)


def split_amounts(rng, total, k, spread=0.2):
    w = rng.uniform(1.0 - spread, 1.0 + spread, k)
    return total * w / w.sum()


def make_handler(world, rng, s, kind, exch, role, iid=None, t_ref=0.0, cover=False):
    cfg = world.cfg
    iid = world.new_identity() if iid is None else iid
    if cover:
        aid = world.new_account(rng, iid, exch, "cover")
        legit_profile(world, rng, aid, prior_scale=10.0, allow_ramp=False)
    elif kind == "self" and cfg.p_self_busy > 0 and rng.random() < cfg.p_self_busy:
        aid = world.new_account(rng, iid, exch, "self_busy")
        legit_profile(world, rng, aid, allow_ramp=False)
    elif kind == "mule" and rng.random() > cfg.p_new_mule_account:
        # recruited existing customer
        aid = world.new_account(rng, iid, exch, "mule_old")
        legit_profile(world, rng, aid, allow_ramp=False)
    else:
        open_t = t_ref - rng.uniform(0, 20) * DAY if kind == "mule" else t_ref - rng.uniform(1, 200) * DAY
        aid = world.new_account(rng, iid, exch, kind, open_t=open_t)
        quiet_profile(world, rng, aid)
    world.truth[(s, aid)] = role
    if role == "SELF":
        world.self_accounts.setdefault(s, []).append(aid)
    return aid, iid


def distribute(world, rng, s, typ, budget, t0, k, collector=False):
    cfg = world.cfg
    E = cfg.n_exchanges
    via = typ == "T6" or collector
    if via:
        if typ == "T6":
            typ = str(rng.choice(["T1", "T2", "T3", "T4", "T5"]))
            world.seeds[s]["base_typology"] = typ
        t0 += rng.uniform(24, 72)
        detected = rng.random() >= cfg.p_cluster_miss
        world.seeds[s]["intermediary_detected"] = detected
        if not detected:
            add_lump(world, s, budget)          # one hop to an unclustered address
    else:
        detected = True
    counted = detected

    spread = world.seeds[s].get("split_spread", cfg.split_spread)
    wsc = world.seeds[s].get("send_window_scale", cfg.send_window_scale)

    def send(aid, t, amt, kind):
        t = t + payout_shift(world, s)
        seed_transfer(world, s, aid, t, amt, detected=detected, counted=counted)
        if kind == "cover":
            d = rng.exponential(cfg.cover_exit_mean_h)
            world.add_event(aid, t + d, "exit_amt", 0.95 * amt, (None, "fiat"))
        else:
            schedule_exit(world, rng, aid, t, kind, s)

    if typ == "T1":
        if cfg.self_busy:
            iid = world.new_identity()
            aid = world.new_account(rng, iid, int(rng.integers(E)), "self_busy")
            legit_profile(world, rng, aid, allow_ramp=False)
            world.truth[(s, aid)] = "SELF"
        else:
            aid, _ = make_handler(world, rng, s, "self", int(rng.integers(E)), "SELF", t_ref=t0)
        if cfg.self_share is not None:
            amt = world.seeds[s]["F"] * cfg.self_share
            add_lump(world, s, max(budget - amt, 0.0))   # the rest leaves through untraced routes
            send(aid, t0, amt, "self")
        else:
            send(aid, t0, budget, "self")
    elif typ == "T2":
        aid, _ = make_handler(world, rng, s, "self", int(rng.integers(E)), "SELF", t_ref=t0)
        for amt in split_amounts(rng, budget, k, spread):
            send(aid, t0 + rng.uniform(0, 72 * wsc), amt, "self")
    elif typ == "T3":
        iid = world.new_identity()
        exs = rng.permutation(E)
        accts = {}
        for i, amt in enumerate(split_amounts(rng, budget, k, spread)):
            ex = int(exs[i % E])
            if ex not in accts:
                accts[ex], _ = make_handler(world, rng, s, "self", ex, "SELF", iid=iid, t_ref=t0)
            send(accts[ex], t0 + rng.uniform(0, 48 * wsc), amt, "self")
    elif typ in ("T4", "T5", "T7"):
        one_ex = int(rng.integers(E))
        for amt in split_amounts(rng, budget, k, spread):
            ex = one_ex if typ == "T4" else int(rng.integers(E))
            cover = typ == "T7"
            aid, _ = make_handler(world, rng, s, "mule", ex, "MULE", t_ref=t0, cover=cover)
            send(aid, t0 + rng.uniform(0, 24 * wsc), amt, "cover" if cover else "mule")
    elif typ == "T8":
        fac = world.facilitators[int(rng.integers(len(world.facilitators)))]
        world.truth[(s, fac)] = "FACILITATOR"
        n = int(rng.integers(1, 4))
        for amt in split_amounts(rng, budget, n, spread):
            seed_transfer(world, s, fac, t0 + rng.uniform(0, 72 * wsc) + payout_shift(world, s), amt,
                          detected=detected, counted=counted)
    elif typ == "T9":
        # slow monthly payments to the fraudster's own, normally active account
        iid = world.new_identity()
        aid = world.new_account(rng, iid, int(rng.integers(E)), "self_busy")
        legit_profile(world, rng, aid, allow_ramp=False)
        world.truth[(s, aid)] = "SELF"
        world.self_accounts.setdefault(s, []).append(aid)
        months = int(rng.integers(cfg.drip_months[0], cfg.drip_months[1] + 1))
        total = 0.0
        for m in range(months):
            amt = float(rng.uniform(*cfg.drip_amount))
            total += amt
            send(aid, t0 + m * 30 * DAY + rng.uniform(-2, 2) * DAY, amt, "self")
        if detected:
            add_lump(world, s, max(budget - total, 0.0))   # the rest stays off-exchange
    else:
        raise ValueError(typ)


def generate_world(cfg: Config, rng: np.random.Generator) -> World:
    w = World(cfg)
    H = cfg.horizon_days * DAY
    w.p_collector = cfg.p_collector
    if cfg.p_collector_range:
        # child generator: the main random stream is unchanged, so worlds differ only in this value
        ss = getattr(rng.bit_generator, "seed_seq", None) or rng.bit_generator._seed_seq
        w.p_collector = float(np.random.default_rng(ss.spawn(1)[0]).uniform(*cfg.p_collector_range))
    if cfg.blacklist_model != "old":
        if TIMING is None:
            raise FileNotFoundError(_TIMING_PATH)
        # own stream: the rest of the world (amounts, accounts, patterns) is the same as with "old"
        ss = getattr(rng.bit_generator, "seed_seq", None) or rng.bit_generator._seed_seq
        w.trng = np.random.default_rng(ss.spawn(1)[0])
    w.popular = [(f"pop{i}", rng.random() < cfg.p_popular_labelled) for i in range(cfg.n_popular_dest)]
    for ex in range(cfg.n_exchanges):
        for _ in range(cfg.n_services_per_exchange):
            iid = w.new_identity()
            aid = w.new_account(rng, iid, ex, "service")
            service_profile(w, rng, aid)
            w.services.append(aid)
    if "T8" in cfg.typologies:
        for _ in range(cfg.n_facilitators):
            iid = w.new_identity()
            aid = w.new_account(rng, iid, int(rng.integers(cfg.n_exchanges)), "facilitator")
            facilitator_profile(w, rng, aid)
            w.facilitators.append(aid)

    for s in range(cfg.n_seeds):
        F = cfg.F_fixed if cfg.F_fixed else float(np.clip(lognormal(rng, cfg.F_median, cfg.F_sigma), 500, 2e6))
        typ = str(rng.choice(cfg.typologies))
        k = cfg.k_fixed if cfg.k_fixed else int(rng.integers(cfg.k_range[0], cfg.k_range[1] + 1))
        if typ == "T1":
            k = 1
        t_col0 = rng.uniform(1, 15) * DAY
        t_col1 = t_col0 + rng.uniform(2, 10) * DAY
        t_dist = t_col1 + rng.uniform(0, 5) * DAY
        tau = t_col1 + rng.uniform(0, 10) * DAY
        F_known = F * rng.uniform(*cfg.F_known_frac)
        lags = None
        if cfg.blacklist_model != "old":
            case = TIMING["alert"][int(w.trng.integers(len(TIMING["alert"])))]
            lags = case["lags"]
            if cfg.blacklist_model == "alert":
                delay = case["delay"]
            elif cfg.blacklist_model == "freeze":
                fz = TIMING["freeze"][int(w.trng.integers(len(TIMING["freeze"])))]
                delay = fz["delay"]
                lo, hi = min(lags), max(lags)        # order of the pay-outs from the alert seed, in Tether's window
                lags = [0.0 if hi == lo else (x - lo) / (hi - lo) * fz["out_span"] for x in lags]
            else:
                raise ValueError(cfg.blacklist_model)
            tau = t_col0 + delay * DAY             # t_col0 = first money received by the seed
            t_dist = t_col0 + min(lags) * DAY      # first pay-out; later ones are shifted by payout_shift
            t_col1 = t_col0 + max(lags) * DAY
        w.seeds[s] = dict(seed=s, F=F, F_known=F_known, typology=typ, k=k, tau=tau,
                          t_col0=t_col0, t_col1=t_col1, t_dist=t_dist, out=0.0, lags=lags)
        budget = F * rng.uniform(*cfg.handler_share)
        if cfg.cex_share < 1.0 and typ != "T9":
            add_lump(w, s, budget * (1.0 - cfg.cex_share))   # leaves through routes outside our exchanges
            budget *= cfg.cex_share
        collector = w.p_collector > 0 and rng.random() < w.p_collector
        w.seeds[s]["collector"] = bool(collector)
        if cfg.split_random:
            w.seeds[s]["split_spread"] = float(rng.uniform(*cfg.split_spread_range))
            lo, hi = cfg.send_window_scale_range
            w.seeds[s]["send_window_scale"] = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
        distribute(w, rng, s, typ, budget, t_dist, k, collector=collector)

        # paid accomplices (secondary target): ordinary customers paid for a service
        for _ in range(int(rng.integers(0, 4))):
            aid = legit_account(w, rng)
            w.truth[(s, aid)] = "ACCOMPLICE"
            seed_transfer(w, s, aid, rng.uniform(t_col0, t_dist + 10 * DAY) + payout_shift(w, s), max(200.0, F * rng.uniform(0.01, 0.04)), rng=rng)
        # arm's-length services (shops, processors)
        for _ in range(int(rng.integers(1, 4))):
            aid = w.services[int(rng.integers(len(w.services)))]
            w.truth.setdefault((s, aid), "SERVICE")
            seed_transfer(w, s, aid, rng.uniform(t_col0, H - 5 * DAY), F * rng.uniform(0.005, 0.03))
        # peer-to-peer buyers: pay the fraudster cash, receive crypto, often resell fast
        if rng.random() < cfg.p_p2p:
            for _ in range(int(rng.integers(2, 11))):
                aid = legit_account(w, rng)
                w.accounts[aid]["ramp"] = w.accounts[aid].get("ramp") or rng.random() < 0.5
                w.truth[(s, aid)] = "P2P"
                seed_transfer(w, s, aid, t_dist + rng.uniform(0, 10) * DAY + payout_shift(w, s), rng.uniform(*cfg.p2p_amount), rng=rng)
        # victims who receive money back
        if rng.random() < cfg.p_inducement:
            blte = cfg.refund_model == "blte" and BLTE is not None
            n_v = (BLTE["refunds_per_refunding_seed"][int(rng.integers(len(BLTE["refunds_per_refunding_seed"])))]
                   if blte else int(rng.integers(2, 7)))
            for _ in range(n_v):
                aid = legit_account(w, rng)
                w.truth[(s, aid)] = "VICTIM"
                tp = rng.uniform(t_col0, t_col1)
                if rng.random() < cfg.p_victim_pays_from_account:
                    w.add_event(aid, tp, "pay_seed", lognormal(rng, 2000, 0.8), (s, "crypto"))
                t_ref = tp + rng.uniform(1, 72)
                if blte:
                    rs = BLTE["refund_sigma"]
                    refund = F * rs[int(rng.integers(len(rs)))]
                else:
                    refund = rng.uniform(50, 500)
                seed_transfer(w, s, aid, t_ref, refund, rng=rng)
        if rng.random() < cfg.p_ponzi:
            for _ in range(int(rng.integers(3, 9))):
                aid = legit_account(w, rng)
                w.truth[(s, aid)] = "VICTIM"
                paid = F * rng.uniform(0.02, 0.1)
                tp = rng.uniform(t_col0, t_col1)
                if rng.random() < cfg.p_victim_pays_from_account:
                    w.add_event(aid, tp, "pay_seed", paid, (s, "crypto"))
                seed_transfer(w, s, aid, tp + rng.uniform(2, 10) * DAY, paid * rng.uniform(0.5, 1.5), rng=rng)
        # dust sent to random customers
        if rng.random() < cfg.p_dust:
            for _ in range(int(rng.integers(20, 201))):
                aid = legit_account(w, rng)
                w.truth[(s, aid)] = "DUST"
                seed_transfer(w, s, aid, rng.uniform(t_col0, H - DAY), rng.uniform(1, 20), rng=rng)
        # framing: a large transfer to an innocent customer
        if rng.random() < cfg.p_framing:
            aid = legit_account(w, rng)
            w.truth[(s, aid)] = "FRAMED"
            seed_transfer(w, s, aid, t_dist + rng.uniform(0, 5) * DAY + payout_shift(w, s), F * rng.uniform(*cfg.framing_share), rng=rng)
        # monthly patterns (second test)
        if cfg.p_salary > 0 and rng.random() < cfg.p_salary:
            for _ in range(int(rng.integers(1, 4))):
                aid = legit_account(w, rng)
                w.truth[(s, aid)] = "ACCOMPLICE"
                monthly(w, rng, s, aid, t_dist + rng.uniform(0, 10) * DAY + payout_shift(w, s), cfg.salary_amount)
        if cfg.p_bait > 0 and rng.random() < cfg.p_bait:
            for _ in range(int(rng.integers(1, 4))):
                aid = legit_account(w, rng)
                w.truth[(s, aid)] = "BAIT"
                monthly(w, rng, s, aid, t_dist + rng.uniform(0, 10) * DAY + payout_shift(w, s), cfg.bait_amount)
        if cfg.p_landlord > 0 and rng.random() < cfg.p_landlord:
            aid = legit_account(w, rng)
            w.accounts[aid]["ramp"] = False
            w.truth[(s, aid)] = "LANDLORD"
            monthly(w, rng, s, aid, t_dist + rng.uniform(0, 10) * DAY + payout_shift(w, s), cfg.rent_amount)
        # second step: the fraudster's own account pays accomplices onwards (+2)
        if cfg.p_plus2 > 0 and s in w.self_accounts and rng.random() < cfg.p_plus2:
            plus2_payments(w, rng, s, t_dist)
    return w


def monthly(w, rng, s, aid, t0, amount_range):
    cfg = w.cfg
    months = int(rng.integers(cfg.drip_months[0], cfg.drip_months[1] + 1))
    for m in range(months):
        seed_transfer(w, s, aid, t0 + m * 30 * DAY + rng.uniform(-2, 2) * DAY, rng.uniform(*amount_range), rng=rng)


def plus2_payments(w, rng, s, t_dist):
    cfg = w.cfg
    src = w.self_accounts[s][0]
    received = sum(e[4] for e in w.events[src] if e[3] == "in_seed" and e[5][0] == s)
    if received <= 0:
        return
    sex = w.accounts[src]["exch"]
    t_pay = t_dist + rng.uniform(2, 14) * DAY
    others = [e for e in range(cfg.n_exchanges) if e != sex]

    def pay(dst, amt, role, same):
        t = t_pay + rng.uniform(0, 72)
        w.add_event(src, t, "exit_amt", amt, (f"acct{dst}", "internal" if same else "crypto"))
        w.add_event(dst, t + (0.0 if same else 0.5), "in", amt)
        w.plus2.append(dict(seed=s, src=src, dst=dst, t=t, amount=float(amt), same_ex=bool(same), role=role))

    n_acc = int(rng.integers(1, 4))
    share = rng.uniform(*cfg.plus2_share)
    for _ in range(n_acc):
        same = rng.random() < 0.5
        ex = sex if same else int(rng.choice(others))
        dst = legit_account(w, rng, exch=ex)
        pay(dst, received * share / n_acc, "ACC2", same)
    n_sp = int(rng.integers(2, 6))
    sp = rng.uniform(*cfg.plus2_spend_share)
    for _ in range(n_sp):
        same = rng.random() < 0.5
        ex = sex if same else int(rng.choice(others))
        if rng.random() < 0.5:
            cand = [a for a in w.services if w.accounts[a]["exch"] == ex]
            dst = cand[int(rng.integers(len(cand)))]
        else:
            dst = legit_account(w, rng, exch=ex)
        pay(dst, received * sp / n_sp, "SPEND2", same)
