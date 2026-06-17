"""Core asyncio logic: concurrent checks with bounded concurrency and retries."""

import asyncio
import time
from typing import Iterable

import aiohttp

from .models import CheckResult

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 2
DEFAULT_CONCURRENCY = 10


async def check_one(
    session: aiohttp.ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> CheckResult:
    """Check a single URL, retrying with exponential backoff on failure.

    The semaphore caps how many of these run at once, so check_all can be
    handed thousands of URLs without opening thousands of sockets at once.
    """
    async with semaphore:
        attempt = 0
        last_error: str | None = None

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
                    await asyncio.sleep(0.2 * (2 ** attempt))  # 0.4s, 0.8s, 1.6s...

        return CheckResult(url=url, status="error", latency_ms=None, ok=False, error=last_error)


async def check_all(
    urls: Iterable[str],
    concurrency: int = DEFAULT_CONCURRENCY,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> list[CheckResult]:
    """Check many URLs concurrently and return results in the same order as `urls`.

    asyncio.gather preserves input order regardless of which task finishes first,
    which matters here since results get zipped back up with their source URLs.
    """
    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        tasks = [check_one(session, url, semaphore, timeout, retries) for url in urls]
        return await asyncio.gather(*tasks)
