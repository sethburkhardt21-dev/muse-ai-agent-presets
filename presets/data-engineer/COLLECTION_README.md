# Data Engineering & Database Architect

Design safe data contracts, reconcile incremental records and review query access paths with reproducible offline tools.

## Run the exported kit

```sh
python run.py --demo
```

No dependency installation, API key, network access or repository checkout is needed. The result is JSON containing actual local calculations and explicit scope. Python 3.10 or newer is required.

For your own supplied records:

```sh
python run.py --tool schema-evolution --input input.json
```

`EXAMPLE.json` contains the exact input shapes for the demo. Copy the `inputs` object for the chosen tool into `input.json`; the file must contain one object, not the entire example wrapper. Unknown fields and invalid values produce a structured error and exit code 2.

## Run from the source repository

```sh
python tools/muse_collection.py demo data-engineer
python tools/muse_collection.py kit data-engineer --to ./data-engineer.zip
```

The ZIP destination is create-only; use a new name rather than overwriting an existing file.

## Included capabilities

- **Review a Schema Change Before Migration**: `schema-evolution`.
- **Reconcile Versioned Events Without Resurrection**: `incremental-pipeline`.
- **Read a Query Plan Before Changing Indexes**: `query-plan-review`.

## Use with an assistant

Read `PLAYBOOK.md` and only the relevant skill documents. Keep the assistant's existing identity, memory, user preferences and tool permissions. Ask it to inspect your supplied records, use the local tool when available, explain the result and hand off any external action to your existing supported host.

## Boundaries

The kit does not connect to databases, control browsers, change infrastructure, grant approvals or create background jobs. Its reports are useful calculations and consistency reviews, not native-assistant performance certification or evidence that a production action occurred. The archive manifest checks package self-consistency, not publisher identity or a cryptographic signature.
