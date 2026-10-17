from __future__ import annotations

import json

import easel_mcp_server as server


def test_publish_is_fail_closed_without_explicit_host_gate():
    result = json.loads(server.easel_publish("bilibili", "t", "b", [], "", "x"))
    assert result["ok"] is False
    assert result["state"] == "blocked"
    assert "闸" in result["error"]


def test_output_path_traversal_and_system_paths_are_rejected():
    result = json.loads(server.easel_read_output("../cookies.json"))
    assert result["ok"] is False
    result = json.loads(server.easel_read_output("_mcp/confirmations.json"))
    assert result["ok"] is False


def test_publish_plan_reports_platform_constraints():
    result = json.loads(server.easel_plan_publish(
        ["xiaohongshu"], "标题" * 30, "正文", [str(i) for i in range(12)], "article"
    ))
    assert result["ok"] is True
    warnings = result["dispatch"][0]["warnings"]
    assert any("标题" in item for item in warnings)
    assert any("标签" in item for item in warnings)
    assert any("类型" in item for item in warnings)


def test_confirmation_is_one_time_and_payload_bound(tmp_path, monkeypatch):
    confirm_file = tmp_path / "confirmations.json"
    monkeypatch.setattr(server, "CONFIRM_FILE", confirm_file)
    payload = {"platform": "bilibili", "title": "T", "body": "B", "media": [], "tags": ""}
    issued = server._issue_confirmation("publish", payload, ttl=60)
    server._consume_confirmation(issued["confirmation_id"], "publish", payload)
    try:
        server._consume_confirmation(issued["confirmation_id"], "publish", payload)
    except PermissionError:
        pass
    else:
        raise AssertionError("confirmation must be one-time")


def test_low_level_schema_preserves_optional_arrays():
    schema = server._schema_for_callable(server.easel_plan_publish)
    assert schema["properties"]["platforms"] == {"type": "array", "items": {"type": "string"}}
    assert schema["properties"]["tags"] == {"type": "array", "items": {"type": "string"}}
