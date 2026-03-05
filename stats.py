"""
Statistics about Atlas contracts, for human consumption.
"""

from collections import Counter
from itertools import combinations

import clean

# Only 3-word contracts for all analysis here
contracts_3 = [c for c in clean.translated_contracts if len(c) == 3]
N = len(contracts_3)
words_flat = [w for c in contracts_3 for w in c]
word_counts = Counter(words_flat)
word_p = {w: n / len(words_flat) for w, n in word_counts.items()}


# ── Independence model ────────────────────────────────────────────────────────

target = ('joyful', 'loving', 'free')
p1 = word_p['joyful'] * word_p['loving'] * word_p['free']

print("=== Independence model: P(joyful, loving, free) ===")
print(f"  (Assuming the three words are drawn independently from the overall word distribution)")
print()
for w in target:
    print(f"  P({w}) = {word_p[w]:.2%}  ({word_counts[w]} appearances / {len(words_flat)} total)")
print()
print(f"  P(one person has this contract)  = {p1:.4%}  (~1 in {round(1/p1):,} people)")
print(f"  P(two people both have it)       = {p1**2:.6%}  (~1 in {round(1/p1**2):,} pairs)")
print(f"  Expected count in this dataset ({N} people): {p1*N:.2f}")
print()


# ── Positional analysis ───────────────────────────────────────────────────────

pos_counts = [Counter(c[i] for c in contracts_3) for i in range(3)]

print("=== Most common word at each position ===")
for i, name in enumerate(["1st", "2nd", "3rd"]):
    top5 = pos_counts[i].most_common(5)
    print(f"  {name}: " + ", ".join(f"{w} ({n})" for w, n in top5))
print()

# For each position, find words most over-represented relative to their overall frequency.
# ratio = (actual rate in position) / (overall rate across all positions)
# Under uniform positional distribution, ratio = 1.0 for all words.
print("=== Words with strongest positional preferences (appearing ≥10 times total) ===")
for i, name in enumerate(["1st", "2nd", "3rd"]):
    biases = []
    for w, n in word_counts.items():
        if n < 10:
            continue
        overall_rate = n / len(words_flat)       # = count / (3·N)
        actual_rate  = pos_counts[i][w] / N      # fraction in this position
        ratio = actual_rate / overall_rate        # = 3 · pos_count / total_count
        biases.append((w, ratio, pos_counts[i][w]))
    biases.sort(key=lambda x: -x[1])
    top5 = biases[:5]
    print(f"  {name} slot:  " +
          "   ".join(f"{w} ({r:.1f}×)" for w, r, _ in top5))
print()


# ── Co-occurrence (lift) ──────────────────────────────────────────────────────
# Lift = P(A and B together) / (P(A) × P(B))
# Lift > 1: appear together more than chance; < 1: less than chance.

word_in_contract_n = {w: sum(1 for c in contracts_3 if w in c)
                      for w in word_counts}

pair_counts = Counter()
for c in contracts_3:
    for a, b in combinations(sorted(set(c)), 2):
        pair_counts[(a, b)] += 1

lifts = []
for (a, b), count in pair_counts.items():
    if count < 3:
        continue
    p_a = word_in_contract_n[a] / N
    p_b = word_in_contract_n[b] / N
    p_ab = count / N
    lift = p_ab / (p_a * p_b)
    expected = p_a * p_b * N
    lifts.append(((a, b), lift, count, expected))

lifts.sort(key=lambda x: -x[1])

print("=== Word pairs that go together more than expected ===")
print("    (lift > 1: seen together more than their individual frequencies predict)")
print()
for (a, b), lift, count, expected in lifts[:15]:
    print(f"  {a} + {b}:  {lift:.1f}× expected  "
          f"(seen {count}×, expected {expected:.1f}×)")
print()

# Anti-correlation: require both words ≥20 occurrences and expected co-occurrence ≥5,
# so we're comparing against a meaningful baseline.
print("=== Word pairs that go together less than expected ===")
print("    (among common words: each appears ≥20×, expected co-occurrence ≥5)")
print("    Likely 'substitutes': people who pick one tend not to also pick the other.")
print()
anti = [
    (pair, lift, count, exp)
    for pair, lift, count, exp in lifts
    if word_counts[pair[0]] >= 20 and word_counts[pair[1]] >= 20 and exp >= 5
]
anti.sort(key=lambda x: x[1])
for (a, b), lift, count, expected in anti[:15]:
    print(f"  {a} + {b}:  {lift:.2f}× expected  "
          f"(seen {count}×, expected {expected:.1f}×)")


