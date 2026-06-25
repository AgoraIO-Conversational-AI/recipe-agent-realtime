# 02 · Architecture

> Two co-located processes. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend owns Agora tokens and the agent session, attaching a single OpenAI Realtime MLLM.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds OpenAIRealtime MLLM via .with_mllm()
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → OpenAI Realtime (voice-to-voice, server_vad)
                                 │  agent speech → user's channel
                                 ▼
                              User hears realtime voice; RTM transcript + metrics → web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service, no mock vendor, no public tunnel — the MLLM is a single cloud-hosted model.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs.
2. Browser joins the RTC channel, then `POST /api/startAgent`; backend validates `OPENAI_API_KEY`, builds the MLLM, and starts an async agent session.
3. Agora routes user audio to OpenAI Realtime; the model streams voice-to-voice back into the channel.
4. RTM delivers transcript + metrics to the web UI.
5. `POST /api/stopAgent { agentId }` ends the session.

## Why no `llm/` service

The realtime recipe attaches a single `OpenAIRealtime` MLLM via `agora_agent` `.with_mllm()`. STT, reasoning, and TTS are all internal to the model — no cascading STT→LLM→TTS vendors. Trade-off: the recipe is **not zero-key**; `OPENAI_API_KEY` with Realtime access is required (validated at agent start, not server boot).

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, env, and the in-memory `_sessions` map keyed by `agent_id`.
- **`build_realtime_mllm()`** (`server/src/realtime_config.py`) — constructs the `OpenAIRealtime` vendor with `turn_detection={"mode": "server_vad"}` and optional `greeting_message` / `input_modalities`.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **MLLM-owned turn detection** — `server_vad` lives on the vendor; no top-level `turn_detection` on `AgoraAgent(...)`.
- **Key validated at `start()`** — server boots without `OPENAI_API_KEY`; `/startAgent` returns 400 until it is set.

## Related Deep Dives

- [realtime_mllm_config](L2/realtime_mllm_config.md) — full `OpenAIRealtime` vendor build and session options.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, transcript mapping.
