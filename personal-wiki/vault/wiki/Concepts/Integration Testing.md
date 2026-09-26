---
title: Integration Testing
type: topic
category: Concepts
source_ids: [src-networking-tracker]
source_files:
  - raw/networking-tracker-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Integration Testing

The project performed an automated integration test to verify Row Level Security (RLS) for two-user privacy. This test ensured that one user could only access their own data and that unauthenticated requests were refused.

## Details

- The test automated the creation of two throwaway accounts via the public Auth API, signing both in, and then checked data isolation without database credentials or special privileges. ([[networking-tracker-README#Integration test — two-user privacy|source]])
- The test verified that User A could create a contact stamped with A's `user_id` and that User B could not read, update, delete, or create contacts owned by User A. ([[networking-tracker-README#Integration test — two-user privacy|source]])
- The test confirmed that an unauthenticated request was refused outright, ensuring that contacts could not be read without a bearer token. ([[networking-tracker-README#Integration test — two-user privacy|source]])

## Related notes

- [[Networking Tracker]] — the project where this topic comes up.
- [[Database Constraints]] — These constraints define the rules that ensure data validity, which is crucial for Row Level Security.
- [[Local Setup Guide]] — This guide outlines the prerequisites needed to set up the database environment for the project.
- [[Row Level Security]] — This note details the specific security feature that the integration test was designed to verify.

## Sources

- [[networking-tracker-README]] (`raw/networking-tracker-README.md`, source ID `src-networking-tracker`)
  - [[networking-tracker-README#Integration test — two-user privacy]] — lines 309–360
