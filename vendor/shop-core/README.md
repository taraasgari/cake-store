# shop-core

Private reusable Django commerce core.

## Rule

This repository contains generic commerce behavior only.
Branding, client media, client `.env`, deployment secrets,
client-specific templates and one-off business features stay
in each client repository.

## Extraction strategy

The existing Arayeshi project is migrated incrementally.
We do **not** rename Django app labels or migrations in the
first extraction step, because `first.User` and existing
migration history must remain compatible.

Generic behavior moves here behind stable service APIs first.
Models/migrations are moved only after compatibility tests exist.
