"""Export anonymized contracts to JSONL (one JSON array per line)."""

import json

import clean

with open("contracts_raw.jsonl", "w", encoding="utf-8") as f:
    for contract in clean.all_contracts:
        f.write(json.dumps(list(contract)) + "\n")

with open("contracts_clean.jsonl", "w", encoding="utf-8") as f:
    for contract in clean.translated_contracts:
        f.write(json.dumps(list(contract)) + "\n")

print(f"contracts_raw.jsonl:   {len(clean.all_contracts)} contracts")
print(f"contracts_clean.jsonl: {len(clean.translated_contracts)} contracts")
