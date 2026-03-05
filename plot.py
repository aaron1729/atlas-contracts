"""
Two visualizations of Atlas contract word frequencies:
  1. Word cloud (size ∝ frequency)
  2. Bubble chart: x = positional bias (tends first vs last),
                   y = log(frequency),
                   size ∝ frequency
"""

import atexit
import io
import math
import os
import tempfile
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from fontTools.ttLib import TTCollection
from wordcloud import WordCloud

import clean


# ── Font extraction ───────────────────────────────────────────────────────────

def _extract_ttc(path, index):
    """Extract a single face from a TTC into a temp TTF file."""
    ttc = TTCollection(path)
    buf = io.BytesIO()
    ttc[index].save(buf)
    tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
    tmp.write(buf.getvalue())
    tmp.close()
    atexit.register(os.unlink, tmp.name)
    return tmp.name

_PLAYFUL_FONT = _extract_ttc("/System/Library/Fonts/MarkerFelt.ttc", 1)  # Wide


# ── Color palette ─────────────────────────────────────────────────────────────

_PALETTE = [
    "#C62828",  # red
    "#E64A19",  # deep orange
    "#F9A825",  # amber
    "#2E7D32",  # green
    "#00695C",  # teal
    "#00838F",  # cyan
    "#0277BD",  # sky blue
    "#1565C0",  # deep blue
    "#4527A0",  # indigo
    "#6A1B9A",  # purple
    "#AD1457",  # deep pink
    "#E91E63",  # hot pink
]

def _word_color(word, font_size, position, orientation, random_state=None, **kwargs):
    return random_state.choice(_PALETTE)

# ── Data prep ─────────────────────────────────────────────────────────────────

contracts_3 = [c for c in clean.translated_contracts if len(c) == 3]
N = len(contracts_3)
words_flat = [w for c in contracts_3 for w in c]
word_counts = Counter(words_flat)

pos_counts = [Counter(c[i] for c in contracts_3) for i in range(3)]

# Positional bias: expected slot index (0, 1, 2) under observed distribution
# 0 = always first, 2 = always last, 1 = perfectly balanced
def pos_bias(word):
    total = sum(pos_counts[i][word] for i in range(3))
    if total == 0:
        return 1.0
    return sum(i * pos_counts[i][word] for i in range(3)) / total


# ── 1. Word cloud ─────────────────────────────────────────────────────────────

wc = WordCloud(
    width=1600,
    height=900,
    background_color="white",
    color_func=_word_color,
    max_words=200,
    prefer_horizontal=0.8,
    relative_scaling=0.5,   # moderate scaling so rare words still show
    random_state=42,
    font_path=_PLAYFUL_FONT,
).generate_from_frequencies(word_counts)

fig, ax = plt.subplots(figsize=(16, 9))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
ax.set_title("Atlas Contract Words by Frequency", fontsize=22, pad=20, fontweight="bold")
fig.tight_layout()
fig.savefig("wordcloud.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved wordcloud.png")


# ── 2. Word-position chart ────────────────────────────────────────────────────

# Only show words appearing ≥ 3 times (single-use words clutter the chart)
words = [(w, n) for w, n in word_counts.items() if n >= 3]
words.sort(key=lambda x: -x[1])

# Shift positional bias from 0–2 to 1–3 scale
xs = [pos_bias(w) + 1 for w, _ in words]
ys = [math.log(n) for _, n in words]

# Color by frequency tier
def tier_color(n):
    if n >= 100: return "#c0392b"   # red   — top tier
    if n >= 30:  return "#e67e22"   # orange
    if n >= 10:  return "#2980b9"   # blue
    return "#7f8c8d"                # gray  — occasional


def nudge_labels(xs, ys, x_tol=0.12, min_gap=0.10, max_iter=100, max_drift=0.6):
    """Pairwise repulsion nudge, capped so labels can't stray far from true y."""
    display_ys = list(ys)
    n = len(display_ys)
    for _ in range(max_iter):
        changed = False
        for i in range(n):
            for j in range(i + 1, n):
                if abs(xs[i] - xs[j]) > x_tol:
                    continue
                overlap = min_gap - abs(display_ys[i] - display_ys[j])
                if overlap > 0:
                    push = overlap / 2 + 1e-4
                    if display_ys[i] <= display_ys[j]:
                        display_ys[i] -= push
                        display_ys[j] += push
                    else:
                        display_ys[i] += push
                        display_ys[j] -= push
                    changed = True
        if not changed:
            break
    # Cap drift so y-axis limits stay close to the data range
    for i in range(n):
        drift = display_ys[i] - ys[i]
        display_ys[i] = ys[i] + max(min(drift, max_drift), -max_drift)
    return display_ys


label_ys = nudge_labels(xs, ys)

fig, ax = plt.subplots(figsize=(14, 8))

for (w, n), x, ly in zip(words, xs, label_ys):
    ax.text(x, ly, w, ha="center", va="center", fontsize=7, color=tier_color(n))

ax.set_xlabel("Positional preference  ←  tends first · tends last  →", fontsize=12)
ax.set_ylabel("frequency (log scale)", fontsize=12)
ax.set_title("Atlas Contract Words: Frequency × Positional Preference", fontsize=14,
             fontweight="bold")

# Y-axis: show actual frequency values at tick marks
freq_ticks = [3, 5, 10, 20, 50, 100, 200, 442]
ax.set_yticks([math.log(f) for f in freq_ticks])
ax.set_yticklabels([str(f) for f in freq_ticks])

y_lo = min(min(ys), min(label_ys)) - 0.2
y_hi = max(max(ys), max(label_ys)) + 0.2
ax.set_ylim(y_lo, y_hi)

legend_items = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#c0392b",
           markersize=12, label="≥100 uses"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#e67e22",
           markersize=10, label="30–99 uses"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#2980b9",
           markersize=8,  label="10–29 uses"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#7f8c8d",
           markersize=6,  label="3–9 uses"),
]
ax.legend(handles=legend_items, loc="upper right", fontsize=9)
ax.set_xlim(0.9, 3.1)
ax.set_xticks([1, 2, 3])
ax.set_xticklabels(["1st", "2nd", "3rd"])
ax.text(0.92, y_lo + 0.05, "← tends to come first", fontsize=8, color="gray")
ax.text(3.08, y_lo + 0.05, "tends to come last →", fontsize=8, color="gray", ha="right")

fig.tight_layout()
fig.savefig("bubble.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved bubble.png")
