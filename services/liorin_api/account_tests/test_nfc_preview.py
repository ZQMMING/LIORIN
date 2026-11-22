from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.liorin_api.nfc_preview import IsolatedDeviceLifecycle


def test_signed_claim_retouch_loss_and_revoke_keep_account_boundary():
    key = Ed25519PrivateKey.generate()
    now = [0.]

    def verify(challenge, proof):
        try:
            key.public_key().verify(proof, challenge)
        except InvalidSignature:
            return False
        return True

    devices = IsolatedDeviceLifecycle(_clock=lambda: now[0])
    devices.register('test-device', verify)
    challenge = devices.begin('test-device', 'owner', 'claim')
    assert devices.consume(challenge, 'owner', key.sign(challenge.encode())) == 'test-device'
    with pytest.raises(ValueError):
        devices.consume(challenge, 'owner', key.sign(challenge.encode()))
    with pytest.raises(ValueError):
        devices.begin('test-device', 'other', 'touch')
    touch = devices.begin('test-device', 'owner', 'touch')
    with pytest.raises(ValueError):
        devices.consume(touch, 'other', key.sign(touch.encode()))
    assert devices.consume(touch, 'owner', key.sign(touch.encode())) == 'test-device'
    expired = devices.begin('test-device', 'owner', 'touch')
    now[0] += 60
    with pytest.raises(ValueError):
        devices.consume(expired, 'owner', key.sign(expired.encode()))
    invalid = devices.begin('test-device', 'owner', 'touch')
    with pytest.raises(ValueError):
        devices.consume(invalid, 'owner', b'test-device')
    pending = devices.begin('test-device', 'owner', 'touch')
    devices.deactivate('test-device', 'owner', lost=True)
    with pytest.raises(ValueError):
        devices.consume(pending, 'owner', key.sign(pending.encode()))
    devices.deactivate('test-device', 'owner', lost=False)
    with pytest.raises(ValueError):
        devices.begin('test-device', 'owner', 'claim')

def test_concurrent_valid_device_proofs_bind_only_one_account():
    key = Ed25519PrivateKey.generate()

    def verify(challenge, proof):
        key.public_key().verify(proof, challenge)
        return True

    devices = IsolatedDeviceLifecycle()
    devices.register('concurrent-device', verify)
    barrier = Barrier(2, timeout=3)

    def claim(account):
        challenge = devices.begin('concurrent-device', account, 'claim')
        signature = key.sign(challenge.encode())
        barrier.wait()
        try:
            devices.consume(challenge, account, signature)
        except ValueError:
            return None
        return account

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(claim, ('account-a', 'account-b')))
    assert outcomes.count(None) == 1
    winner = next(account for account in outcomes if account is not None)
    loser = 'account-a' if winner == 'account-b' else 'account-b'
    with pytest.raises(ValueError):
        devices.begin('concurrent-device', loser, 'touch')
    with pytest.raises(ValueError):
        devices.deactivate('concurrent-device', loser, lost=True)
