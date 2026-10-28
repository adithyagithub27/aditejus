# Claude Code free with Ollama (local models)

Code and commands for the ADITEJUS tutorial **"Claude Code Free with Ollama: Beginner Setup (2026)"**.

**Honest note:** this runs the Claude Code *tool* (the coding agent in your terminal) with a free open model on your own computer. It is **not** Anthropic's Claude model. Local models cost nothing to run; Ollama's cloud models are paid per use.

- Video: on the ADITEJUS channel, https://www.youtube.com/@aditejus (publishes Thu 5 Nov 2026)
- Tested with: Ollama 0.40.11, Claude Code 2.1.311, `qwen3.5:2b` (27 Oct 2026)

## Setup (steps 1–4, as in the video)

1. Install Ollama: https://ollama.com (Linux: `curl -fsSL https://ollama.com/install.sh | sh`)
2. Install Claude Code (official quickstart: https://code.claude.com/docs/en/quickstart)
   ```
   curl -fsSL https://claude.ai/install.sh | bash      # macOS / Linux / WSL
   irm https://claude.ai/install.ps1 | iex             # Windows PowerShell
   ```
3. Pull a model that supports **tools** (Claude Code calls tools to read and edit files):
   ```
   ollama pull qwen3.5:2b      # 2.7 GB; try qwen3.5:4b or qwen3.5:9b if you have more memory
   ```
3b. **Raise the context length** (the step most guides skip). Unless you have a big GPU, Ollama gives models a 4,096-token context by default, and Claude Code's prompt is far larger, so Ollama silently cuts it. In our test with default settings, Ollama logged `truncating input prompt limit=2050 prompt=24073`. Ollama recommends at least 64k for coding tools:
   - Ollama app: Settings, move the context length slider.
   - Or start the server with: `OLLAMA_CONTEXT_LENGTH=64000 ollama serve`
4. Go into your project and launch:
   ```
   cd expense-tracker
   ollama launch claude --model qwen3.5:2b
   ```

### Manual setup (what `ollama launch` does for you)

```
export ANTHROPIC_AUTH_TOKEN=ollama
export ANTHROPIC_API_KEY=""
export ANTHROPIC_BASE_URL=http://localhost:11434
claude --model qwen3.5:2b
```

## The yellow "model isn't recognized" warning

When Claude Code starts on a local model you'll see:
`⚠ Model "qwen3.5:2b" isn't recognized · context assumed to be 200k tokens`
This is normal. Claude Code doesn't know the local model, so it assumes a 200k-token context. Ollama only gives the model the context length you set (we used 32k; Ollama recommends 64k for coding tools). In a long session Ollama may therefore cut the conversation before Claude Code decides to summarise it. So:
- set `OLLAMA_CONTEXT_LENGTH` (step 3b) as high as your RAM allows, and
- run `/compact` in Claude Code when a session gets long.

The header also says "Claude API": that's the kind of API Claude Code is talking to. Ollama speaks the same Anthropic-style API, but every request goes to `localhost`, not to Anthropic.

## The demo project

`expense-tracker/` is the tiny project from the video: `expenses.csv` plus `tracker.py`, which prints the total.
```
python3 tracker.py      # 5 expenses, total Rs 1109
```

## Notes

- **Use a tool-capable model.** With an older chat model such as `qwen2.5:3b`, `ollama launch` warns that it "does not work well with Claude Code".
- **Speed:** Claude Code sends a large prompt with every request (12,600 to 24,000 tokens in our tests), so a small CPU-only machine is slow. More cores, Apple silicon or a GPU help a lot.
- **Context:** a bigger context window needs more RAM. On our small test machine we used 32k (`OLLAMA_CONTEXT_LENGTH=32768`).
- **Small models need explicit steps.** In the video, "What does this project do?" made qwen3.5:2b ask for the files instead of reading them; "Read tracker.py, then tell me..." worked.
- **Permissions:** Claude Code asks before it edits files or runs commands. Read every change before you approve it, and don't turn permission checks off on your real machine.

## Very slow machine? `keepalive.py`

With providers other than Anthropic's own API (Ollama included), Claude Code stops a streaming reply when no bytes arrive for 5 minutes. On our busy 2-core test machine, the local model needed longer than that just to read Claude Code's prompt, so the requests timed out. `keepalive.py` is a small relay that sits between Claude Code and Ollama: it starts each streaming reply at once and sends `ping` events until Ollama's first real bytes arrive, then passes Ollama's answer through unchanged. The model, prompts and answers are not touched.

Most laptops don't need it. Use it only if you see repeated "API error · Retrying" messages on a slow machine.

```
pip install aiohttp
python3 keepalive.py                       # relay on 127.0.0.1:11435 -> Ollama on 127.0.0.1:11434
OLLAMA_HOST=127.0.0.1:11435 ollama launch claude --model qwen3.5:2b
```

Options: `--port` (default 11435), `--upstream` (default `http://127.0.0.1:11434`), `--log FILE` (optional; logs timings only, never prompts). The relay listens on 127.0.0.1 only.

Simpler alternative: turn that 5-minute idle limit off with `export API_FORCE_IDLE_TIMEOUT=0` (Claude Code docs, environment variables). `API_TIMEOUT_MS` (default 10 minutes) is a separate request timeout; raise it too if requests still time out.

## How the video was recorded

All terminal screens in the video are real captures (27 Oct 2026) of Claude Code 2.1.311 + Ollama 0.40.11 + `qwen3.5:2b` on a busy 2-core cloud CPU machine with no GPU. Waiting times were cut and labelled. We ran Ollama with `OLLAMA_CONTEXT_LENGTH=32768` (step 3b). Two machine-specific settings we needed there, which a normal laptop shouldn't need:
- `keepalive.py` (above), because the first replies took longer than Claude Code's 5-minute stream idle limit;
- the model's `num_thread` set to 1 (a Modelfile with `PARAMETER num_thread 1`), because the 2 CPU cores were shared with other jobs and 2 threads were about 7x slower than 1.

`expense-tracker/tracker_after_claude_code.py` is the file exactly as Claude Code left it at the end of the video.
