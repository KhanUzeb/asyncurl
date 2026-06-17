from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CheckResult:
    """Outcome of a single health check against one URL."""

    url: str
    status: int | str          # HTTP status code, or "error" if the request failed
    latency_ms: float | None   # round-trip time in milliseconds, None if it errored
    ok: bool                   # True if status < 400
    error: str | None = None
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
