# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the `OpenAIRealtime` MLLM config.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, parameters?: object }`.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, status: "started" }`.
- 400 if `OPENAI_API_KEY` is unset, or `channelName`/`rtcUid`/`userUid` invalid.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `startAgent(channelName, rtcUid, userUid) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope          | Required | Default                   |
| ----------------------- | -------------- | :------: | ------------------------- |
| `AGORA_APP_ID`          | backend        |    ✅    | —                         |
| `AGORA_APP_CERTIFICATE` | backend        |    ✅    | —                         |
| `OPENAI_API_KEY`        | backend        |    ✅    | — (validated at start)    |
| `OPENAI_MODEL`          | backend        |          | `gpt-4o-realtime-preview` |
| `AGENT_GREETING`        | backend        |          | built-in line             |
| `AGENT_BACKEND_URL`     | web (deploy)   |    ✅\*   | `http://localhost:8000` (dev) |
| `PORT`                  | backend (env only) |      | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## `OpenAIRealtime` MLLM config (`realtime_config.py`)

`build_realtime_mllm(api_key, model, greeting?, input_modalities?)` produces a vendor whose `to_config()` yields:

- `vendor: "openai"`, `api_key`, `params.model`
- `turn_detection: {"mode": "server_vad"}` (always set)
- `greeting_message` when `greeting` provided
- `input_modalities` when provided (e.g. `["text", "image"]`)

## Related Deep Dives

- [realtime_mllm_config](L2/realtime_mllm_config.md) — every field and the session options around it.
