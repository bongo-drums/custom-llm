---
title: Learning Limitations
type: topic
category: Concepts
source_ids: [src-ms-pacman]
source_files:
  - raw/ms-pacman-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Learning Limitations

The agent failed to learn ghost avoidance and learning stalled due to three primary limitations: short memory, clipped rewards, and the lack of a penalty for dying. A next experiment was proposed to test if increasing exploration could overcome these bottlenecks.

## Details

- The agent never learned to avoid ghosts, and its learning stalled after about 150 games. ([[ms-pacman-README#Limitation and next experiment|source]])
- The replay memory holds only 5,000 decisions, about eight games. The agent mostly learns from its last few games and keeps relearning the same early-maze situations. ([[ms-pacman-README#Limitation and next experiment|source]])
- Rewards are clipped to ±1 for learning, so eating a ghost (200–1,600 points) teaches no more than a 10-point pellet. ([[ms-pacman-README#Limitation and next experiment|source]])
- Losing a life only costs the pellets the agent would have eaten later, a weak and delayed signal. ([[ms-pacman-README#Limitation and next experiment|source]])
- The next experiment proposed changing exploration from 0.10 to 0.20. ([[ms-pacman-README#Limitation and next experiment|source]])

## Related notes

- [[Ms. Pac-Man DQN]] — the project where this topic comes up.
- [[DQN Hyperparameters]] — Details the specific settings chosen for the DQN project.
- [[Evaluation Comparison]] — Compares the evaluation results across different experimental groups.
- [[Training Results]] — Details the findings of the training process that faced limitations.

## Sources

- [[ms-pacman-README]] (`raw/ms-pacman-README.md`, source ID `src-ms-pacman`)
  - [[ms-pacman-README#Limitation and next experiment]] — lines 239–258
