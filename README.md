# Research Integrity Agent

An automated system for verifying whether citations in academic writing actually
support the claims attached to them — catching fabricated, misattributed, and
misrepresented citations before they reach publication.

## Why this exists

AI writing tools frequently fabricate or misattribute citations. This project
verifies claims against real source papers using a structured extraction →
retrieval → verification pipeline, benchmarked against a hand-built adversarial
dataset.

**Status:** 🚧 In active development (Phase 0: benchmark design)

## Project structure

- `benchmark/` — hand-labeled evaluation dataset + scoring scripts
- `src/` — pipeline source code (extraction, retrieval, verification)
- `docs/` — taxonomy, design notes, architecture

## Roadmap

- [x] Phase 0: Problem definition & benchmark construction
- [ ] Phase 1: Claim & citation extraction
- [ ] Phase 2: Source retrieval & resolution
- [ ] Phase 3: Verification core
- [ ] Phase 4: Agent orchestration
- [ ] Phase 5: Frontend
- [ ] Phase 6: Deployment & write-up
