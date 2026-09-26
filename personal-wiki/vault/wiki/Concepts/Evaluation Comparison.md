---
title: Evaluation Comparison
type: topic
category: Concepts
source_ids: [src-custom-llm]
source_files:
  - raw/custom-llm-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Evaluation Comparison

This section compares the evaluation results across four experimental groups based on correctness, scorable, and total scores. The comparison highlights performance differences depending on whether the starter patterns, transfer wording, or corpus were expanded.

## Details

- The comparison is also presented by group (correct / scorable / total). ([[custom-llm-README#By group (correct / scorable / total)|source]])
- For the starter_patterns group, the Starter trained condition achieved 16 / 16 / 16, while the Expanded trained condition achieved 16 / 16 / 16. ([[custom-llm-README#By group (correct / scorable / total)|source]])
- For the starter_transfer group, the Expanded trained condition achieved 8 / 8 / 8. ([[custom-llm-README#By group (correct / scorable / total)|source]])
- For the extend_corpus group, the Expanded trained condition achieved 5 / 8 / 24. ([[custom-llm-README#By group (correct / scorable / total)|source]])

## Related notes

- [[Custom nanoGPT LLM]] — the project where this topic comes up.
- [[Integration Testing]] — Verifies the functionality of Row Level Security, which is a key feature tested.
- [[Learning Limitations]] — Details specific failures and limitations encountered during the agent's learning process.
- [[Training Results]] — Shows the overall findings of the training process, which is part of the evaluation.

## Sources

- [[custom-llm-README]] (`raw/custom-llm-README.md`, source ID `src-custom-llm`)
  - [[custom-llm-README#By group (correct / scorable / total)]] — lines 39–46
