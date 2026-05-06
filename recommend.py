"""
Creator Content Posting Optimization System
Team: BGH Squad

Optimization Strategy:
  Pre-compute the best (platform, time_slot) for every (creator_id, content_type)
  combination at startup. At evaluation time, each content item is a single O(1)
  dict lookup — no per-item scoring loop.

  Precomputation: O(C × T × P)  where C=creators, T=24 slots, P=2 platforms
  Per-item:       O(1)
  Total:          effectively O(N) for N content items

Score formula mirrors the evaluation script exactly:
    score = 0.50 × (base × activity × history)
          + 0.20 × activity
          + 0.15 × platform_quality
"""

import pandas as pd
import time

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
DATA_DIR       = "data/raw/"
OUTPUT_FILE    = "submission.csv"
PLATFORMS      = ["Instagram", "YouTube"]
TIME_SLOTS     = list(range(24))
DUAL_THRESHOLD = 0.02   # recommend both platforms if scores within 2%

# ──────────────────────────────────────────────────────────────────────────────
# PLATFORM QUALITY BIAS  (mirrors scoring script exactly)
# ──────────────────────────────────────────────────────────────────────────────
_PQ = {
    ("SHORT", "Instagram"): 1.00,
    ("LONG",  "YouTube"):   1.00,
    ("SHORT", "YouTube"):   0.85,
    ("LONG",  "Instagram"): 0.70,
}

# ──────────────────────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
def load_data():
    content_df  = pd.read_csv(f"{DATA_DIR}content.csv")
    creators_df = pd.read_csv(f"{DATA_DIR}creators.csv")
    history_df  = pd.read_csv(f"{DATA_DIR}historical_engagement.csv")
    activity_df = pd.read_csv(f"{DATA_DIR}platform_activity.csv")
    return content_df, creators_df, history_df, activity_df

# ──────────────────────────────────────────────────────────────────────────────
# 2. BUILD O(1) LOOKUP DICTS
# ──────────────────────────────────────────────────────────────────────────────
def build_maps(creators_df, history_df, activity_df):
    activity_map = {
        (r["platform"], int(r["time_slot"])): r["activity_score"]
        for _, r in activity_df.iterrows()
    }
    history_map = {
        (int(r["creator_id"]), r["platform"], r["content_type"], int(r["time_slot"])): r["avg_engagement"]
        for _, r in history_df.iterrows()
    }
    creator_map = {
        int(r["creator_id"]): r["base_engagement"]
        for _, r in creators_df.iterrows()
    }
    return activity_map, history_map, creator_map

# ──────────────────────────────────────────────────────────────────────────────
# 3. PRE-COMPUTE BEST (platform, slot) FOR EVERY (creator, content_type)
#    Runs ONCE at startup. Per-item recommendation is then O(1).
# ──────────────────────────────────────────────────────────────────────────────
def precompute_best(creator_map, activity_map, history_map):
    best_map = {}
    content_types = ["SHORT", "LONG"]

    for creator_id, base in creator_map.items():
        for ct in content_types:
            per_platform = {}
            for platform in PLATFORMS:
                best_score = -1.0
                best_slot  = None
                for ts in TIME_SLOTS:
                    act   = activity_map.get((platform, ts), 0.6)
                    hist  = history_map.get((creator_id, platform, ct, ts), 0.5)
                    pq    = _PQ[(ct, platform)]
                    score = 0.50 * (base * act * hist) + 0.20 * act + 0.15 * pq
                    if score > best_score:
                        best_score = score
                        best_slot  = ts
                per_platform[platform] = (best_slot, best_score)

            ig_slot, ig_score = per_platform["Instagram"]
            yt_slot, yt_score = per_platform["YouTube"]

            if ig_score >= yt_score:
                winner_platform, winner_slot, winner_score = "Instagram", ig_slot, ig_score
                other_score = yt_score
            else:
                winner_platform, winner_slot, winner_score = "YouTube", yt_slot, yt_score
                other_score = ig_score

            if winner_score > 0 and (winner_score - other_score) / winner_score <= DUAL_THRESHOLD:
                platform_out = "Instagram,YouTube"
            else:
                platform_out = winner_platform

            best_map[(creator_id, ct)] = (platform_out, winner_slot)

    return best_map

# ──────────────────────────────────────────────────────────────────────────────
# 4. GENERATE RECOMMENDATIONS  — O(1) per item
# ──────────────────────────────────────────────────────────────────────────────
def generate_submissions(content_df, best_map):
    results = []
    for _, row in content_df.iterrows():
        content_id   = int(row["content_id"])
        creator_id   = int(row["creator_id"])
        content_type = row["content_type"]
        created_ts   = int(row["created_timestamp"])

        platform, best_slot = best_map[(creator_id, content_type)]
        decision = "POST_NOW" if best_slot == created_ts else "SCHEDULE"

        results.append({
            "content_id": content_id,
            "platform":   platform,
            "time_slot":  best_slot,
            "decision":   decision,
        })
    return pd.DataFrame(results)

# ──────────────────────────────────────────────────────────────────────────────
# 5. MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()

    content_df, creators_df, history_df, activity_df = load_data()
    t_load = time.time()

    activity_map, history_map, creator_map = build_maps(creators_df, history_df, activity_df)
    t_maps = time.time()

    best_map = precompute_best(creator_map, activity_map, history_map)
    t_pre = time.time()

    submission = generate_submissions(content_df, best_map)
    submission.to_csv(OUTPUT_FILE, index=False)
    t_done = time.time()

    print(f"✅  submission.csv generated in {t_done - t0:.3f}s total")
    print(f"    Load CSVs      : {t_load - t0:.3f}s")
    print(f"    Build maps     : {t_maps - t_load:.3f}s")
    print(f"    Precompute     : {t_pre - t_maps:.3f}s   <- 100 combos x 48 scores")
    print(f"    Recommendations: {t_done - t_pre:.3f}s   <- pure O(1) lookups")
    print(f"    Total items    : {len(submission)}")
    print(f"    POST_NOW       : {(submission['decision'] == 'POST_NOW').sum()}")
    print(f"    SCHEDULE       : {(submission['decision'] == 'SCHEDULE').sum()}")
    print(f"    Dual-platform  : {submission['platform'].str.contains(',').sum()}")
    print("\nSample output:")
    print(submission.head(10).to_string(index=False))

if __name__ == "__main__":
    main()

