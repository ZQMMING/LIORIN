# LIORIN product API bootstrap

This is an isolated integration entry point; it does not install or change the
existing `heluo-engine` package. No engine, database, account or date policy is
wired at this stage. `/health` reports process liveness and component state;
`/ready` and calculation/account endpoints return 503 until those dependencies
are reviewed and integrated. `/v1/locations` reads the existing city catalogue;
`/v1/locations/resolve` rejects ambiguous names and colliding IDs rather than
guessing. A directory being present is not evidence that its data is valid.

From the repository root:

```sh
python -m pip install -r services/liorin_api/requirements.txt
python -m uvicorn services.liorin_api.app:app --host 127.0.0.1 --port 8000
```

The optional `LIORIN_DATA_DIR` must be an absolute path. The default is the
repository's `data` directory; the bootstrap only checks its existence and
does not create or modify it. This entry point is not a deployment instruction.
