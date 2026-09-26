---
title: Row Level Security
type: topic
category: Concepts
source_ids: [src-networking-tracker]
source_files:
  - raw/networking-tracker-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Row Level Security

Neon Managed Better Auth handles user sign-up, sign-in, sessions, and password storage. This process involves issuing a JWT and verifying claims to load user information into the Postgres session for policy checks.

## Details

- Neon Managed Better Auth handles sign up, sign in, sessions, and password storage. ([[networking-tracker-README#Authentication and ownership|source]])
- On sign-in, the system issues a JWT. ([[networking-tracker-README#Authentication and ownership|source]])
- The Neon Data API verifies the JWT against the project's JWKS and loads its claims into the Postgres session. ([[networking-tracker-README#Authentication and ownership|source]])
- `auth.user_id()` returns the signed-in user's id inside a policy. ([[networking-tracker-README#Authentication and ownership|source]])

## Related notes

- [[Networking Tracker]] — the project where this topic comes up.
- [[Database Constraints]] — RLS relies on database constraints to enforce the data access policies.
- [[Integration Testing]] — This note details the automated test performed specifically to verify Row Level Security.
- [[Local Setup Guide]] — This guide covers the necessary steps to set up the Neon database for the project.

## Sources

- [[networking-tracker-README]] (`raw/networking-tracker-README.md`, source ID `src-networking-tracker`)
  - [[networking-tracker-README#Authentication and ownership]] — lines 174–177
