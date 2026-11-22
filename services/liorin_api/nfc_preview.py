"""Isolated device lifecycle. No route, account token or production persistence."""

from dataclasses import dataclass, field
from secrets import token_urlsafe
from threading import Lock
from time import monotonic
from typing import Callable, Literal


Purpose = Literal['claim', 'touch']
Verifier = Callable[[bytes, bytes], bool]


@dataclass
class _Device:
    verify: Verifier
    owner: str | None = None
    state: Literal['available', 'bound', 'lost', 'revoked'] = 'available'


@dataclass(frozen=True)
class _Challenge:
    device: str
    account: str
    purpose: Purpose
    expires_at: float


@dataclass
class IsolatedDeviceLifecycle:
    _clock: Callable[[], float] = monotonic
    _devices: dict[str, _Device] = field(default_factory=dict, init=False)
    _challenges: dict[str, _Challenge] = field(default_factory=dict, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def register(self, device_id: str, verify: Verifier) -> None:
        with self._lock:
            if not device_id or device_id in self._devices:
                raise ValueError('Device registration rejected')
            self._devices[device_id] = _Device(verify=verify)

    def begin(self, device_id: str, account: str, purpose: Purpose) -> str:
        with self._lock:
            device = self._devices.get(device_id)
            if not account or not self._eligible(device, account, purpose):
                raise ValueError('Device operation unavailable')
            now = self._clock()
            self._challenges = {key: value for key, value in self._challenges.items()
                                if value.expires_at > now and (value.device, value.account, value.purpose)
                                != (device_id, account, purpose)}
            challenge = 'liorin-nfc-preview-v1:' + token_urlsafe(32)
            self._challenges[challenge] = _Challenge(device_id, account, purpose, now + 60)
            return challenge

    @staticmethod
    def _eligible(device: _Device | None, account: str, purpose: Purpose) -> bool:
        return device is not None and (
            (purpose == 'claim' and device.state == 'available')
            or (purpose == 'touch' and device.state == 'bound' and device.owner == account)
        )

    def consume(self, challenge: str, account: str, signed_proof: bytes) -> str:
        with self._lock:
            pending = self._challenges.get(challenge)
            if pending is None or pending.account != account or pending.expires_at <= self._clock():
                raise ValueError('Device proof rejected')
            device = self._devices[pending.device]
            if not self._eligible(device, account, pending.purpose):
                raise ValueError('Device operation unavailable')
            del self._challenges[challenge]
            if not device.verify(challenge.encode('ascii'), signed_proof):
                raise ValueError('Device proof rejected')
            if pending.purpose == 'claim':
                device.owner = account
                device.state = 'bound'
            return pending.device

    def deactivate(self, device_id: str, account: str, *, lost: bool) -> None:
        with self._lock:
            device = self._devices.get(device_id)
            if device is None or device.owner != account or device.state not in ('bound', 'lost'):
                raise ValueError('Device operation unavailable')
            device.state = 'lost' if lost else 'revoked'
            self._challenges = {key: value for key, value in self._challenges.items() if value.device != device_id}
