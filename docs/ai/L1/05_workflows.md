# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Change the agent prompt / greeting / model

1. Greeting: set `AGENT_GREETING` (env) or edit the default in `server/src/agent.py`.
2. Model: set `OPENAI_MODEL` (default `gpt-4o-realtime-preview`).
3. Other MLLM options (VAD mode, modalities): edit `build_realtime_mllm()` in `server/src/realtime_config.py`. See [realtime_mllm_config](L2/realtime_mllm_config.md).
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Add vision (image input modalities)

1. Pass `input_modalities=["text", "image"]` through to `build_realtime_mllm()` (test coverage already exists in `test_realtime_config.py`).
2. Wire the call site in `agent.py` if exposing it as an env/parameter.
3. Verify: `cd server && pytest tests -v`.

## Adjust session parameters (codec, scenario)

1. Edit the `parameters` dict in `Agent.start()` (`audio_scenario`, `data_channel`, `enable_metrics`, etc.). `output_audio_codec` is also accepted per-request via `parameters` on `POST /startAgent`.
2. Verify: `bun run verify:local:fastapi`.

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                 |
| ---------------------------- | ------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                 |
| Backend logic / MLLM config  | `bun run verify:backend` + `cd server && pytest tests -v`            |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`    |
| Anything end-to-end (local)  | `bun run verify:local`                                               |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-realtime` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.

## Related Deep Dives

- [realtime_mllm_config](L2/realtime_mllm_config.md) — MLLM build details.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/renewal/teardown.
