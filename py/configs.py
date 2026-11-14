"""Simulator settings used in the thesis tests (copied from experiments3.py and experiments5.py)."""
from sim import Config

REAL = dict(
    horizon_days=180.0,
    mule_exit_model="rusi",
    self_exit_model="blte",
    p_self_busy=0.5,
    p_new_mule_account=0.25,
    refund_model="blte", p_inducement=0.17,
    cex_share=0.50,             # 14 Nov 2026: Chainalysis (2024) 'over 50 %' of illicit funds end at CEXs; 0.30 and 0.86 tested
    p_new_mule_range=(0.25, 0.50),   # 14 Nov 2026: RUSI 2025 (most mule accounts > 1 year old), FCA 2026 (47.1 % closed in first year)
    p_collector=0.67,           # pilot value, used only when p_collector_range is None
    p_collector_range=(0.267, 0.712),   # BigQuery: share of phishing seeds sending >= 99% .. >= 50% to one address
    p_cluster_miss=0.089,   # measured on our BigQuery data: 26 of 293 phishing seeds, 95% CI 5.8-12.3% (experiments6.py)
)
CAL_CFG = Config(**REAL).with_(p_landlord=0.2)                      # calibration worlds (patterns T1-T5)
TEST_CFG = Config(**REAL, typologies=("T1", "T2", "T3", "T4", "T5", "T7", "T8", "T9"),
                  F_median=30_000, legit_rate_scale=1.5, legit_amount_scale=1.5,
                  p_framing=0.3, p_ramp=0.35, p_p2p=0.5,
                  p_salary=0.3, p_bait=0.2, p_landlord=0.2, p_plus2=0.5)   # test worlds D (pilot split)
TEST3_CFG = TEST_CFG.with_(split_random=True)                       # test worlds E (split drawn per fraud)
