# Results: Does the Route Matter?

Faithful = B1 or B2. FaithGap = faithful% on confirming − faithful% on opposing. ΔFaithGap = FaithGap(condition) − FaithGap(C1). All rates use valid (judged) answers; F_opp_given_R0 keeps only runs where the gold document reached the model.

## Model: claude_sonnet46

### All categories (percent)

| condition | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | ClaimPreservation_opp | SilentInversion_opp | SilentShare_opp | F_opp_given_R0 | share_R0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Direct | 1876 | 59.9 | 33.3 | 26.7 | 0.0 | 36.9 | 0.4 | 76.4 | 33.3 | 99.8 |
| C2 | Direct-reshaped | 1880 | 36.1 | 17.8 | 18.3 | -8.4 | 21.5 | 1.2 | 91.8 | 17.8 | 100.0 |
| T1 | Tool-injected | 1880 | 57.4 | 27.8 | 29.7 | 3.0 | 33.2 | 2.8 | 84.2 | 27.8 | 100.0 |
| C3 | Tool | 1880 | 56.9 | 27.9 | 29.0 | 2.4 | 31.9 | 2.0 | 84.8 | 27.9 | 100.0 |
| C4 | RAG-oracle | 1880 | 33.0 | 15.9 | 17.1 | -9.5 | 20.4 | 1.3 | 92.4 | 15.9 | 100.0 |
| C5 | RAG-BM25 | 1876 | 44.0 | 27.8 | 16.2 | -10.4 | 34.4 | 1.3 | 78.0 | 27.8 | 92.1 |

Route diagnostics (percent):

| condition | tool_call_rate | recall_at_k |
|---|---|---|
| C3 | 100.0 |  |
| C5 |  | 92.3 |

### By group (percent)

| condition | group | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | SilentInversion_opp |
|---|---|---|---|---|---|---|---|---|
| C1 | safety | Direct | 772 | 64.5 | 8.5 | 56.0 | 0.0 | 0.3 |
| C2 | safety | Direct-reshaped | 772 | 34.7 | 5.2 | 29.5 | -26.4 | 1.6 |
| T1 | safety | Tool-injected | 772 | 64.8 | 9.8 | 54.9 | -1.0 | 2.8 |
| C3 | safety | Tool | 772 | 64.0 | 9.1 | 54.9 | -1.0 | 2.6 |
| C4 | safety | RAG-oracle | 772 | 29.8 | 5.4 | 24.4 | -31.6 | 1.8 |
| C5 | safety | RAG-BM25 | 772 | 36.5 | 11.7 | 24.9 | -31.1 | 0.8 |
| C1 | capability | Direct | 492 | 90.7 | 78.0 | 12.6 | 0.0 | 0.0 |
| C2 | capability | Direct-reshaped | 496 | 60.5 | 36.7 | 23.8 | 11.2 | 0.8 |
| T1 | capability | Tool-injected | 496 | 79.4 | 51.6 | 27.8 | 15.2 | 3.2 |
| C3 | capability | Tool | 496 | 80.2 | 52.4 | 27.8 | 15.2 | 2.4 |
| C4 | capability | RAG-oracle | 496 | 59.3 | 32.3 | 27.0 | 14.4 | 0.8 |
| C5 | capability | RAG-BM25 | 492 | 79.7 | 55.7 | 24.0 | 11.4 | 0.0 |
| C1 | subjective | Direct | 612 | 29.4 | 28.4 | 1.0 | 0.0 | 1.0 |
| C2 | subjective | Direct-reshaped | 612 | 18.0 | 18.3 | -0.3 | -1.3 | 1.0 |
| T1 | subjective | Tool-injected | 612 | 30.4 | 31.0 | -0.7 | -1.6 | 2.3 |
| C3 | subjective | Tool | 612 | 29.1 | 31.7 | -2.6 | -3.6 | 1.0 |
| C4 | subjective | RAG-oracle | 612 | 15.7 | 15.7 | 0.0 | -1.0 | 1.0 |
| C5 | subjective | RAG-BM25 | 612 | 24.8 | 25.8 | -1.0 | -2.0 | 2.9 |

### ΔFaithGap vs C1 and alignment specificity (percentage points, 95% bootstrap CI)

Alignment specificity = ΔFaithGap on safety − ΔFaithGap on capability. Clearly above 0: the route effect is alignment-specific.

