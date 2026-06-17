# Async Health Checker

Check a list of URLs concurrently using asyncio.

## Setup

```
uv venv && uv pip install -e ".[dev]"
```

## Usage

CLI:
```
health-checker urls.txt
health-checker urls.txt --watch --interval 30
health-checker urls.txt --concurrency 20 --timeout 3 --retries 1
```

API:
```
uvicorn health_checker.api:app --reload
```

- `GET /health` — latest status per URL
- `GET /health/{url}/history?limit=50` — history for a URL
- `POST /check` — trigger a fresh check

## Tests

```
pytest tests/ -v
```
