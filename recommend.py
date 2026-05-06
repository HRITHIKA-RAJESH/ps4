"""
Creator Content Posting Optimization System
Team: [Your Team Name]
Approach: Joint greedy optimization of platform + time_slot using
          engagement scoring: base_engagement * activity_score * avg_engagement
          with soft platform quality bias.
"""

import pandas as pd
import time

# ──────────────────────────────────────────────
# 1. LOAD DATA
# ──────────────────────────────────────────────
content_df   = pd.read_csv("data/raw/content.csv")
creators_df  = pd.read_csv("data/raw/creators.csv")
history_df   = pd.read_csv("data/raw/historical_engagement.csv")
activity_df  = pd.read_csv("data/raw/platform_activity.csv")

# ──────────────────────────────────────────────
# 2. BUILD FAST LOOKUP DICTIONARIES
# ──────────────────────────────────────────────

# activity[(platform, time_slot)] = score
activity_map = {
    (row["platform"], row["time_slot"]): row["activity_score"]
    for _, row in activity_df.iterrows()
}

# history[(creator_id, platform, content_type, time_slot)] = avg_engagement
history_map = {
    (row["creator_id"], row["platform"], row["content_type"], row["time_slot"]): row["avg_engagement"]
    for _, row in history_df.iterrows()
}

# creator[creator_id] = base_engagement
creator_map = {
    row["creator_id"]: row["base_engagement"]
    for _, row in creators_df.iterrows()
}

PLATFORMS   = ["Instagram", "YouTube"]
TIME_SLOTS  = list(range(24))

# ──────────────────────────────────────────────
# 3. PLATFORM QUALITY BIAS (soft, 15% of score)
# ──────────────────────────────────────────────
def platform_quality(content_type, platform):
    if content_type == "SHORT" and platform == "Instagram":
        return 1.0
    elif content_type == "LONG" and platform == "YouTube":
        return 1.0
    elif content_type == "SHORT" and platform == "YouTube":
        return 0.85
    else:  # LONG on Instagram
        return 0.70

# ──────────────────────────────────────────────
# 4. SCORE A SINGLE (platform, time_slot) COMBO
# ──────────────────────────────────────────────
def compute_score(creator_id, content_type, platform, time_slot):
    base  = creator_map.get(creator_id, 1.0)
    act   = activity_map.get((platform, time_slot), 0.6)
    hist  = history_map.get((creator_id, platform, content_type, time_slot), 0.5)
    pq    = platform_quality(content_type, platform)

    # Combined score matching evaluation formula weights
    engagement = base * act * hist         # 50% weight in final eval
    timing     = act                       # 20% weight
    plat_score = pq                        # 15% weight

    # Weighted combo (efficiency is runtime, not per-item)
    combined = 0.50 * engagement + 0.20 * timing + 0.15 * plat_score
    return combined

# ──────────────────────────────────────────────
# 5. GENERATE RECOMMENDATIONS
# ──────────────────────────────────────────────
start_time = time.time()

results = []

for _, row in content_df.iterrows():
    content_id       = row["content_id"]
    creator_id       = row["creator_id"]
    content_type     = row["content_type"]
    created_ts       = row["created_timestamp"]

    best_score    = -1
    best_platform = None
    best_slot     = None

    # Joint optimization: try all platform × time_slot combos
    for platform in PLATFORMS:
        for ts in TIME_SLOTS:
            score = compute_score(creator_id, content_type, platform, ts)
            # Deterministic tie-breaking: prefer lower time_slot, then Instagram
            if score > best_score:
                best_score    = score
                best_platform = platform
                best_slot     = ts

    # Scheduling decision
    # POST_NOW if optimal slot is current hour or already past and within 1h
    if best_slot == created_ts:
        decision = "POST_NOW"
    else:
        decision = "SCHEDULE"

    results.append({
        "content_id": content_id,
        "platform":   best_platform,
        "time_slot":  best_slot,
        "decision":   decision
    })

# ──────────────────────────────────────────────
# 6. SAVE SUBMISSION
# ──────────────────────────────────────────────
submission = pd.DataFrame(results)
submission.to_csv("submission.csv", index=False)

elapsed = time.time() - start_time
print(f"✅ submission.csv generated in {elapsed:.3f}s")
print(f"   Total items: {len(submission)}")
print(f"   POST_NOW: {(submission['decision']=='POST_NOW').sum()}")
print(f"   SCHEDULE: {(submission['decision']=='SCHEDULE').sum()}")
print("\nSample output:")
print(submission.head(10).to_string())