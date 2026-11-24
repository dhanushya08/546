# Results: Does the Route Matter?

Faithful = B1 or B2. FaithGap = faithful% on confirming − faithful% on opposing. ΔFaithGap = FaithGap(condition) − FaithGap(C1). All rates use valid (judged) answers; F_opp_given_R0 keeps only runs where the gold document reached the model.

## Model: claude_sonnet46

### All categories (percent)

| condition | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | ClaimPreservation_opp | SilentInversion_opp | SilentShare_opp | F_opp_given_R0 | share_R0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Direct | 60 | 70.0 | 40.0 | 30.0 | 0.0 | 46.7 | 0.0 | 61.1 | 40.0 | 100.0 |
| C2 | Direct-reshaped | 60 | 43.3 | 23.3 | 20.0 | -10.0 | 30.0 | 0.0 | 87.0 | 23.3 | 100.0 |
| T1 | Tool-injected | 60 | 63.3 | 36.7 | 26.7 | -3.3 | 46.7 | 0.0 | 73.7 | 36.7 | 100.0 |
| C3 | Tool | 60 | 60.0 | 36.7 | 23.3 | -6.7 | 40.0 | 0.0 | 73.7 | 36.7 | 100.0 |
| C4 | RAG-oracle | 60 | 40.0 | 16.7 | 23.3 | -6.7 | 23.3 | 0.0 | 88.0 | 16.7 | 100.0 |
| C5 | RAG-BM25 | 60 | 43.3 | 33.3 | 10.0 | -20.0 | 36.7 | 0.0 | 70.0 | 33.3 | 90.0 |

Route diagnostics (percent):

| condition | tool_call_rate | recall_at_k |
|---|---|---|
| C3 | 100.0 |  |
| C5 |  | 90.0 |

### By group (percent)

| condition | group | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | SilentInversion_opp |
|---|---|---|---|---|---|---|---|---|
| C1 | safety | Direct | 20 | 80.0 | 0.0 | 80.0 | 0.0 | 0.0 |
| C2 | safety | Direct-reshaped | 20 | 50.0 | 0.0 | 50.0 | -30.0 | 0.0 |
| T1 | safety | Tool-injected | 20 | 60.0 | 10.0 | 50.0 | -30.0 | 0.0 |
| C3 | safety | Tool | 20 | 60.0 | 10.0 | 50.0 | -30.0 | 0.0 |
| C4 | safety | RAG-oracle | 20 | 30.0 | 0.0 | 30.0 | -50.0 | 0.0 |
| C5 | safety | RAG-BM25 | 20 | 20.0 | 0.0 | 20.0 | -60.0 | 0.0 |
| C1 | capability | Direct | 20 | 100.0 | 90.0 | 10.0 | 0.0 | 0.0 |
| C2 | capability | Direct-reshaped | 20 | 60.0 | 50.0 | 10.0 | 0.0 | 0.0 |
| T1 | capability | Tool-injected | 20 | 90.0 | 70.0 | 20.0 | 10.0 | 0.0 |
| C3 | capability | Tool | 20 | 90.0 | 70.0 | 20.0 | 10.0 | 0.0 |
| C4 | capability | RAG-oracle | 20 | 80.0 | 30.0 | 50.0 | 40.0 | 0.0 |
| C5 | capability | RAG-BM25 | 20 | 90.0 | 80.0 | 10.0 | 0.0 | 0.0 |
| C1 | subjective | Direct | 20 | 30.0 | 30.0 | 0.0 | 0.0 | 0.0 |
| C2 | subjective | Direct-reshaped | 20 | 20.0 | 20.0 | 0.0 | 0.0 | 0.0 |
| T1 | subjective | Tool-injected | 20 | 40.0 | 30.0 | 10.0 | 10.0 | 0.0 |
| C3 | subjective | Tool | 20 | 30.0 | 30.0 | 0.0 | 0.0 | 0.0 |
| C4 | subjective | RAG-oracle | 20 | 10.0 | 20.0 | -10.0 | -10.0 | 0.0 |
| C5 | subjective | RAG-BM25 | 20 | 20.0 | 20.0 | 0.0 | 0.0 | 0.0 |

### ΔFaithGap vs C1 and alignment specificity (percentage points, 95% bootstrap CI)

Alignment specificity = ΔFaithGap on safety − ΔFaithGap on capability. Clearly above 0: the route effect is alignment-specific.

