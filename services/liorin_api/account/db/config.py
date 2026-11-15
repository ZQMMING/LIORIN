"""The account adapter never falls back to a database connection."""


def get_dsn() -> str:
    raise RuntimeError('an explicit account database is required')
