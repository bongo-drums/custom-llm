---
title: Local Setup Guide
type: topic
category: Tools
source_ids: [src-networking-tracker]
source_files:
  - raw/networking-tracker-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Local Setup Guide

The project requires specific prerequisites and a multi-step process to set up the Neon database and apply initial schema migrations.

## Details

- Requirements: Node.js 20.9 or newer, and a Neon account. ([[networking-tracker-README#Local setup|source]])
- The setup involves cloning the repository and installing dependencies. ([[networking-tracker-README#Local setup|source]])
- The Neon project setup requires enabling Managed Better Auth and enabling the Data API with Managed Better Auth for JWT authentication. ([[networking-tracker-README#1. Create the Neon project|source]])
- The Data API is enabled per branch and is unavailable if IP Allow or Private Networking is on. ([[networking-tracker-README#1. Create the Neon project|source]])
- The database migration command applies `db/schema.sql` and reports whether RLS is enabled and how many policies exist. ([[networking-tracker-README#3. Create the table and policies|source]])
- The migration process is idempotent, meaning it is safe to re-run after editing the schema. ([[networking-tracker-README#3. Create the table and policies|source]])

## Related notes

- [[Networking Tracker]] — the project where this topic comes up.
- [[DQN Hyperparameters]] — Details the specific settings used to optimize the Ms. Pac-Man DQN training.
- [[Integration Testing]] — Verifies the automated test ensuring Row Level Security for two-user privacy.
- [[Training Results]] — Shows the findings and outcomes of the Ms. Pac-Man DQN training process.

## Sources

- [[networking-tracker-README]] (`raw/networking-tracker-README.md`, source ID `src-networking-tracker`)
  - [[networking-tracker-README#Local setup]] — lines 222–231
  - [[networking-tracker-README#1. Create the Neon project]] — lines 232–240
  - [[networking-tracker-README#3. Create the table and policies]] — lines 249–258
