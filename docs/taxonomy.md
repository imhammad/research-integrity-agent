# Verification Taxonomy

Every (claim, citation) pair in the benchmark is labeled with exactly one
primary category. This keeps the core classification task clean (4-way),
while an optional subtype field captures richer detail for analysis.

## Primary labels

**VERIFIED**
The cited source is real, resolvable, and accurately supports the claim as stated.

**FABRICATED**
No real paper matches the citation — title, authors, and DOI do not resolve
to an actual publication via CrossRef/Semantic Scholar.

**MISATTRIBUTED**
The source is real and resolvable, but does not discuss the claimed topic or
finding at all. The citation exists; it's just the wrong citation.

**MISREPRESENTED**
The source is real, resolvable, and discusses the relevant topic — but the
claim distorts what the source actually says. See subtypes below.

## Misrepresentation subtypes (metadata field, not separate top-level labels)

- `MAGNITUDE` — claim overstates or understates an effect size / result
- `DIRECTION` — claim reverses the actual direction of a finding
- `CERTAINTY` — claim states as settled fact what the source presented as
  preliminary, tentative, or one possible interpretation
- `SCOPE` — claim generalizes a finding beyond the population, dataset, or
  conditions the source actually studied

## Difficulty tiers

- `easy` — clearly wrong on inspection (e.g. citation doesn't exist at all)
- `medium` — requires reading the abstract to catch
- `hard` — adversarial: correct-looking citation, plausible claim, but subtly
  wrong (e.g. correct paper, correct topic, but effect size inflated 3x)

Hard examples are the ones that actually differentiate a good verification
system from a shallow one — they should be roughly a third of the benchmark.