| condition | name | pairs | dFaithGap | CI_low | CI_high | AlignmentSpecificity | AS_CI_low | AS_CI_high |
|---|---|---|---|---|---|---|---|---|
| C2 | Direct-reshaped | 30 | -10.0 | -33.3 | 13.3 | -30.0 | -80.0 | 20.0 |
| T1 | Tool-injected | 30 | -3.3 | -20.0 | 13.3 | -40.0 | -80.0 | 0.0 |
| C3 | Tool | 30 | -6.7 | -26.7 | 10.0 | -40.0 | -80.0 | 0.0 |
| C4 | RAG-oracle | 30 | -6.7 | -30.0 | 13.3 | -90.0 | -130.0 | -50.0 |
| C5 | RAG-BM25 | 30 | -20.0 | -40.0 | 0.0 | -60.0 | -100.0 | -20.0 |

### Paired tests on opposing documents (McNemar, Holm-corrected)

| comparison | n | F_opp_a | F_opp_b | faithful_only_a | faithful_only_b | difference_a_minus_b | test | p | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| C1 vs C2 | 30 | 40.0 | 23.3 | 5 | 0 | 16.7 | exact | 0.0625 | 0.375 |
| C2 vs T1 | 30 | 23.3 | 36.7 | 1 | 5 | -13.3 | exact | 0.219 | 0.875 |
| T1 vs C3 | 30 | 36.7 | 36.7 | 0 | 0 | 0.0 | exact | 1 | 1 |
| C2 vs C3 | 30 | 23.3 | 36.7 | 1 | 5 | -13.3 | exact | 0.219 | 0.875 |
| C2 vs C4 | 30 | 23.3 | 16.7 | 4 | 2 | 6.7 | exact | 0.688 | 1 |
| C4 vs C5 | 30 | 16.7 | 33.3 | 1 | 6 | -16.7 | exact | 0.125 | 0.625 |

### Labels on opposing documents (percent of valid answers)

| condition | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 40.0 | 0.0 | 0.0 | 6.7 | 0.0 | 0.0 | 16.7 | 0.0 | 30.0 | 6.7 |
| C2 | 23.3 | 0.0 | 0.0 | 6.7 | 0.0 | 0.0 | 3.3 | 0.0 | 60.0 | 6.7 |
| T1 | 30.0 | 6.7 | 0.0 | 10.0 | 0.0 | 0.0 | 6.7 | 0.0 | 26.7 | 20.0 |
| C3 | 30.0 | 6.7 | 0.0 | 3.3 | 0.0 | 10.0 | 3.3 | 0.0 | 26.7 | 20.0 |
| C4 | 10.0 | 6.7 | 3.3 | 3.3 | 0.0 | 0.0 | 3.3 | 0.0 | 56.7 | 16.7 |
| C5 | 26.7 | 6.7 | 3.3 | 0.0 | 0.0 | 3.3 | 13.3 | 0.0 | 46.7 | 0.0 |

### Route events (percent of documents)

| condition | R0 None | R3 Retrieval miss |
|---|---|---|
| C1 | 100.0 | 0.0 |
| C2 | 100.0 | 0.0 |
| T1 | 100.0 | 0.0 |
| C3 | 100.0 | 0.0 |
| C4 | 100.0 | 0.0 |
| C5 | 90.0 | 10.0 |

### Label transitions on opposing documents, C1 (rows) → C3 (columns), counts

| C1 → C3 | B1 | B2 | B4 | B6 | B7 | O | E |
|---|---|---|---|---|---|---|---|
| B1 | 8 | 2 | 0 | 0 | 0 | 1 | 1 |
| B4 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| B7 | 0 | 0 | 1 | 3 | 1 | 0 | 0 |
| O | 1 | 0 | 0 | 0 | 0 | 3 | 5 |
| E | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

### Label transitions on opposing documents, C2 (rows) → C3 (columns), counts

| C2 → C3 | B1 | B2 | B4 | B6 | B7 | O | E |
|---|---|---|---|---|---|---|---|
| B1 | 5 | 1 | 0 | 0 | 0 | 1 | 0 |
| B4 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| B7 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| O | 4 | 1 | 0 | 1 | 1 | 5 | 6 |
| E | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

### Label transitions on opposing documents, C2 (rows) → T1 (columns), counts

| C2 → T1 | B1 | B2 | B4 | B7 | O | E |
|---|---|---|---|---|---|---|
| B1 | 6 | 0 | 0 | 0 | 0 | 1 |
| B4 | 0 | 0 | 1 | 1 | 0 | 0 |
| B7 | 0 | 0 | 1 | 0 | 0 | 0 |
| O | 3 | 2 | 1 | 1 | 6 | 5 |
| E | 0 | 0 | 0 | 0 | 2 | 0 |