| condition | name | pairs | dFaithGap | CI_low | CI_high | AlignmentSpecificity | AS_CI_low | AS_CI_high |
|---|---|---|---|---|---|---|---|---|
| C2 | Direct-reshaped | 938 | -8.4 | -12.4 | -4.4 | -37.4 | -46.9 | -27.3 |
| T1 | Tool-injected | 938 | 3.1 | -0.6 | 6.8 | -16.5 | -26.2 | -6.8 |
| C3 | Tool | 938 | 2.5 | -1.3 | 6.3 | -16.5 | -26.6 | -6.4 |
| C4 | RAG-oracle | 938 | -9.6 | -13.3 | -5.7 | -45.8 | -55.4 | -36.0 |
| C5 | RAG-BM25 | 935 | -10.6 | -15.2 | -6.1 | -42.2 | -52.7 | -32.3 |

### Paired tests on opposing documents (McNemar, Holm-corrected)

| comparison | n | F_opp_a | F_opp_b | faithful_only_a | faithful_only_b | difference_a_minus_b | test | p | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| C1 vs C2 | 938 | 33.3 | 17.8 | 167 | 22 | 15.5 | chi2 | 1.13e-25 | 6.79e-25 |
| C2 vs T1 | 940 | 17.8 | 27.8 | 32 | 126 | -10.0 | chi2 | 1.38e-13 | 5.12e-13 |
| T1 vs C3 | 940 | 27.8 | 27.9 | 20 | 21 | -0.1 | chi2 | 1 | 1 |
| C2 vs C3 | 940 | 17.8 | 27.9 | 33 | 128 | -10.1 | chi2 | 1.28e-13 | 5.12e-13 |
| C2 vs C4 | 940 | 17.8 | 15.9 | 60 | 42 | 1.9 | chi2 | 0.0923 | 0.185 |
| C4 vs C5 | 938 | 15.9 | 27.8 | 36 | 148 | -11.9 | chi2 | 2.77e-16 | 1.38e-15 |

### Labels on opposing documents (percent of valid answers)

| condition | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 30.5 | 2.8 | 1.9 | 1.2 | 0.5 | 0.2 | 11.9 | 0.4 | 41.7 | 8.8 |
| C2 | 16.9 | 0.9 | 0.7 | 2.8 | 0.2 | 0.4 | 2.6 | 1.2 | 59.6 | 14.8 |
| T1 | 25.0 | 2.8 | 1.1 | 2.9 | 1.5 | 0.2 | 5.7 | 2.8 | 45.1 | 13.0 |
| C3 | 25.4 | 2.4 | 0.3 | 3.2 | 0.5 | 1.1 | 5.9 | 2.0 | 43.8 | 15.3 |
| C4 | 14.4 | 1.5 | 2.2 | 2.0 | 0.3 | 0.4 | 1.4 | 1.3 | 58.1 | 18.4 |
| C5 | 24.6 | 3.2 | 2.8 | 3.7 | 0.1 | 1.3 | 8.0 | 1.3 | 53.6 | 1.4 |

### Route events (percent of documents)

| condition | R0 None | R3 Retrieval miss | R5 Budget hit / no answer |
|---|---|---|---|
| C1 | 99.8 | 0.0 | 0.2 |
| C2 | 100.0 | 0.0 | 0.0 |
| T1 | 100.0 | 0.0 | 0.0 |
| C3 | 100.0 | 0.0 | 0.0 |
| C4 | 100.0 | 0.0 | 0.0 |
| C5 | 92.1 | 7.7 | 0.2 |

### Label transitions on opposing documents, C1 (rows) → C3 (columns), counts

| C1 → C3 | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | 181 | 10 | 0 | 4 | 1 | 0 | 0 | 6 | 50 | 34 |
| B2 | 7 | 4 | 0 | 4 | 0 | 0 | 1 | 2 | 5 | 3 |
| B3 | 6 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 8 | 1 |
| B4 | 0 | 0 | 0 | 2 | 0 | 0 | 1 | 1 | 5 | 2 |
| B5 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 |
| B6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| B7 | 0 | 0 | 0 | 18 | 3 | 9 | 49 | 1 | 19 | 13 |
| B8 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 |
| O | 35 | 5 | 3 | 1 | 0 | 1 | 2 | 6 | 268 | 70 |
| E | 5 | 3 | 0 | 1 | 0 | 0 | 1 | 0 | 52 | 21 |

### Label transitions on opposing documents, C2 (rows) → C3 (columns), counts

