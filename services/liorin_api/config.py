"""Read-only resource location; no implicit database or engine setup."""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    data_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str], repo_root: Path) -> 'Settings':
        configured = env.get('LIORIN_DATA_DIR')
        path = Path(configured).expanduser() if configured else repo_root / 'data'
        if not path.is_absolute():
            raise ValueError('LIORIN_DATA_DIR must be an absolute path')
        return cls(data_dir=path.resolve())