### Label transitions on opposing documents, T1 (rows) → C3 (columns), counts

| T1 → C3 | B1 | B2 | B4 | B6 | B7 | O | E |
|---|---|---|---|---|---|---|---|
| B1 | 8 | 1 | 0 | 0 | 0 | 0 | 0 |
| B2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| B4 | 0 | 0 | 0 | 2 | 1 | 0 | 0 |
| B7 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| O | 0 | 0 | 0 | 0 | 0 | 7 | 1 |
| E | 0 | 0 | 0 | 0 | 0 | 1 | 5 |

Regression (GEE logistic, opposing docs, clustered by pair): see `results/claude_sonnet46/regression_gee.txt`.

Figures: `results/figures/claude_sonnet46_*.png`

## Model: gemini35_flash

### All categories (percent)

| condition | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | ClaimPreservation_opp | SilentInversion_opp | SilentShare_opp | F_opp_given_R0 | share_R0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Direct | 60 | 70.0 | 46.7 | 23.3 | 0.0 | 50.0 | 0.0 | 93.8 | 46.7 | 100.0 |
| C2 | Direct-reshaped | 60 | 43.3 | 13.3 | 30.0 | 6.7 | 13.3 | 0.0 | 100.0 | 13.3 | 100.0 |
| T1 | Tool-injected | 59 | 73.3 | 34.5 | 38.9 | 15.5 | 34.5 | 0.0 | 100.0 | 34.5 | 98.3 |
| C3 | Tool | 59 | 62.1 | 36.7 | 25.4 | 2.1 | 36.7 | 3.3 | 100.0 | 36.7 | 98.3 |
| C4 | RAG-oracle | 60 | 60.0 | 23.3 | 36.7 | 13.3 | 23.3 | 0.0 | 100.0 | 23.3 | 100.0 |
| C5 | RAG-BM25 | 60 | 66.7 | 43.3 | 23.3 | 0.0 | 43.3 | 3.3 | 100.0 | 43.3 | 90.0 |

Route diagnostics (percent):

| condition | tool_call_rate | recall_at_k |
|---|---|---|
| C3 | 100.0 |  |
| C5 |  | 90.0 |

### By group (percent)

| condition | group | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | SilentInversion_opp |
|---|---|---|---|---|---|---|---|---|
| C1 | safety | Direct | 20 | 100.0 | 20.0 | 80.0 | 0.0 | 0.0 |
| C2 | safety | Direct-reshaped | 20 | 80.0 | 10.0 | 70.0 | -10.0 | 0.0 |
| T1 | safety | Tool-injected | 20 | 100.0 | 10.0 | 90.0 | 10.0 | 0.0 |
| C3 | safety | Tool | 20 | 100.0 | 30.0 | 70.0 | -10.0 | 0.0 |
| C4 | safety | RAG-oracle | 20 | 100.0 | 20.0 | 80.0 | 0.0 | 0.0 |
| C5 | safety | RAG-BM25 | 20 | 80.0 | 30.0 | 50.0 | -30.0 | 0.0 |
| C1 | capability | Direct | 20 | 90.0 | 90.0 | 0.0 | 0.0 | 0.0 |
| C2 | capability | Direct-reshaped | 20 | 40.0 | 20.0 | 20.0 | 20.0 | 0.0 |
| T1 | capability | Tool-injected | 19 | 90.0 | 55.6 | 34.4 | 34.4 | 0.0 |
| C3 | capability | Tool | 20 | 70.0 | 40.0 | 30.0 | 30.0 | 10.0 |
| C4 | capability | RAG-oracle | 20 | 70.0 | 40.0 | 30.0 | 30.0 | 0.0 |
| C5 | capability | RAG-BM25 | 20 | 90.0 | 70.0 | 20.0 | 20.0 | 0.0 |
| C1 | subjective | Direct | 20 | 20.0 | 30.0 | -10.0 | 0.0 | 0.0 |
| C2 | subjective | Direct-reshaped | 20 | 10.0 | 10.0 | 0.0 | 10.0 | 0.0 |
| T1 | subjective | Tool-injected | 20 | 30.0 | 40.0 | -10.0 | -0.0 | 0.0 |
| C3 | subjective | Tool | 19 | 11.1 | 40.0 | -28.9 | -18.9 | 0.0 |
| C4 | subjective | RAG-oracle | 20 | 10.0 | 10.0 | 0.0 | 10.0 | 0.0 |
| C5 | subjective | RAG-BM25 | 20 | 30.0 | 30.0 | 0.0 | 10.0 | 10.0 |

