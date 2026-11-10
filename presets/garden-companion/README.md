# Garden Companion — Muse AI specialist preset

Supports garden observations, planting plans and owner-approved seasonal schedules.

Status: **source template only**. Optional Family Link adapter is present and disabled by default. This package does not install a skill, start a model, create a subchat, or perform an external effect.

An optional [local SQLite calendar reference](../../docs/GARDEN_LOCAL_CALENDAR.md) supports scoped events, specialist proposals and explicit owner approval with durable receipts. **It is not installed in Muse**, and its authority resolver is only a fixture until bound to an authenticated host. Run `PYTHONPATH=src python examples/garden_calendar_demo.py` from the repository root.

See [installation and persistence](../../docs/INSTALL_AND_PERSISTENCE.md) and [Security](../../docs/SECURITY.md).
