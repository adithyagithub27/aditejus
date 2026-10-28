"""Keep-alive relay for VERY slow machines: Claude Code -> this relay (:11435) -> Ollama (:11434).
With non-Anthropic providers, Claude Code stops a stream after 5 minutes with no bytes (API_FORCE_IDLE_TIMEOUT=0 turns
that off). On a busy 2-core CPU, a local model needs longer than that just to read Claude Code's ~12k-token prompt (measured). This relay answers streaming /v1/messages requests at once
and sends Anthropic-style `ping` events until Ollama's first bytes arrive, then passes Ollama's stream through unchanged.
Everything else is forwarded as is. The model, prompts and answers are untouched.
usage:
    python3 keepalive.py [--port 11435] [--upstream http://127.0.0.1:11434] [--log keepalive.log]
    OLLAMA_HOST=127.0.0.1:11435 ollama launch claude --model qwen3.5:2b
Logging is off unless you pass --log. Needs: pip install aiohttp"""
import argparse, asyncio, json, sys, time
from aiohttp import web, ClientSession, ClientTimeout

ap = argparse.ArgumentParser(description="keep-alive relay between Claude Code and Ollama")
ap.add_argument("--port", type=int, default=11435)
ap.add_argument("--upstream", default="http://127.0.0.1:11434")
ap.add_argument("--log", help="optional log file (timings only, no prompts)")
ARGS = ap.parse_args() if __name__ == "__main__" else ap.parse_args([])
UP = ARGS.upstream.rstrip("/")
PING = b'event: ping\ndata: {"type": "ping"}\n\n'


class _NoLog:
    def write(self, s):
        pass


LOG = open(ARGS.log, "a", buffering=1) if ARGS.log else _NoLog()
HOP = {"host", "content-length", "transfer-encoding", "connection", "accept-encoding"}


async def handle(req):
    body = await req.read()
    hdrs = {k: v for k, v in req.headers.items() if k.lower() not in HOP}
    url = UP + req.path_qs
    stream = False
    if req.method == "POST" and req.path.startswith("/v1/messages") and not req.path.endswith("count_tokens"):
        try:
            stream = bool(json.loads(body or b"{}").get("stream"))
        except Exception:
            pass
    sess = req.app["sess"]
    if not stream:
        async with sess.request(req.method, url, data=body, headers=hdrs) as r:
            data = await r.read()
            return web.Response(status=r.status, body=data, headers={k: v for k, v in r.headers.items() if k.lower() not in HOP})
    t0 = time.time(); LOG.write(f"{t0:.0f} stream start {len(body)}B\n")
    resp = web.StreamResponse(status=200, headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"})
    await resp.prepare(req)
    q = asyncio.Queue()

    async def pump():
        try:
            async with sess.request("POST", url, data=body, headers=hdrs) as r:
                if r.status != 200:
                    msg = (await r.read()).decode(errors="ignore")[:500]
                    err = {"type": "error", "error": {"type": "api_error", "message": f"ollama {r.status}: {msg}"}}
                    await q.put(b"event: error\ndata: " + json.dumps(err).encode() + b"\n\n"); return
                async for chunk in r.content.iter_any():
                    await q.put(chunk)
        except Exception as e:
            err = {"type": "error", "error": {"type": "api_error", "message": f"relay: {e!r}"}}
            await q.put(b"event: error\ndata: " + json.dumps(err).encode() + b"\n\n")
        finally:
            await q.put(None)

    task = asyncio.create_task(pump())
    first = True
    try:
        while True:
            try:
                chunk = await asyncio.wait_for(q.get(), timeout=15)
            except asyncio.TimeoutError:
                await resp.write(PING); continue
            if chunk is None:
                break
            if first:
                LOG.write(f"{time.time():.0f} first bytes after {time.time() - t0:.0f}s\n"); first = False
            await resp.write(chunk)
    except (ConnectionResetError, asyncio.CancelledError):
        task.cancel(); LOG.write(f"{time.time():.0f} client gone after {time.time() - t0:.0f}s\n"); raise
    LOG.write(f"{time.time():.0f} stream done in {time.time() - t0:.0f}s\n")
    await resp.write_eof()
    return resp


async def init():
    app = web.Application(client_max_size=64 << 20)
    app["sess"] = ClientSession(timeout=ClientTimeout(total=None, sock_read=None, sock_connect=30))
    app.router.add_route("*", "/{tail:.*}", handle)
    return app

if __name__ == "__main__":
    print(f"relay on http://127.0.0.1:{ARGS.port} -> {UP}", file=sys.stderr)
    web.run_app(init(), host="127.0.0.1", port=ARGS.port, print=None)
