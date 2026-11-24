# Data

`faithconflict.jsonl` is the normalized form of **FaithConflict** (Zahraei et al., COLM 2026), built by `python -m src.data --prepare` from the Hugging Face dataset [PardisSzah/FaithConflict](https://huggingface.co/datasets/PardisSzah/FaithConflict), which is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Changes from the original: each pair's `summary_template` is filled with `claim_true` (confirming) and `claim_false` (opposing) to make the two documents, and fields are renamed to the harness's schema (`pair_id`, `doc_id`, `doc_uid`, `twin_doc_id`, `category`, `group`, `polarity`, `claim`, `document`, `question`). 1,880 documents from 940 pairs: safety 386, capability 248, subjective 306.

Rebuild it at any time with `python -m src.data --prepare`.
