"""Command-line entry point: run once, or watch on an interval."""

import argparse
import asyncio
import sys
from pathlib import Path

from .checker import check_all
from .storage import init_db, save_results


def load_urls(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        print(f"URL file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return [
        line.strip()
        for line in p.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def print_results(results) -> None:
    for r in results:
        marker = "OK  " if r.ok else "FAIL"
        latency = f"{r.latency_ms}ms" if r.latency_ms is not None else "-"
        line = f"[{marker}] {r.url:<45} status={r.status} latency={latency}"
        if r.error:
            line += f" error={r.error}"
        print(line)


async def run_once(urls, concurrency, timeout, retries, db_path) -> list:
    await init_db(db_path)
    results = await check_all(urls, concurrency=concurrency, timeout=timeout, retries=retries)
    await save_results(results, db_path)
    print_results(results)
    return results


async def watch(urls, interval, concurrency, timeout, retries, db_path) -> None:
    await init_db(db_path)
    while True:
        results = await check_all(urls, concurrency=concurrency, timeout=timeout, retries=retries)
        await save_results(results, db_path)
        print_results(results)
        print(f"--- sleeping {interval}s ---")
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Async URL/API health checker")
    parser.add_argument("urls_file", nargs="?", default="urls.txt", help="File with one URL per line")
    parser.add_argument("--watch", action="store_true", help="Run continuously instead of once")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between checks in watch mode")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--db", default="health_checks.db")
    args = parser.parse_args()

    urls = load_urls(args.urls_file)
    if not urls:
        print("No URLs to check.", file=sys.stderr)
        sys.exit(1)

    try:
        if args.watch:
            asyncio.run(watch(urls, args.interval, args.concurrency, args.timeout, args.retries, args.db))
        else:
            asyncio.run(run_once(urls, args.concurrency, args.timeout, args.retries, args.db))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
