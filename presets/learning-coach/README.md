# Learning Coach — Muse AI specialist preset

Runs source-grounded, adaptive study and evidence-based learning reviews.

Status: **source template only**. Optional Family Link adapter is present and disabled by default. This package does not install a skill, start a model, create a subchat, or perform an external effect.

See [installation and persistence](../../docs/INSTALL_AND_PERSISTENCE.md) and [the five-layer proof standard](../../docs/FIVE_LAYERS_AND_DOORS.md).

## Working offline study engine (R6)

Run `PYTHONPATH=src python examples/learning_session_demo.py` from the repository root. It demonstrates a real, local SQLite flow from owner-supplied science definitions through specialist-held question drafts, owner approval, learner scoring and review-due replay. Read [the complete source and authorization contract](../../docs/LEARNING_LOCAL_STUDY.md) before using this in an application. `LearningScope` is a local callback shape, not an authenticated Muse credential. Higher-stakes study, hidden exams and real account migration remain gated.
