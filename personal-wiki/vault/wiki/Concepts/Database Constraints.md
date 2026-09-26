---
title: Database Constraints
type: topic
category: Concepts
source_ids: [src-networking-tracker]
source_files:
  - raw/networking-tracker-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Database Constraints

The project uses specific database constraints to ensure data validity. These constraints define rules that make invalid data impossible within the database schema.

## Details

- The full definition of the database schema is located in `db/schema.sql`. ([[networking-tracker-README#Database schema|source]])
- The constraints listed are the authoritative validation rules for the data. ([[networking-tracker-README#Constraints that make invalid data impossible|source]])
- A constraint ensures that the contact name is not blank. ([[networking-tracker-README#Constraints that make invalid data impossible|source]])
- A constraint ensures that the priority value is one of 'high', 'medium', or 'low'. ([[networking-tracker-README#Constraints that make invalid data impossible|source]])

## Related notes

- [[Networking Tracker]] — the project where this topic comes up.
- [[Integration Testing]] — Shows the automated verification process for Row Level Security.
- [[Learning Limitations]] — Explains why the agent failed to learn ghost avoidance.
- [[Row Level Security]] — Details how Row Level Security was tested during integration testing.

## Sources

- [[networking-tracker-README]] (`raw/networking-tracker-README.md`, source ID `src-networking-tracker`)
  - [[networking-tracker-README#Database schema]] — lines 141–144
  - [[networking-tracker-README#Constraints that make invalid data impossible]] — lines 163–173
