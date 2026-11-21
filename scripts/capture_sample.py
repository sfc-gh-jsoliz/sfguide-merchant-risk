"""Capture Sample-mode AI responses from Live runs.

Needs Live env vars (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PRIVATE_KEY_PATH).
Runs every note scope and every suggested question once, against Snowflake,
and writes app/sample/ai.json. Use --resume to skip entries already captured.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import ai  # noqa: E402

out = ai.SAMPLE_AI
cur = json.loads(out.read_text()) if ("--resume" in sys.argv and out.exists()) else {"notes": {}, "ask": {}}
noop = lambda i, s: print("   ", s, flush=True)  # noqa: E731
for scope in ai.SCOPES:
    if scope in cur["notes"]:
        continue
    print("note", scope, flush=True)
    cur["notes"][scope] = ai.run_note_live(scope, noop)
    out.write_text(json.dumps(cur, indent=1, ensure_ascii=False))
for q in ai.QUESTIONS:
    if q in cur["ask"]:
        continue
    print("ask", q, flush=True)
    cur["ask"][q] = ai.ask_live(q, noop)
    out.write_text(json.dumps(cur, indent=1, ensure_ascii=False))
print("done", len(cur["notes"]), "notes,", len(cur["ask"]), "answers")
