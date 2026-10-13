import logging
import json

from octodig.observability import JsonLogFormatter


def test_json_logs_allowlist_operational_fields_only() -> None:
    record = logging.LogRecord("octodig.api", logging.INFO, __file__, 1, "ignored", (), None)
    record.event = "http_request"
    record.method = "POST"
    record.path = "/api/v1/runs/run_1"
    record.status_code = 202
    record.duration_ms = 12
    record.authorization = "Bearer private-token"
    record.query = "api_key=private"

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["event"] == "http_request"
    assert payload["path"] == "/api/v1/runs/run_1"
    assert "authorization" not in payload
    assert "private" not in json.dumps(payload)