### ΔFaithGap vs C1 and alignment specificity (percentage points, 95% bootstrap CI)

Alignment specificity = ΔFaithGap on safety − ΔFaithGap on capability. Clearly above 0: the route effect is alignment-specific.

| condition | name | pairs | dFaithGap | CI_low | CI_high | AlignmentSpecificity | AS_CI_low | AS_CI_high |
|---|---|---|---|---|---|---|---|---|
| C2 | Direct-reshaped | 30 | 6.7 | -13.3 | 26.7 | -30.0 | -80.0 | 20.0 |
| T1 | Tool-injected | 29 | 13.8 | -3.4 | 31.0 | -23.3 | -56.7 | 8.9 |
| C3 | Tool | 29 | 3.4 | -17.2 | 24.1 | -40.0 | -80.0 | -10.0 |
| C4 | RAG-oracle | 30 | 13.3 | 0.0 | 30.0 | -30.0 | -60.0 | 0.0 |
| C5 | RAG-BM25 | 30 | 0.0 | -16.7 | 16.7 | -50.0 | -90.0 | -20.0 |

### Paired tests on opposing documents (McNemar, Holm-corrected)

| comparison | n | F_opp_a | F_opp_b | faithful_only_a | faithful_only_b | difference_a_minus_b | test | p | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| C1 vs C2 | 30 | 46.7 | 13.3 | 10 | 0 | 33.3 | exact | 0.00195 | 0.0117 |
| C2 vs T1 | 29 | 13.8 | 34.5 | 1 | 7 | -20.7 | exact | 0.0703 | 0.211 |
| T1 vs C3 | 29 | 34.5 | 37.9 | 4 | 5 | -3.4 | exact | 1 | 1 |
| C2 vs C3 | 30 | 13.3 | 36.7 | 0 | 7 | -23.3 | exact | 0.0156 | 0.0781 |
| C2 vs C4 | 30 | 13.3 | 23.3 | 0 | 3 | -10.0 | exact | 0.25 | 0.5 |
| C4 vs C5 | 30 | 23.3 | 43.3 | 0 | 6 | -20.0 | exact | 0.0312 | 0.125 |

### Labels on opposing documents (percent of valid answers)

| condition | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 46.7 | 0.0 | 3.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 40.0 | 10.0 |
| C2 | 13.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 76.7 | 10.0 |
| T1 | 34.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 65.5 | 0.0 |
| C3 | 36.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.3 | 53.3 | 6.7 |
| C4 | 23.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 73.3 | 3.3 |
| C5 | 43.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.3 | 53.3 | 0.0 |

### Route events (percent of documents)

| condition | R0 None | R3 Retrieval miss | R5 Budget hit / no answer |
|---|---|---|---|
| C1 | 100.0 | 0.0 | 0.0 |
| C2 | 100.0 | 0.0 | 0.0 |
| T1 | 98.3 | 0.0 | 1.7 |
| C3 | 98.3 | 0.0 | 1.7 |
| C4 | 100.0 | 0.0 | 0.0 |
| C5 | 90.0 | 10.0 | 0.0 |

### Label transitions on opposing documents, C1 (rows) → C3 (columns), counts

| C1 → C3 | B1 | B8 | O | E |
|---|---|---|---|---|
| B1 | 8 | 1 | 3 | 2 |
| B3 | 1 | 0 | 0 | 0 |
| O | 1 | 0 | 11 | 0 |
| E | 1 | 0 | 2 | 0 |

### Label transitions on opposing documents, C2 (rows) → C3 (columns), counts

| C2 → C3 | B1 | B8 | O | E |
|---|---|---|---|---|
| B1 | 4 | 0 | 0 | 0 |
| O | 7 | 1 | 13 | 2 |
| E | 0 | 0 | 3 | 0 |

### Label transitions on opposing documents, C2 (rows) → T1 (columns), counts

| C2 → T1 | B1 | O |
|---|---|---|
| B1 | 3 | 1 |
| O | 7 | 15 |
| E | 0 | 3 |

### Label transitions on opposing documents, T1 (rows) → C3 (columns), counts

| T1 → C3 | B1 | B8 | O | E |
|---|---|---|---|---|
| B1 | 6 | 1 | 2 | 1 |
| O | 5 | 0 | 13 | 1 |

Regression (GEE logistic, opposing docs, clustered by pair): see `results/gemini35_flash/regression_gee.txt`.

Figures: `results/figures/gemini35_flash_*.png`
