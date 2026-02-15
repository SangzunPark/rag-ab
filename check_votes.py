import sqlite3

conn = sqlite3.connect("experiments/events.db")
cur = conn.cursor()

print("=== vote 개수 ===")
cur.execute("SELECT count(*) FROM events WHERE user_vote IS NOT NULL")
print(cur.fetchone())

print("\n=== vote가 있는 행 요약 ===")
cur.execute("""
SELECT experiment, variant, user_vote, count(*)
FROM events
WHERE user_vote IS NOT NULL
GROUP BY experiment, variant, user_vote
ORDER BY count(*) DESC
""")
for row in cur.fetchall():
    print(row)

print("\n=== experiment 목록 ===")
cur.execute("""
SELECT experiment, count(*)
FROM events
GROUP BY experiment
ORDER BY count(*) DESC
""")
for row in cur.fetchall():
    print(row)

conn.close()