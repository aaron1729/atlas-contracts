"""
What is the probability that two randomly chosen participants share the same contract?

Uses the empirical contract distribution as a stand-in for the true distribution.
P(match) = Σ p_i²  (sum of squared probabilities, i.e. the collision probability)
"""

from collections import Counter

import clean

contracts = clean.translated_contracts
N = len(contracts)
contract_counts = Counter(contracts)

p_same = sum(n * n for n in contract_counts.values()) / (N * N)

print(f"N = {N} contracts ({len(contract_counts)} unique)")
print()
print(f"P(same contract) = {p_same:.4%}")
print()
print("Most common contracts:")
for contract, n in contract_counts.most_common(10):
    print(f"  {n:3d}x  {contract}")
