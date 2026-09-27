# XEO Audit Product Spec

Last updated: 2026-09-27

## Product Intent

XEO Audit is not meant to be only a classic technical SEO checker. The product
should explain whether a website is easy to crawl, index, interpret, summarize,
and cite by search engines and language-model based answer systems.

## Demo Scope

The current public demo is intentionally limited:

- single URL input;
- no user account;
- compact crawl sample;
- HTML report rendered in browser;
- PDF export through browser print;
- no lead form for now.

## XEO Dimensions

The product should make these dimensions explicit in the report:

- Crawlability: can bots discover and fetch the sampled pages?
- Indexability: are robots/canonical/status signals coherent?
- Semantic clarity: are titles, headings, descriptions, structured data, and
  internal anchors understandable?
- Entity/context readiness: can a language model infer what the site/page is
  about from visible and structured signals?
- Performance accessibility: is performance data available and acceptable?
- Evidence quality: each recommendation should point to observed evidence, not
  generic advice.

## Current Scoring Model

Each category starts at 100.

- critical issue: -15
- high issue: -10
- medium issue: -5
- low issue: -2
- info: 0

Repeated issues are grouped by finding type and capped by severity inside the
category. This avoids an automatic zero when the same problem appears on many
sampled pages.

Current group caps:

- critical: max -30 per issue type
- high: max -20 per issue type
- medium: max -15 per issue type
- low: max -6 per issue type
- info: 0

The overall score is the rounded average of the category scores observed in the
audit. This prevents a site with generally strong categories from receiving an
overall failing grade just because the same medium issue repeats across many
sampled URLs.

The grade is derived from the final score:

- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: below 60

## Score Interpretation

A score such as `15/100, F` means the sampled pages triggered severe or repeated
deductions under the current rubric. It does not mean the business, brand, or
website has "zero value". It means the demo audit found enough technical or
semantic blockers to classify the sample as high risk.

## Known Gaps

- The XEO model is still weighted mostly toward technical SEO evidence.
- Language-model specific signals are measured only with first-pass
  deterministic heuristics, not yet with provider-backed semantic validation.
- No competitor-calibration baseline has been documented yet.
- No formal PRD file was present before this spec; this document is now the
  working product contract until a fuller PRD replaces it.

## Next Required Product Work

- Expand XEO-specific evidence beyond first-pass heuristics: entity extraction,
  structured facts validation, answerability scoring, and citation readiness.
- Create a calibration set comparing this tool with at least one external audit
  tool across the same URLs.
