# Benchmark

Hand-labeled evaluation dataset for the citation verification system.

- `schema.json` — defines the required structure for every example
- `examples/` — individual labeled (claim, citation) examples, one JSON file each
- `scripts/validate_examples.py` — validates all examples against the schema

See `docs/taxonomy.md` for label definitions.

## Construction methodology

Examples are built from real, verified papers pulled from PubMed/arXiv, using
the same method established benchmarks like FEVER and SciFact use:

- **VERIFIED** examples pair a real paper with a claim that accurately reflects it
- **MISATTRIBUTED** examples pair a real, resolvable paper with a claim about
  a different topic or dataset than the paper actually covers
- **MISREPRESENTED** examples pair a real paper with a claim that deliberately
  distorts its magnitude, direction, certainty, or scope
- **FABRICATED** examples use a constructed citation (plausible author name +
  fictitious title) confirmed via search not to resolve to any real publication

Current batch (v0, 8 examples) is sourced from three real papers in the
cross-dataset EEG seizure prediction literature:

- Jemal et al. (2024), _Frontiers in Neuroinformatics_, DOI: 10.3389/fninf.2024.1303380
- Chen et al. (2026), "CG-MambaNet," arXiv:2606.08226
- Li et al. (2025), "STAN," arXiv:2511.02846

More examples, including harder adversarial cases, will be added in subsequent batches.
