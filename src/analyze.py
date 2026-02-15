import sqlite3
from pathlib import Path
import statistics

DB_PATH = Path("experiments") / "events.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT variant, latency_ms, user_vote
        FROM events
        WHERE experiment IN ('topk_ab', 'topk_ab_offline_k2_k4')
        """
    ).fetchall()
    conn.close()

    # latency, vote 결과 등을 담을 변수 준비
    by_variant = {"A": {"lat": [], "vote_up": 0, "vote_down": 0, "vote_total": 0},
                  "B": {"lat": [], "vote_up": 0, "vote_down": 0, "vote_total": 0}}

    for variant, latency_ms, user_vote in rows:
        if variant not in by_variant:
            continue
        if latency_ms is not None:
            by_variant[variant]["lat"].append(latency_ms)
        if user_vote in ("up", "down"):
            by_variant[variant]["vote_total"] += 1
            if user_vote == "up":
                by_variant[variant]["vote_up"] += 1
            else:
                by_variant[variant]["vote_down"] += 1

    def summarize_lat(xs):
        if not xs:
            return None
        return {
            "n": len(xs),
            "mean_ms": round(statistics.mean(xs), 1),
            "median_ms": round(statistics.median(xs), 1),
        }

    # latency 평균, 미디언
    print("=== Latency Summary ===")
    for v in ["A", "B"]:
        print(v, summarize_lat(by_variant[v]["lat"]))

    # vote 평균, 미디언
    print("\n=== Vote Summary (from UI runs only) ===")
    for v in ["A", "B"]:
        vt = by_variant[v]["vote_total"]
        if vt == 0:
            print(v, {"votes": 0})
        else:
            up = by_variant[v]["vote_up"]
            rate = round(up / vt * 100, 1)
            print(v, {"votes": vt, "up": up, "down": by_variant[v]["vote_down"], "up_rate_%": rate})


if __name__ == "__main__":
    main()