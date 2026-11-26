import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import realtime_config as rc  # noqa: E402


def test_builds_openai_realtime_config():
    cfg = rc.build_realtime_mllm("test-key", "gpt-realtime").to_config()
    assert cfg["vendor"] == "openai"
    assert cfg["api_key"] == "test-key"
    assert cfg["params"]["model"] == "gpt-realtime"
    assert cfg.get("turn_detection") is not None


def test_vision_variant_adds_input_modalities():
    cfg = rc.build_realtime_mllm("k", "gpt-realtime", input_modalities=["text", "image"]).to_config()
    assert cfg["input_modalities"] == ["text", "image"]
