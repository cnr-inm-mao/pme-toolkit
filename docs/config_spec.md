# Configuration specification

PME-toolkit uses **JSON configuration files** to describe benchmark runs and test cases.

## Scope of the JSON files

Depending on the case, a JSON configuration may specify:

- dataset files;
- variable ranges;
- filtering rules;
- goal-oriented selection settings;
- method settings for PME, PI-PME, or PD-PME;
- output paths and reporting options.

## Practical reference

The most reliable self-contained examples in the repository are:

- `tests/cases/test_glider.json`
- `tests/cases/test_glider_back.json`

Benchmark-style examples are available under `benchmarks/`.

## Recommendation

When creating new cases, start from an existing JSON file already present in the repository and adapt it incrementally.
