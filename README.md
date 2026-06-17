# Async Health Checker

Check a list of URLs concurrently using asyncio — bounded concurrency,
retries with backoff, SQLite storage, CLI and HTTP API.

## Files

| File | What it does |
|------|-------------|
| `checker.py` | Core async logic — semaphore-bounded concurrent checks with retry backoff |
| `models.py` | `CheckResult` dataclass for a single check outcome |
| `storage.py` | Async SQLite read/write via aiosqlite |
| `cli.py` | Command-line entry point — one-shot or watch mode |
| `api.py` | FastAPI server exposing the checker over HTTP |
| `tests/test_checker.py` | Integration tests with a live aiohttp server |

## Setup

```bash
uv venv && uv pip install -e ".[dev]"
```

## Usage

```bash
health-checker urls.txt                          # one-shot
health-checker urls.txt --watch --interval 30    # every 30s
health-checker urls.txt --concurrency 20 --timeout 3 --retries 1
```

```
[OK  ] http://127.0.0.1:8767/ok      status=200 latency=3.1ms
[OK  ] http://127.0.0.1:8767/slow    status=200 latency=307.7ms
[FAIL] http://127.0.0.1:8767/broken  status=500 latency=2.2ms
```

## API

```bash
uvicorn health_checker.api:app --reload
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Latest status per URL |
| GET | `/health/{url}/history?limit=50` | History for one URL |
| POST | `/check` | Run a fresh check |

## Tests

```bash
pytest tests/ -v
```
