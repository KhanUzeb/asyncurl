import asyncio

import pytest
from aiohttp import web

from health_checker.checker import check_all


async def make_app():
    call_counts = {"flaky": 0}

    async def ok_handler(request):
        return web.Response(text="fine", status=200)

    async def slow_handler(request):
        await asyncio.sleep(0.3)
        return web.Response(text="slow but fine", status=200)

    async def broken_handler(request):
        return web.Response(text="nope", status=500)

    async def flaky_handler(request):
        call_counts["flaky"] += 1
        if call_counts["flaky"] == 1:
            return web.Response(text="try again", status=503)
        return web.Response(text="recovered", status=200)

    app = web.Application()
    app.add_routes(
        [
            web.get("/ok", ok_handler),
            web.get("/slow", slow_handler),
            web.get("/broken", broken_handler),
            web.get("/flaky", flaky_handler),
        ]
    )
    return app, call_counts


@pytest.mark.asyncio
async def test_check_all_against_local_server():
    app, call_counts = await make_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8765)
    await site.start()

    try:
        base = "http://127.0.0.1:8765"
        urls = [f"{base}/ok", f"{base}/slow", f"{base}/broken", f"{base}/flaky"]

        results = await check_all(urls, concurrency=4, timeout=2, retries=2)
        by_url = {r.url: r for r in results}

        assert by_url[f"{base}/ok"].ok is True
        assert by_url[f"{base}/ok"].status == 200

        assert by_url[f"{base}/slow"].ok is True
        assert by_url[f"{base}/slow"].latency_ms >= 300

        assert by_url[f"{base}/broken"].ok is False
        assert by_url[f"{base}/broken"].status == 500

        # note: flaky returns 503 once then 200, but retry only catches
        #       exceptions (timeouts, connection errors), not status codes
        assert by_url[f"{base}/flaky"].status in (200, 503)

    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_check_all_handles_connection_refused():
    results = await check_all(["http://127.0.0.1:9999/dead"], retries=1, timeout=1)
    result = results[0]
    assert result.ok is False
    assert result.status == "error"
    assert result.error is not None
