"""Exercise the proposed transaction boundary in a disposable database.

Inputs represent proof facts already accepted by a verifier. The tests have
no chip, key provider, account recovery provider or runtime route.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
from threading import Barrier

import pytest


@pytest.fixture
def device_db(tmp_path):
    path = tmp_path / 'device-isolation.sqlite'
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("""CREATE TABLE device (
            id TEXT PRIMARY KEY, epoch INTEGER NOT NULL, counter INTEGER NOT NULL,
            owner TEXT, state TEXT NOT NULL CHECK(state IN ('ready','bound','lost','revoked')),
            CHECK(state = 'ready' OR owner IS NOT NULL))""")
        db.execute("INSERT INTO device VALUES ('a',1,-1,NULL,'ready')")
        db.execute("INSERT INTO device VALUES ('b',1,-1,NULL,'ready')")
        db.execute("CREATE TABLE recovery (id TEXT PRIMARY KEY, account TEXT, old_device TEXT, new_device TEXT)")
    return path


def claim(db, device, account, epoch, counter):
    return db.execute("""
        UPDATE device SET owner=?, state='bound', counter=?
        WHERE id=? AND state='ready' AND epoch=? AND counter < ?
    """, (account, counter, device, epoch, counter)).rowcount == 1


def touch(db, device, account, epoch, counter):
    return db.execute("""
        UPDATE device SET counter=?
        WHERE id=? AND state='bound' AND owner=? AND epoch=? AND counter < ?
    """, (counter, device, account, epoch, counter)).rowcount == 1


def test_concurrent_binding_and_read_counter_survive_reopen(device_db):
    barrier = Barrier(2, timeout=4)

    def compete(account):
        with closing(sqlite3.connect(device_db)) as db, db:
            barrier.wait()
            return account if claim(db, 'a', account, 1, 2) else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        owners = list(pool.map(compete, ('one', 'two')))
    assert owners.count(None) == 1
    owner = next(account for account in owners if account)
    other = 'two' if owner == 'one' else 'one'
    with closing(sqlite3.connect(device_db)) as db, db:
        assert not touch(db, 'a', owner, 1, 2)
        assert not touch(db, 'a', other, 1, 3)
        assert not touch(db, 'a', owner, 0, 100)
        assert touch(db, 'a', owner, 1, 3)
    with closing(sqlite3.connect(device_db)) as db, db:
        assert not touch(db, 'a', owner, 1, 3)


def test_recovery_ticket_and_device_ownership_change_atomically(device_db):
    with closing(sqlite3.connect(device_db)) as db, db:
        assert claim(db, 'a', 'owner', 1, 1)
        db.execute("UPDATE device SET state='lost' WHERE id='a' AND owner='owner'")
        assert not touch(db, 'a', 'owner', 1, 2)
        # The isolated fixture represents a separate, reauthenticated recovery grant.
        db.execute("INSERT INTO recovery VALUES ('ticket','owner','a','b')")
    with closing(sqlite3.connect(device_db)) as db:
        with pytest.raises(ValueError), db:
            assert db.execute("DELETE FROM recovery WHERE id='ticket' AND account='owner'").rowcount == 1
            if not claim(db, 'b', 'owner', 0, 4):
                raise ValueError('Wrong proof epoch')
        with db:
            assert db.execute("DELETE FROM recovery WHERE id='ticket' AND account='other'").rowcount == 0
            assert db.execute("""
                DELETE FROM recovery WHERE id=? AND account=? AND old_device=? AND new_device=?
            """, ('ticket', 'owner', 'a', 'b')).rowcount == 1
            assert claim(db, 'b', 'owner', 1, 4)
            assert db.execute("""
                UPDATE device SET state='revoked' WHERE id='a' AND owner='owner' AND state='lost'
            """).rowcount == 1
    with closing(sqlite3.connect(device_db)) as db, db:
        assert db.execute("SELECT count(*) FROM recovery").fetchone() == (0,)
        assert not touch(db, 'a', 'owner', 1, 5)
        assert not claim(db, 'a', 'other', 1, 5)
        assert touch(db, 'b', 'owner', 1, 5)
