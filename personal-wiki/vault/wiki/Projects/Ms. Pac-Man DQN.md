---
title: Ms. Pac-Man DQN
type: project
category: Projects
source_ids: [src-ms-pacman]
source_files:
  - raw/ms-pacman-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Ms. Pac-Man DQN

This project details the training of a Deep Q-Network (DQN) agent to play Ms. Pac-Man. The agent was trained using specific hyperparameters and demonstrated performance improvements over an untrained baseline.

> Class 3, Assignment 2: a Deep Q-Network trained to play Ms. Pac-Man, with my hyperparameter choices and results.

## Key facts

- Exploration was set to 0.10, which was half the notebook's 0.20 and closer to the 5% used at evaluation, so the agent trains in cond ([[ms-pacman-README#My hyperparameters|source]])
- The trained agent averaged 808 against the untrained network's 492 (+316). ([[ms-pacman-README#What I observed|source]])
- The agent never learned to avoid ghosts, and its learning stalled after about 150 games. ([[ms-pacman-README#Limitation and next experiment|source]])
- Four consecutive game screens, each shrunk to 84 × 84 grayscale pixels. ([[ms-pacman-README#How the agent learns|source]])

## Topics in this project

- [[DQN Hyperparameters]] — This note details the specific hyperparameters chosen for the Ms.
- [[Learning Limitations]] — The agent failed to learn ghost avoidance and learning stalled due to three primary limitations: short memory, clipped rewards, and the lack of a penalty for dying.
- [[Training Results]] — This note covers the results section of the Ms.

## Sources

- [[ms-pacman-README]] (`raw/ms-pacman-README.md`, source ID `src-ms-pacman`)
  - [[ms-pacman-README#My hyperparameters]] — lines 47–62
  - [[ms-pacman-README#What I observed]] — lines 187–224
  - [[ms-pacman-README#Limitation and next experiment]] — lines 239–258
  - [[ms-pacman-README#How the agent learns]] — lines 225–238
