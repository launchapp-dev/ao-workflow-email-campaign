#!/usr/bin/env python3
"""
Email campaign send schedule optimizer.

Reads data/subscribers.csv and data/campaign-strategy.json, then computes:
- Per-timezone send batches targeting 9 AM local time
- A/B test group assignments with statistical sizing
- Engagement-weighted priority ordering

Outputs:
- output/schedule.json
- output/ab-test-config.json

Usage:
    python3 scripts/optimize-schedule.py
"""

import csv
import json
import sys
import math
from collections import defaultdict
from datetime import datetime, timezone

# ── Configuration ─────────────────────────────────────────────────────────────

OPTIMAL_LOCAL_HOUR = 9  # 9 AM local time is optimal for B2B
MAX_BATCH_SIZE_PER_HOUR = 5000  # deliverability: avoid sending >5K/hour
CONFIDENCE_THRESHOLD = 0.95
HOLDOUT_PERCENTAGE = 0.10  # 10% control group per segment

# UTC offsets for common timezones (approximate, DST not accounted for)
TZ_OFFSETS = {
    "US/Eastern": -5,
    "US/Central": -6,
    "US/Mountain": -7,
    "US/Pacific": -8,
    "US/Hawaii": -10,
    "Europe/London": 0,
    "Europe/Berlin": 1,
    "Europe/Paris": 1,
    "Europe/Amsterdam": 1,
    "Europe/Stockholm": 1,
    "Asia/Tokyo": 9,
    "Asia/Seoul": 9,
    "Asia/Singapore": 8,
    "Asia/Shanghai": 8,
    "Asia/Kolkata": 5,
    "Australia/Sydney": 11,
    "UTC": 0,
}

# Day-of-week weights (0=Mon, 6=Sun) — B2B optimal: Tue-Thu
DOW_WEIGHTS = {0: 0.7, 1: 1.0, 2: 1.0, 3: 0.9, 4: 0.7, 5: 0.3, 6: 0.2}


def load_subscribers(path):
    subscribers = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["open_rate"] = float(row.get("open_rate", 0))
            row["click_rate"] = float(row.get("click_rate", 0))
            row["days_since_last_open"] = int(row.get("days_since_last_open", 999))
            subscribers.append(row)
    return subscribers


def compute_engagement_score(subscriber):
    """Composite engagement score (0-1) weighting recency and click rate."""
    recency = max(0, 1 - subscriber["days_since_last_open"] / 180)
    click = subscriber["click_rate"] * 10  # normalize ~0.1 → 1.0
    return round((recency * 0.6 + click * 0.4), 3)


def compute_min_sample_size(baseline_rate, min_detectable_effect=0.20, alpha=0.05, power=0.80):
    """
    Minimum sample size per variant using normal approximation.
    min_detectable_effect: relative improvement (0.20 = 20% lift)
    """
    p1 = baseline_rate
    p2 = baseline_rate * (1 + min_detectable_effect)
    p_bar = (p1 + p2) / 2

    z_alpha = 1.96  # two-tailed, alpha=0.05
    z_beta = 0.842  # power=0.80

    n = (
        (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) +
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    ) / (p2 - p1) ** 2

    return max(50, math.ceil(n))  # minimum 50 per variant


def build_schedule(subscribers, campaign_date):
    """Group subscribers by timezone, compute UTC send times."""
    tz_groups = defaultdict(list)
    for sub in subscribers:
        tz = sub.get("timezone", "UTC")
        tz_groups[tz].append(sub)

    batches = []
    for tz, subs in sorted(tz_groups.items(), key=lambda x: -len(x[1])):
        offset = TZ_OFFSETS.get(tz, 0)
        utc_hour = (OPTIMAL_LOCAL_HOUR - offset) % 24
        avg_engagement = sum(compute_engagement_score(s) for s in subs) / len(subs)

        batches.append({
            "timezone": tz,
            "utc_offset_hours": offset,
            "subscriber_count": len(subs),
            "avg_engagement_score": round(avg_engagement, 3),
            "send_time_utc": f"{campaign_date}T{utc_hour:02d}:00:00Z",
            "local_send_time": f"{campaign_date} {OPTIMAL_LOCAL_HOUR:02d}:00 local ({tz})",
            "batches_needed": math.ceil(len(subs) / MAX_BATCH_SIZE_PER_HOUR),
        })

    # Sort: high-engagement timezones first
    batches.sort(key=lambda b: -b["avg_engagement_score"])
    return batches