| C2 → C3 | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | 119 | 10 | 0 | 0 | 1 | 0 | 0 | 3 | 18 | 8 |
| B2 | 5 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| B3 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 |
| B4 | 7 | 0 | 0 | 6 | 2 | 3 | 7 | 0 | 1 | 0 |
| B5 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| B6 | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 0 | 0 | 0 |
| B7 | 0 | 0 | 0 | 2 | 2 | 2 | 15 | 0 | 1 | 2 |
| B8 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 7 | 1 |
| O | 86 | 12 | 3 | 13 | 0 | 4 | 19 | 14 | 309 | 100 |
| E | 16 | 1 | 0 | 4 | 0 | 1 | 10 | 1 | 74 | 32 |

### Label transitions on opposing documents, C2 (rows) → T1 (columns), counts

| C2 → T1 | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | 123 | 6 | 1 | 1 | 0 | 0 | 0 | 3 | 18 | 7 |
| B2 | 5 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| B3 | 4 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| B4 | 7 | 1 | 0 | 3 | 4 | 1 | 8 | 0 | 2 | 0 |
| B5 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| B6 | 0 | 0 | 0 | 2 | 0 | 0 | 2 | 0 | 0 | 0 |
| B7 | 0 | 0 | 0 | 2 | 4 | 0 | 16 | 1 | 1 | 0 |
| B8 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 8 | 0 |
| O | 79 | 16 | 7 | 16 | 3 | 1 | 16 | 18 | 314 | 90 |
| E | 15 | 2 | 1 | 1 | 3 | 0 | 10 | 3 | 79 | 25 |

### Label transitions on opposing documents, T1 (rows) → C3 (columns), counts

| T1 → C3 | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | 207 | 12 | 1 | 1 | 0 | 0 | 0 | 1 | 9 | 4 |
| B2 | 12 | 10 | 0 | 2 | 1 | 0 | 0 | 1 | 0 | 0 |
| B3 | 6 | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 1 | 0 |
| B4 | 1 | 0 | 0 | 11 | 0 | 2 | 10 | 1 | 1 | 1 |
| B5 | 2 | 0 | 0 | 3 | 1 | 2 | 5 | 0 | 1 | 0 |
| B6 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| B7 | 0 | 0 | 0 | 7 | 3 | 5 | 38 | 0 | 1 | 0 |
| B8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 15 | 6 |
| O | 8 | 0 | 1 | 2 | 0 | 0 | 1 | 8 | 313 | 91 |
| E | 3 | 1 | 0 | 1 | 0 | 0 | 1 | 3 | 71 | 42 |

Regression (GEE logistic, opposing docs, clustered by pair): see `results/claude_sonnet46/regression_gee.txt`.

Figures: `results/figures/claude_sonnet46_*.png`

## Model: gemini35_flash

### All categories (percent)

| condition | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | ClaimPreservation_opp | SilentInversion_opp | SilentShare_opp | F_opp_given_R0 | share_R0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Direct | 1879 | 71.1 | 42.7 | 28.4 | 0.0 | 44.5 | 0.1 | 96.8 | 42.7 | 100.0 |
| C2 | Direct-reshaped | 1880 | 44.0 | 21.9 | 22.1 | -6.2 | 23.0 | 0.3 | 98.6 | 21.9 | 100.0 |
| T1 | Tool-injected | 1857 | 70.3 | 34.0 | 36.3 | 8.0 | 35.6 | 0.5 | 97.5 | 34.0 | 98.8 |
| C3 | Tool | 1811 | 68.0 | 33.7 | 34.3 | 5.9 | 36.0 | 0.8 | 96.7 | 33.7 | 96.3 |
| C4 | RAG-oracle | 1879 | 60.9 | 26.0 | 35.0 | 6.6 | 27.1 | 0.0 | 98.4 | 26.0 | 100.0 |
| C5 | RAG-BM25 | 1880 | 63.0 | 39.4 | 23.6 | -4.7 | 42.6 | 0.7 | 94.7 | 39.4 | 92.3 |

Route diagnostics (percent):

| condition | tool_call_rate | recall_at_k |
|---|---|---|
| C3 | 100.0 |  |
| C5 |  | 92.3 |

### By group (percent)

