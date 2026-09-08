import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

if os.path.exists("veritas.db"):
    os.remove("veritas.db")

from main import ingest_starter_datasets, storage

res = ingest_starter_datasets()
print("Ingest result:", res)

recs = storage.get_reconciliations()
types = {}
for r in recs:
    types[r.type] = types.get(r.type, 0) + 1
print("Reconciliation count by type:", types)

for t in ["corroboration", "reconciled", "contradiction", "failure"]:
    matches = [r for r in recs if r.type == t]
    if matches:
        m = matches[0]
        print(f"\n=== Case [{t.upper()}] ===")
        print(f"  Doc A ({m.factA.doc_id} p.{m.factA.page}): {m.factA.object}")
        print(f"  Quote A: \"{m.factA.quote[:80]}...\"")
        print(f"  Doc B ({m.factB.doc_id} p.{m.factB.page}): {m.factB.object}")
        print(f"  Quote B: \"{m.factB.quote[:80]}...\"")
        print(f"  Reasoning: {m.reasoning}")