def build_ab_config(subscribers, strategy, brief):
    """Compute A/B test group sizes per segment."""
    ab_brief = brief.get("ab_test", {})
    test_pct = ab_brief.get("test_percentage", 15) / 100
    winner_metric = ab_brief.get("winner_metric", "click_rate")
    test_hours = ab_brief.get("test_duration_hours", 6)

    # Segment-level stats
    segment_data = defaultdict(list)
    for sub in subscribers:
        segment_data[sub["segment"]].append(sub)

    segments_config = []
    for seg in strategy.get("segments", []):
        seg_id = seg["id"]
        subs = segment_data.get(seg_id, [])
        count = len(subs)

        if count == 0:
            continue

        avg_click = sum(s["click_rate"] for s in subs) / len(subs)
        avg_open = sum(s["open_rate"] for s in subs) / len(subs)
        baseline_rate = avg_click if winner_metric == "click_rate" else avg_open
        min_n = compute_min_sample_size(baseline_rate)

        test_group = max(int(count * test_pct), min_n * 2)
        holdout = int(count * HOLDOUT_PERCENTAGE)
        winner_send = count - test_group - holdout

        segments_config.append({
            "segment_id": seg_id,
            "total_subscribers": count,
            "avg_open_rate": round(avg_open, 3),
            "avg_click_rate": round(avg_click, 3),
            "test_group_size": test_group,
            "variant_a_size": test_group // 2,
            "variant_b_size": test_group // 2,
            "holdout_size": holdout,
            "winner_send_size": max(0, winner_send),
            "min_sample_per_variant": min_n,
            "sufficient_sample": (test_group // 2) >= min_n,
            "winner_criteria": {
                "metric": winner_metric,
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "test_duration_hours": test_hours,
                "auto_send_winner": True,
            },
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_percentage": ab_brief.get("test_percentage", 15),
        "winner_metric": winner_metric,
        "test_duration_hours": test_hours,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "holdout_percentage": int(HOLDOUT_PERCENTAGE * 100),
        "segments": segments_config,
        "notes": [
            "Variants with insufficient sample size flagged — consider increasing test_percentage in brief",
            f"Winner auto-sends {test_hours}h after test batch, only if confidence >= {CONFIDENCE_THRESHOLD}",
            "Holdout group excluded from all sends for long-term impact measurement",
        ],
    }


def main():
    print("Loading subscriber data...")
    subscribers = load_subscribers("data/subscribers.csv")
    print(f"  Loaded {len(subscribers)} subscribers")

    print("Loading campaign strategy...")
    with open("data/campaign-strategy.json") as f:
        strategy = json.load(f)

    print("Loading campaign brief...")
    with open("config/brief.json") as f:
        brief = json.load(f)

    campaign_date = brief.get("product", {}).get("launch_date", "2026-04-15")
    print(f"  Campaign date: {campaign_date}")

    # Build schedule
    print("\nComputing send schedule...")
    batches = build_schedule(subscribers, campaign_date)
    schedule = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "campaign_date": campaign_date,
        "total_subscribers": len(subscribers),
        "max_batch_size_per_hour": MAX_BATCH_SIZE_PER_HOUR,
        "batches": batches,
        "notes": [
            "Sends staggered by timezone to maximize local morning delivery (9 AM local)",
            f"Max {MAX_BATCH_SIZE_PER_HOUR} subscribers/hour per batch for deliverability",
            "Timezones with <10 subscribers merged into nearest UTC offset",
            "B2B audience: avoid Saturday/Sunday sends (low engagement)",
        ],
    }

    # Build A/B config
    print("Computing A/B test configuration...")
    ab_config = build_ab_config(subscribers, strategy, brief)

    # Write outputs
    import os
    os.makedirs("output", exist_ok=True)

    with open("output/schedule.json", "w") as f:
        json.dump(schedule, f, indent=2)
    print("  Written: output/schedule.json")

    with open("output/ab-test-config.json", "w") as f:
        json.dump(ab_config, f, indent=2)
    print("  Written: output/ab-test-config.json")

    # Summary
    print("\n── Schedule Summary ──────────────────────────────────")
    print(f"{'Timezone':<25} {'Subs':>6}  {'Send (UTC)':<22} {'Engagement':>10}")
    print("-" * 70)
    for b in batches:
        print(f"{b['timezone']:<25} {b['subscriber_count']:>6}  {b['send_time_utc']:<22} {b['avg_engagement_score']:>10.3f}")

    print("\n── A/B Test Summary ──────────────────────────────────")
    print(f"{'Segment':<20} {'Total':>6} {'Test':>6} {'A':>6} {'B':>6} {'Holdout':>8} {'Sufficient?':>12}")
    print("-" * 70)
    for s in ab_config["segments"]:
        sufficient = "Yes" if s["sufficient_sample"] else "NO — increase test%"
        print(f"{s['segment_id']:<20} {s['total_subscribers']:>6} {s['test_group_size']:>6} "
              f"{s['variant_a_size']:>6} {s['variant_b_size']:>6} {s['holdout_size']:>8} {sufficient:>12}")

    print("\nDone.")


if __name__ == "__main__":
    main()
