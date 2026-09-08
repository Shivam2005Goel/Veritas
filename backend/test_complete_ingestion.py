import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

if os.path.exists("veritas.db"):
    os.remove("veritas.db")

from main import ingest_starter_datasets, storage

# Test 1: Ingest Delhivery
print("--- Test 1: Ingesting Delhivery Dataset ---")
res_delhivery = ingest_starter_datasets("delhivery")
print("Delhivery Ingestion Result:", res_delhivery)

# Test 2: Ingest India Macroeconomy
print("\n--- Test 2: Ingesting India Macroeconomy Dataset ---")
res_macro = ingest_starter_datasets("india-macroeconomy")
print("Macroeconomy Ingestion Result:", res_macro)

# Overall Stats
facts = storage.get_all_facts()
recs = storage.get_reconciliations()
print(f"\n==========================================")
print(f"Total Unique Facts Stored: {len(facts)}")
print(f"Total Reconciliations Generated: {len(recs)}")
print(f"==========================================")

types = {}
for r in recs:
    types[r.type] = types.get(r.type, 0) + 1
print("Breakdown by Case Type:", types)

print("\n--- Demonstration Case Highlights ---")
for t in ["corroboration", "reconciled", "contradiction", "failure"]:
    matches = [r for r in recs if r.type == t]
    print(f"\n[{t.upper()} CASES: {len(matches)} found]")
    for m in matches[:2]:
        print(f"  • {m.factA.subject} ({m.factA.doc_id} p.{m.factA.page}) vs ({m.factB.doc_id} p.{m.factB.page})")
        print(f"    Fact A: {m.factA.object} | Fact B: {m.factB.object}")
        print(f"    Reasoning: {m.reasoning[:130]}...")