| condition | group | name | n_valid | F_conf | F_opp | FaithGap | dFaithGap_vs_C1 | SilentInversion_opp |
|---|---|---|---|---|---|---|---|---|
| C1 | safety | Direct | 771 | 83.2 | 17.1 | 66.0 | 0.0 | 0.0 |
| C2 | safety | Direct-reshaped | 772 | 59.1 | 13.7 | 45.3 | -20.7 | 0.3 |
| T1 | safety | Tool-injected | 765 | 89.7 | 18.4 | 71.3 | 5.3 | 0.5 |
| C3 | safety | Tool | 730 | 89.2 | 20.5 | 68.7 | 2.6 | 0.3 |
| C4 | safety | RAG-oracle | 771 | 75.6 | 15.3 | 60.3 | -5.7 | 0.0 |
| C5 | safety | RAG-BM25 | 772 | 66.8 | 23.1 | 43.8 | -22.2 | 0.3 |
| C1 | capability | Direct | 496 | 89.5 | 79.4 | 10.1 | 0.0 | 0.4 |
| C2 | capability | Direct-reshaped | 496 | 39.5 | 21.8 | 17.7 | 7.7 | 0.8 |
| T1 | capability | Tool-injected | 492 | 79.8 | 50.0 | 29.8 | 19.8 | 0.8 |
| C3 | capability | Tool | 491 | 69.4 | 44.7 | 24.7 | 14.6 | 1.6 |
| C4 | capability | RAG-oracle | 496 | 68.1 | 29.0 | 39.1 | 29.0 | 0.0 |
| C5 | capability | RAG-BM25 | 496 | 82.7 | 58.5 | 24.2 | 14.1 | 0.0 |
| C1 | subjective | Direct | 612 | 40.8 | 45.1 | -4.2 | 0.0 | 0.0 |
| C2 | subjective | Direct-reshaped | 612 | 28.8 | 32.4 | -3.6 | 0.7 | 0.0 |
| T1 | subjective | Tool-injected | 600 | 38.1 | 40.9 | -2.9 | 1.4 | 0.3 |
| C3 | subjective | Tool | 590 | 40.3 | 40.7 | -0.5 | 3.8 | 0.7 |
| C4 | subjective | RAG-oracle | 612 | 36.6 | 36.9 | -0.3 | 3.9 | 0.0 |
| C5 | subjective | RAG-BM25 | 612 | 42.2 | 44.4 | -2.3 | 2.0 | 2.0 |

### ΔFaithGap vs C1 and alignment specificity (percentage points, 95% bootstrap CI)

Alignment specificity = ΔFaithGap on safety − ΔFaithGap on capability. Clearly above 0: the route effect is alignment-specific.

| condition | name | pairs | dFaithGap | CI_low | CI_high | AlignmentSpecificity | AS_CI_low | AS_CI_high |
|---|---|---|---|---|---|---|---|---|
| C2 | Direct-reshaped | 939 | -6.3 | -10.2 | -2.2 | -28.4 | -38.0 | -18.9 |
| T1 | Tool-injected | 918 | 7.8 | 4.5 | 11.1 | -14.0 | -22.5 | -5.1 |
| C3 | Tool | 871 | 7.0 | 3.3 | 10.8 | -10.2 | -19.3 | -1.2 |
| C4 | RAG-oracle | 938 | 6.6 | 3.0 | 10.1 | -34.8 | -44.2 | -25.9 |
| C5 | RAG-BM25 | 939 | -4.8 | -9.2 | -0.5 | -36.5 | -46.5 | -26.5 |

### Paired tests on opposing documents (McNemar, Holm-corrected)

| comparison | n | F_opp_a | F_opp_b | faithful_only_a | faithful_only_b | difference_a_minus_b | test | p | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| C1 vs C2 | 939 | 42.7 | 21.9 | 215 | 20 | 20.8 | chi2 | 1.05e-36 | 6.29e-36 |
| C2 vs T1 | 927 | 21.5 | 34.0 | 23 | 139 | -12.5 | chi2 | 1.64e-19 | 8.18e-19 |
| T1 vs C3 | 891 | 34.7 | 33.2 | 68 | 55 | 1.5 | chi2 | 0.279 | 0.279 |
| C2 vs C3 | 904 | 22.1 | 33.7 | 28 | 133 | -11.6 | chi2 | 2.48e-16 | 7.43e-16 |
| C2 vs C4 | 940 | 21.9 | 26.0 | 35 | 73 | -4.0 | chi2 | 0.00037 | 0.000741 |
| C4 vs C5 | 940 | 26.0 | 39.4 | 40 | 166 | -13.4 | chi2 | 3.06e-18 | 1.22e-17 |

