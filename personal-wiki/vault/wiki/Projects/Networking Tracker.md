---
title: Networking Tracker
type: project
category: Projects
source_ids: [src-networking-tracker]
source_files:
  - raw/networking-tracker-README.md
generated_by: gemma4:e2b via local Ollama
updated: 2026-09-26
reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone
---

# Networking Tracker

Networking Tracker is a private networking application designed for users to track professional contacts. The project utilizes Next.js and a PostgreSQL database secured by Row Level Security to ensure user privacy over contact data.

> Class 1, Assignment 1: a private Next.js contact tracker whose per-user privacy is enforced by Postgres Row Level Security.

## Key facts

- The application uses Neon Managed Better Auth for handling user sign-up, sign-in, and session management. ([[networking-tracker-README#Features|source]])
- The application is built using Next.js 16 (App Router) and React 19. ([[networking-tracker-README#Technology stack|source]])

## Topics in this project

- [[Database Constraints]] — The project uses specific database constraints to ensure data validity.
- [[Integration Testing]] — The project performed an automated integration test to verify Row Level Security (RLS) for two-user privacy.
- [[Local Setup Guide]] — The project requires specific prerequisites and a multi-step process to set up the Neon database and apply initial schema migrations.
- [[Row Level Security]] — Neon Managed Better Auth handles user sign-up, sign-in, sessions, and password storage.

## Sources

- [[networking-tracker-README]] (`raw/networking-tracker-README.md`, source ID `src-networking-tracker`)
  - [[networking-tracker-README#Features]] — lines 28–39
  - [[networking-tracker-README#Technology stack]] — lines 80–95
