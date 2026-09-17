"""Video helper: what a recorded conversation did, and which policies it cited.

Usage: uv run python show.py 12 15
Not committed; delete it when you're done.
"""
import json, re, sys

POLICY_ID = re.compile(r"\b(cw-[a-z][a-z-]+|store-[a-z][a-z-]*-policy)\b")
KEY = re.compile(r"system check|7 days|overrid|30-day|30 days", re.I)

rows = [json.loads(line) for line in open("hw1-session.jsonl")]
for n in (int(a) for a in sys.argv[1:]):
    r = rows[n - 1]
    cited = sorted(set(POLICY_ID.findall(r["response"])))
    print(f"record {n}  {r['role']} user {r['user_id']}")
    print(f"  requirement    {r['requirement']}   met={r['met_requirement']}   source={r['problem_source']}")
    print(f"  tools called   {[c['name'] for c in r['tool_calls']]}")
    print(f"  policies cited {cited if cited else 'NONE'}")
    for line in r["response"].split("\n"):
        if KEY.search(line):
            print(f"  reason         {line.strip()[:150]}")
            break
    print()
