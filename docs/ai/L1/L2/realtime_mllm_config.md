# Deep Dive — Realtime MLLM Config

> **When to Read This:** You are changing the model, turn detection, greeting, vision input modalities, audio codec, or any session option around the `OpenAIRealtime` MLLM. For the high-level picture, start at [02_architecture](../02_architecture.md).

This recipe replaces the cascading STT→LLM→TTS pipeline with a single voice-to-voice model attached via `agora_agent` `.with_mllm()`. The vendor lives in `server/src/realtime_config.py`; it is wired into the session in `server/src/agent.py`.

## The builder

`build_realtime_mllm(api_key, model, greeting=None, input_modalities=None) → OpenAIRealtime`

```python
kwargs = {
    "api_key": api_key,
    "model": model,                                  # OPENAI_MODEL, default gpt-4o-realtime-preview
    "turn_detection": {"mode": "server_vad"},        # always set, on the vendor
}
if greeting:
    kwargs["greeting_message"] = greeting
if input_modalities:
    kwargs["input_modalities"] = input_modalities    # e.g. ["text", "image"] for vision
return OpenAIRealtime(**kwargs)
```

`to_config()` (asserted in `tests/test_realtime_config.py`) yields:

- `vendor == "openai"`
- `api_key == <key>`
- `params.model == <model>`
- `turn_detection` is non-null
- `input_modalities == ["text", "image"]` when the vision variant is requested

## Turn detection (server_vad)

`turn_detection` is **vendor-owned**. The MLLM decides turn boundaries server-side. Consequences:

- Do **not** set a top-level `turn_detection` on `AgoraAgent(...)` — it is ignored under `.with_mllm()` and only adds confusion (see [07_gotchas](../07_gotchas.md)).
- To change VAD behavior, edit the `turn_detection` dict in the builder.

## No tools

The `OpenAIRealtime` MLLM exposes no tool/function-calling surface in this SDK. There is no tool registration path in this recipe. If a feature needs tools, it belongs in a cascading-vendor recipe, not here.

## How it is wired into the session

In `Agent.start()` (`agent.py`):

```python
mllm = build_realtime_mllm(self.openai_api_key, self.openai_model, greeting=self.greeting)
agora_agent = AgoraAgent(
    client=self.client,
    greeting=self.greeting,
    failure_message="Please wait a moment.",
    max_history=50,
    advanced_features={"enable_rtm": True},
    parameters=parameters,           # see below
).with_mllm(mllm)
session = agora_agent.create_async_session(
    channel=channel_name,
    agent_uid=str(agent_uid),
    remote_uids=[str(user_uid)],
    enable_string_uid=False,
    idle_timeout=30,
    expires_in=3600,
)
agent_id = await session.start()     # stored in self._sessions[agent_id]
```

## Session `parameters`

Set in `Agent.start()` and passed to `AgoraAgent`:

| Key                    | Value     | Why                                              |
| ---------------------- | --------- | ------------------------------------------------ |
| `audio_scenario`       | `chorus`  | Ultra-low-latency profile for web clients.       |
| `data_channel`         | `rtm`     | Transcript + metrics delivered over RTM.         |
| `enable_error_message` | `true`    | Surface agent-side errors to the client.         |
| `enable_metrics`       | `true`    | Emit pipeline metrics to the UI.                 |
| `output_audio_codec`   | optional  | Forwarded from `POST /startAgent` `parameters`.  |

## Adding vision

Pass `input_modalities=["text", "image"]` into `build_realtime_mllm()` (coverage already exists). Then expose it through `agent.py` (env or request parameter) if you want it configurable at runtime.

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