# ── Tidbit 1: Contract twins ──────────────────────────────────────────────────

contract_counts = Counter(contracts_3)
has_twin = sum(count for count in contract_counts.values() if count >= 2)
freq_dist = Counter(contract_counts.values())

print()
print("=== Tidbit 1: Contract twins ===")
print(f"  {has_twin}/{N} people ({has_twin/N:.1%}) share their exact contract with at least one other person.")
print(f"  Breakdown by how many people share a contract:")
for k in sorted(freq_dist):
    n_contracts = freq_dist[k]
    n_people    = k * n_contracts
    label = "unique" if k == 1 else f"shared by {k} people"
    print(f"    {k}× ({label}): {n_contracts} contracts → {n_people} people")


# ── Tidbit 2: Sworn enemies — compassionate & passionate ──────────────────────
# Among common words (≥20 appearances), find pairs with 0 co-occurrences,
# sorted by how many times we'd expect them to appear together.

common = sorted(w for w, n in word_counts.items() if n >= 20)
sworn_enemies = []
for a, b in combinations(common, 2):
    key = (min(a, b), max(a, b))
    if pair_counts.get(key, 0) == 0:
        expected = word_in_contract_n[a] / N * word_in_contract_n[b] / N * N
        sworn_enemies.append((a, b, word_counts[a], word_counts[b], expected))
sworn_enemies.sort(key=lambda x: -x[4])

print()
print("=== Tidbit 2: 'Sworn enemies' — common words that have NEVER appeared together ===")
print("    (sorted by how many co-occurrences chance would predict)")
print()
for a, b, na, nb, exp in sworn_enemies[:8]:
    print(f"  {a} ({na}×) + {b} ({nb}×):  expected {exp:.1f} co-occurrences, actual 0")


# ── Tidbit 3: Vocabulary concentration & solo words ──────────────────────────

sorted_counts = sorted(word_counts.values(), reverse=True)
total = sum(sorted_counts)
cumulative = 0
for i, c in enumerate(sorted_counts, 1):
    cumulative += c
    if cumulative >= total * 0.5:
        n_for_half = i
        break

solo_words = sorted(w for w, n in word_counts.items() if n == 1)

print()
print("=== Tidbit 3: Vocabulary concentration & solo words ===")
top5 = [w for w, _ in word_counts.most_common(5)]
top5_pct = sum(word_counts[w] for w in top5) / total
print(f"  {len(word_counts)} unique words total, across {len(words_flat)} total word-slots.")
print(f"  Top 5 words ({', '.join(top5)}) fill {top5_pct:.1%} of all slots.")
print(f"  Just {n_for_half} words account for 50% of all appearances.")
print(f"  {len(solo_words)} words have been chosen by exactly one person ever:")
print(f"  {', '.join(solo_words)}")


# ── Tidbit 4: Identity clusters — contracts that far exceed independence ───────

contract_lifts = []
for contract, count in contract_counts.items():
    if count < 3:
        continue
    p_ind = 1.0
    for w in contract:
        p_ind *= word_p[w]
    lift = (count / N) / p_ind
    contract_lifts.append((contract, lift, count, p_ind * N))
contract_lifts.sort(key=lambda x: -x[1])

print()
print("=== Tidbit 4: Identity clusters — contracts appearing far above chance ===")
print("    These combinations recur so often they suggest a shared 'archetype'.")
print()
for contract, lift, count, expected in contract_lifts[:8]:
    print(f"  {count}× {contract}  ({lift:,.0f}× the independent prediction of {expected:.3f})")


# ── Tidbit 5: 'Loving' as universal connector ─────────────────────────────────

word_degree = Counter()
for a, b in pair_counts:
    word_degree[a] += 1
    word_degree[b] += 1

print()
print("=== Tidbit 5: Word connectivity (how many different words each appears alongside) ===")
print()
for w, degree in word_degree.most_common(8):
    pct_contracts = word_in_contract_n[w] / N
    print(f"  {w}: {degree} unique co-words  "
          f"(present in {word_in_contract_n[w]} contracts, {pct_contracts:.1%} of all)")
print()
print("  Least connected words (appearing ≥10× but pairing with fewest others):")
bottom = sorted(
    [(w, word_degree[w]) for w, n in word_counts.items() if n >= 10],
    key=lambda x: x[1]
)
for w, degree in bottom[:6]:
    print(f"  {w}: {degree} unique co-words  (appears {word_counts[w]}× total)")
