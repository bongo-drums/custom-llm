---
title: DQN Hyperparameters
type: topic
category: Concepts
source_ids: [src-ms-pacman]
source_files:
  - raw/ms-pacman-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# DQN Hyperparameters

This note details the specific hyperparameters chosen for the Ms. Pac-Man DQN project. These settings were selected to optimize training time and ensure the agent experienced sufficient environmental interaction.

## Details

- Exploration was set to 0.10, which is half the notebook's 0.20 and closer to the 5% used at evaluation. This setting ensures the agent trains in conditions similar to those scored during evaluation, allowing for fewer random moves and longer game durations. ([[ms-pacman-README#My hyperparameters|source]])
- The number of episodes was set to 1,000. This number allows the agent to complete training within an hour, fitting approximately 0.6–1.0 million decisions, which is about 15–20 times the budget of the setup check. ([[ms-pacman-README#My hyperparameters|source]])
- The learning rate was set to 0.0001, which is the standard Adam learning rate for DQN and the notebook's reference value. This rate was chosen because it resulted in stable, finite loss during the setup check. ([[ms-pacman-README#My hyperparameters|source]])

## Related notes

- [[Ms. Pac-Man DQN]] — the project where this topic comes up.
- [[Evaluation Comparison]] — Compares the evaluation results across different experimental groups.
- [[Learning Limitations]] — Explains why the agent failed to learn ghost avoidance and stalled.
- [[Training Results]] — Details the findings of the training process related to the DQN agent.

## Sources

- [[ms-pacman-README]] (`raw/ms-pacman-README.md`, source ID `src-ms-pacman`)
  - [[ms-pacman-README#My hyperparameters]] — lines 47–62
