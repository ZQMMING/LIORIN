from pathlib import Path

import pytest

from tools.authorized_corpus_ci import inventory, main


def test_missing_manifest_is_unverified_not_success(monkeypatch, capsys):
    monkeypatch.delenv('LIORIN_CI_DATA_MANIFEST', raising=False)
    assert main() == 2
    assert 'UNVERIFIED' in capsys.readouterr().out


def test_inventory_changes_with_corpus_contents(tmp_path: Path):
    target = tmp_path / 'dummy'
    target.write_text('first', encoding='utf-8')
    first = inventory('cases', target)
    target.write_text('second', encoding='utf-8')
    assert inventory('cases', target) != first


def test_criteria_inventory_rejects_missing_slices(tmp_path: Path):
    with pytest.raises(ValueError, match='No original-text slices'):
        inventory('criteria', tmp_path)
