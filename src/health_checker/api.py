"""FastAPI layer on top of the checker — same async functions, served over HTTP."""

from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException

from .checker import check_all
from .cli import load_urls
from .storage import history, init_db, latest_results, save_results

URLS_FILE = "urls.txt"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Async Health Checker", lifespan=lifespan)


@app.get("/health")
async def get_latest():
    """Most recent status per monitored URL."""
    return await latest_results()


@app.get("/health/{url:path}/history")
async def get_history(url: str, limit: int = 50):
    rows = await history(url, limit)
    if not rows:
        raise HTTPException(status_code=404, detail="No history for this URL")
    return rows


@app.post("/check")
async def trigger_check():
    """Run a fresh check against every URL in urls.txt right now."""
    urls = load_urls(URLS_FILE)
    results = await check_all(urls)
    await save_results(results)
    return [asdict(r) for r in results]
