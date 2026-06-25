from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TransformDirective(str, Enum):
    """Hardware/graphics directives used by the Her GUI stack."""

    TRANSLATE_IO = "Daq"
    SCALE_IO = "Cap"
    ROTATE_IO = "MVP"
    SORT_IO = "Jecht"


@dataclass(frozen=True, slots=True)
class PointInTimeVector:
    tick: int
    restraint: float = 0.62

    def clamp(self, value: float) -> float:
        limit = abs(self.restraint)
        return max(-limit, min(limit, value))


@dataclass(frozen=True, slots=True)
class Request:
    package: str
    updates: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Bucket:
    """A bounded pool entry represented as bytes, hexadecimal, and bits."""

    raw: bytes

    @property
    def hex(self) -> str:
        return self.raw.hex()

    @property
    def bits(self) -> str:
        return "".join(f"{byte:08b}" for byte in self.raw)


class BucketPool:
    def __init__(self, capacity: int = 413) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._items: list[Bucket] = []

    def push(self, payload: bytes) -> Bucket:
        if len(self._items) >= self.capacity:
            self._items.pop(0)
        bucket = Bucket(payload)
        self._items.append(bucket)
        return bucket

    def snapshot(self) -> tuple[Bucket, ...]:
        return tuple(self._items)


class HerRuntime:
    """Safe user-space prototype for the proposed Her hardware VM stack.

    This runtime deliberately runs above Linux/KVM. It models deterministic
    requests, bounded memory buckets, fixed restraint values, and GUI transform
    directives without accessing privileged hardware directly.
    """

    STACK_ID = 413

    def __init__(self, restraint: float = 0.62, pool_capacity: int = 413) -> None:
        self.vector = PointInTimeVector(tick=0, restraint=restraint)
        self.pool = BucketPool(pool_capacity)
        self._handlers: dict[TransformDirective, Callable[[dict[str, Any]], Any]] = {
            TransformDirective.TRANSLATE_IO: self._translate,
            TransformDirective.SCALE_IO: self._scale,
            TransformDirective.ROTATE_IO: self._rotate,
            TransformDirective.SORT_IO: self._sort,
        }

    def request(self, request: Request) -> dict[str, Any]:
        encoded = repr((request.package, request.updates, request.payload)).encode("utf-8")
        bucket = self.pool.push(encoded)
        self.vector = PointInTimeVector(self.vector.tick + 1, self.vector.restraint)
        return {
            "stack": self.STACK_ID,
            "tick": self.vector.tick,
            "package": request.package,
            "updates": request.updates,
            "bucket": {"hex": bucket.hex, "bits": bucket.bits},
        }

    def inject(self, directive: TransformDirective, payload: dict[str, Any]) -> Any:
        return self._handlers[directive](payload)

    def _translate(self, payload: dict[str, Any]) -> dict[str, float]:
        return {
            axis: self.vector.clamp(float(payload.get(axis, 0.0)))
            for axis in ("x", "y", "z")
        }

    def _scale(self, payload: dict[str, Any]) -> float:
        return max(0.0, self.vector.clamp(float(payload.get("factor", 1.0))))

    def _rotate(self, payload: dict[str, Any]) -> dict[str, float]:
        return {
            axis: self.vector.clamp(float(payload.get(axis, 0.0)))
            for axis in ("pitch", "yaw", "roll")
        }

    def _sort(self, payload: dict[str, Any]) -> list[Any]:
        values = list(payload.get("values", []))
        return sorted(values, key=lambda item: (type(item).__name__, repr(item)))
