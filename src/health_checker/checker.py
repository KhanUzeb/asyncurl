import asyncio
import time
from typing import Iterable

import aiohttp

from .models import CheckResult

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 2
DEFAULT_CONCURRENCY = 10

# FIXME: backoff should probably use jitter to avoid thundering herd
#        on mass restarts, but keeping it simple for now


async def check_one(
    session: aiohttp.ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> CheckResult:
    """Check a single URL, with retries + exponential backoff."""
    async with semaphore:
        attempt = 0
        last_error = None

        while attempt <= retries:
            start = time.perf_counter()
            try:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    latency = (time.perf_counter() - start) * 1000
                    return CheckResult(
                        url=url,
                        status=resp.status,
                        latency_ms=round(latency, 1),
                        ok=resp.status < 400,
                    )
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                attempt += 1
                if attempt <= retries:
                    await asyncio.sleep(0.2 * (2**attempt))

        return CheckResult(url=url, status="error", latency_ms=None, ok=False, error=last_error)


async def check_all(
    urls: Iterable[str],
    concurrency: int = DEFAULT_CONCURRENCY,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> list[CheckResult]:
    """Check many URLs concurrently. Preserves input order."""
    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        tasks = [check_one(session, url, semaphore, timeout, retries) for url in urls]
        return await asyncio.gather(*tasks)
