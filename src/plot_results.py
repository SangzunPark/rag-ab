import sqlite3
from pathlib import Path
import math
import matplotlib.pyplot as plt

DB_PATH = Path("experiments") / "events.db"
OUT_PATH = Path("experiments") / "ab_results.png"

#  DB 기준 실험명
UI_EXPERIMENT = "topk_ab"
OFFLINE_EXPERIMENT = "topk_ab_offline_k2_k4"

def fetch_rows():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Latency는 UI + offline 둘 다 포함(분리 가능)
    cur.execute(
        """
        SELECT experiment, variant, latency_ms, user_vote
        FROM events
        WHERE experiment IN (?, ?)
        """,
        (UI_EXPERIMENT, OFFLINE_EXPERIMENT),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def main():
    rows = fetch_rows()

    # latency: variant별 모든 latency
    lat = {"A": [], "B": []}

    # votes: UI experiment에서만 집계
    votes = {"A": {"up": 0, "down": 0}, "B": {"up": 0, "down": 0}}

    for experiment, variant, latency_ms, user_vote in rows:
        if variant in lat and latency_ms is not None:
            lat[variant].append(latency_ms)

        if experiment == UI_EXPERIMENT and variant in votes:
            if user_vote == "up":
                votes[variant]["up"] += 1
            elif user_vote == "down":
                votes[variant]["down"] += 1

    # Up rate 계산
    up_rate = {}
    vote_n = {}
    for v in ["A", "B"]:
        up = votes[v]["up"]
        down = votes[v]["down"]
        total = up + down
        vote_n[v] = total
        up_rate[v] = (up / total) if total > 0 else math.nan

    # ----- Plot -----
    # 한 이미지(2개 차트)로 저장하기 위해 figsize 크게
    fig = plt.figure(figsize=(10, 6))

    # (1) Vote up rate bar
    ax1 = fig.add_axes([0.08, 0.55, 0.84, 0.38])  # [left, bottom, width, height]
    labels = ["A", "B"]
    rates = [up_rate["A"], up_rate["B"]]
    ax1.bar(labels, rates)
    ax1.set_ylim(0, 1)
    ax1.set_title("Thumbs-up rate (UI only)")
    ax1.set_ylabel("Up rate")

    # 막대 위에 n 표시
    for i, v in enumerate(labels):
        ax1.text(i, rates[i] + 0.02, f"n={vote_n[v]}", ha="center")

    # (2) Latency boxplot
    ax2 = fig.add_axes([0.08, 0.08, 0.84, 0.38])
    data = [lat["A"], lat["B"]]
    ax2.boxplot(data, labels=labels)
    ax2.set_title(f"Latency (ms) - UI + Offline ({UI_EXPERIMENT} + {OFFLINE_EXPERIMENT})")
    ax2.set_ylabel("ms")

    # 저장
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=200)
    plt.close(fig)

    print(f"[OK] Saved plot to: {OUT_PATH}")

if __name__ == "__main__":
    main()
