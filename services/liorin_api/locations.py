"""Exact city-ID and alias resolution against the existing repository data."""
from collections import Counter, defaultdict
import json
from pathlib import Path


class LocationCatalogueError(ValueError):
    pass


class LocationAmbiguous(ValueError):
    pass


class LocationUnknown(ValueError):
    pass


class LocationCatalogue:
    def __init__(self, data_dir: Path):
        try:
            data = json.loads((data_dir / 'locations.json').read_text(encoding='utf-8'))
            entries = data['locations']
            if not isinstance(entries, list) or not entries:
                raise ValueError('empty locations')
            for item in entries:
                if not isinstance(item, dict):
                    raise ValueError('invalid location')
                if any(not isinstance(item.get(k), str) or not item[k].strip()
                       for k in ('id', 'name_zh', 'country', 'timezone')):
                    raise ValueError('invalid fields')
                if not isinstance(item.get('aliases', []), list) or any(
                        not isinstance(x, str) for x in item.get('aliases', [])):
                    raise ValueError('invalid aliases')
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            raise LocationCatalogueError('location catalogue unavailable') from exc
        self.entries = entries
        self.id_counts = Counter(item['id'].casefold() for item in entries)
        self.by_id = defaultdict(list)
        self.by_name = defaultdict(list)
        # Existing engine registry resolves aliases in file order; avoid
        # offering IDs that it would silently resolve to a different entry.
        engine_lookup = {}
        for item in entries:
            self.by_id[item['id'].casefold()].append(item)
            for name in (item['id'], item['name_zh'], *item.get('aliases', [])):
                engine_lookup[name.casefold()] = item
            for name in (item['name_zh'], *item.get('aliases', [])):
                self.by_name[name.strip().casefold()].append(item)
        self.safe_ids = {item['id'] for item in entries
                         if self.id_counts[item['id'].casefold()] == 1
                         and engine_lookup[item['id'].casefold()] is item}

    @staticmethod
    def public(item: dict) -> dict:
        return {'id': item['id'], 'name': item['name_zh'], 'country': item['country'],
                'timezone': item['timezone'], 'aliases': list(item.get('aliases', []))}

    def listing(self) -> list[dict]:
        return [self.public(item) for item in self.entries if item['id'] in self.safe_ids]

    def resolve(self, value: str) -> dict:
        key = value.strip().casefold()
        ids = self.by_id.get(key, [])
        if ids:
            if len(ids) != 1 or ids[0]['id'] not in self.safe_ids:
                raise LocationAmbiguous('location id is ambiguous')
            return self.public(ids[0])
        matches = {item['id']: item for item in self.by_name.get(key, [])}
        if not matches:
            raise LocationUnknown('location not found')
        if len(matches) != 1:
            raise LocationAmbiguous('location name is ambiguous')
        item = next(iter(matches.values()))
        if item['id'] not in self.safe_ids:
            raise LocationAmbiguous('location id is ambiguous')
        return self.public(item)
