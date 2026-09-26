---
title: Custom nanoGPT LLM
type: project
category: Projects
source_ids: [src-custom-llm]
source_files:
  - raw/custom-llm-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Custom nanoGPT LLM

The project involved training a custom nanoGPT Large Language Model from scratch using a small set of word tokens. The experiment compared the performance of a starter model against an expanded model trained on different data sources.

> Class 4, Assignment 3: a tiny nanoGPT trained from scratch on a CPU, with a starter and an expanded corpus.

## Key facts

- The model was trained using nanoGPT with 2 blocks, 4 heads, 64-number embeddings, 48-token context, and word tokens. ([[custom-llm-README#My Custom LLM: a tiny nanoGPT trained from scratch|source]])
- The expanded model achieved 16/16/16 performance across the group comparison metrics. ([[custom-llm-README#By group (correct / scorable / total)|source]])
- Vocabulary coverage explains the jump from 24 to 32 scorable cases. ([[custom-llm-README#What changed, and why (vocabulary vs. learned patterns)|source]])
- The experiment used two fixed panels of 20 training and 20 validation passages. ([[custom-llm-README#4. Loss and samples|source]])

## Topics in this project

- [[Evaluation Comparison]] — This section compares the evaluation results across four experimental groups based on correctness, scorable, and total scores.

## Sources

- [[custom-llm-README]] (`raw/custom-llm-README.md`, source ID `src-custom-llm`)
  - [[custom-llm-README#My Custom LLM: a tiny nanoGPT trained from scratch]] — lines 1–14
  - [[custom-llm-README#By group (correct / scorable / total)]] — lines 39–46
  - [[custom-llm-README#What changed, and why (vocabulary vs. learned patterns)]] — lines 73–82
  - [[custom-llm-README#4. Loss and samples]] — lines 149–181