### Labels on opposing documents (percent of valid answers)

| condition | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | O | E |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 42.6 | 0.1 | 1.4 | 0.4 | 0.0 | 0.0 | 0.0 | 0.1 | 47.6 | 7.8 |
| C2 | 21.8 | 0.1 | 0.7 | 0.3 | 0.0 | 0.0 | 0.0 | 0.3 | 66.1 | 10.6 |
| T1 | 34.0 | 0.0 | 1.2 | 0.4 | 0.0 | 0.0 | 0.0 | 0.5 | 58.0 | 5.8 |
| C3 | 33.7 | 0.0 | 1.4 | 0.8 | 0.0 | 0.0 | 0.0 | 0.8 | 58.4 | 4.9 |
| C4 | 26.0 | 0.0 | 1.0 | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 | 64.7 | 8.2 |
| C5 | 39.3 | 0.1 | 1.0 | 2.2 | 0.0 | 0.0 | 0.0 | 0.7 | 55.9 | 0.9 |

### Route events (percent of documents)

| condition | R0 None | R3 Retrieval miss | R5 Budget hit / no answer |
|---|---|---|---|
| C1 | 100.0 | 0.0 | 0.0 |
| C2 | 100.0 | 0.0 | 0.0 |
| T1 | 98.8 | 0.0 | 1.2 |
| C3 | 96.3 | 0.0 | 3.7 |
| C4 | 100.0 | 0.0 | 0.0 |
| C5 | 92.3 | 7.7 | 0.0 |

### Label transitions on opposing documents, C1 (rows) → C3 (columns), counts

| C1 → C3 | B1 | B3 | B4 | B8 | O | E |
|---|---|---|---|---|---|---|
| B1 | 246 | 10 | 3 | 6 | 124 | 5 |
| B2 | 1 | 0 | 0 | 0 | 0 | 0 |
| B3 | 5 | 1 | 2 | 0 | 5 | 0 |
| B4 | 3 | 0 | 1 | 0 | 0 | 0 |
| B8 | 0 | 0 | 0 | 0 | 1 | 0 |
| O | 45 | 2 | 1 | 1 | 341 | 34 |
| E | 5 | 0 | 0 | 0 | 56 | 5 |

### Label transitions on opposing documents, C2 (rows) → C3 (columns), counts

| C2 → C3 | B1 | B3 | B4 | B8 | O | E |
|---|---|---|---|---|---|---|
| B1 | 171 | 8 | 1 | 2 | 17 | 0 |
| B2 | 1 | 0 | 0 | 0 | 0 | 0 |
| B3 | 4 | 2 | 0 | 0 | 1 | 0 |
| B4 | 2 | 0 | 1 | 0 | 0 | 0 |
| B8 | 2 | 0 | 0 | 0 | 1 | 0 |
| O | 121 | 3 | 5 | 3 | 430 | 36 |
| E | 4 | 0 | 0 | 2 | 79 | 8 |

### Label transitions on opposing documents, C2 (rows) → T1 (columns), counts

| C2 → T1 | B1 | B3 | B4 | B8 | O | E |
|---|---|---|---|---|---|---|
| B1 | 176 | 2 | 1 | 2 | 14 | 3 |
| B2 | 0 | 1 | 0 | 0 | 0 | 0 |
| B3 | 3 | 0 | 0 | 0 | 4 | 0 |
| B4 | 2 | 1 | 0 | 0 | 0 | 0 |
| B8 | 2 | 0 | 0 | 0 | 1 | 0 |
| O | 128 | 7 | 3 | 2 | 437 | 39 |
| E | 4 | 0 | 0 | 1 | 82 | 12 |

### Label transitions on opposing documents, T1 (rows) → C3 (columns), counts

| T1 → C3 | B1 | B3 | B4 | B8 | O | E |
|---|---|---|---|---|---|---|
| B1 | 241 | 8 | 2 | 2 | 54 | 2 |
| B3 | 4 | 0 | 1 | 1 | 4 | 1 |
| B4 | 1 | 0 | 0 | 0 | 3 | 0 |
| B8 | 2 | 0 | 0 | 1 | 2 | 0 |
| O | 47 | 4 | 4 | 3 | 419 | 36 |
| E | 1 | 1 | 0 | 0 | 42 | 5 |

Regression (GEE logistic, opposing docs, clustered by pair): see `results/gemini35_flash/regression_gee.txt`.

Figures: `results/figures/gemini35_flash_*.png`
