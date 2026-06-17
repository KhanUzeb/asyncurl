from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CheckResult:
    url: str
    status: int | str
    latency_ms: float | None
    ok: bool
    error: Optional[str] = None          # TODO: consider using a dedicated exception type
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
