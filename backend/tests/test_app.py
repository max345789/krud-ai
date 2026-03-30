from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("KRUD_DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("KRUD_PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.setenv("KRUD_BILLING_MODE", "mock")

    from importlib import reload

    import app.api.routes
    import app.core.auth
    import app.core.config
    import app.core.db
    import app.main
    import app.services.billing
    import app.services.llm

    reload(app.core.config)
    reload(app.core.db)
    reload(app.core.auth)
    reload(app.services.llm)
    reload(app.services.billing)
    reload(app.api.routes)
    reload(app.main)
    return TestClient(app.main.app)


def test_device_flow_chat_and_billing(client: TestClient) -> None:
    start = client.post("/v1/device/start", json={"client_name": "pytest-cli"})
    assert start.status_code == 200
    device_payload = start.json()
    assert device_payload["user_code"]
    assert device_payload["verification_uri_complete"].startswith("http://testserver/cli-auth")

    complete = client.post(
        f"/v1/device/complete?user_code={device_payload['user_code']}",
        json={"email": "founder@dabcloud.in", "name": "Krud Founder"},
    )
    assert complete.status_code == 200

    poll = client.post("/v1/device/poll", json={"device_code": device_payload["device_code"]})
    assert poll.status_code == 200
    poll_payload = poll.json()
    assert poll_payload["status"] == "approved"
    token = poll_payload["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/v1/account/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "founder@dabcloud.in"
    assert me.json()["usage_events"] == 0

    session = client.post("/v1/chat/sessions", json={"title": "Terminal help"}, headers=headers)
    assert session.status_code == 200
    session_id = session.json()["session_id"]

    reply = client.post(
        f"/v1/chat/sessions/{session_id}/messages",
        json={"content": "please run git status and list files", "cwd": "/Users/sarath/Projects/krud-ai"},
        headers=headers,
    )
    assert reply.status_code == 200
    payload = reply.json()
    commands = [item["command"] for item in payload["command_proposals"]]
    assert "git status --short --branch" in commands
    assert "ls -la" in commands
    assert payload["provider"] in {"heuristic", "openai"}
    assert payload["usage"]["prompt_tokens"] > 0

    me_after = client.get("/v1/account/me", headers=headers)
    assert me_after.status_code == 200
    assert me_after.json()["usage_events"] == 1

    billing = client.get("/v1/billing", headers=headers)
    assert billing.status_code == 200
    assert billing.json()["subscription"]["status"] == "trialing"
    assert billing.json()["checkout_enabled"] is True

    checkout = client.post("/v1/billing/checkout", headers=headers)
    assert checkout.status_code == 200
    assert checkout.json()["mode"] == "mock"

    portal = client.post("/v1/billing/portal", headers=headers)
    assert portal.status_code == 200
    assert portal.json()["mode"] == "mock"

    webhook = client.post(
        "/v1/billing/webhook",
        json={"email": "founder@dabcloud.in", "status": "active", "customer_id": "cus_mock"},
    )
    assert webhook.status_code == 200
    assert webhook.json()["status"] == "active"

    subscription = client.get("/v1/account/subscription", headers=headers)
    assert subscription.status_code == 200
    assert subscription.json()["status"] == "active"
    assert subscription.json()["customer_id"] == "cus_mock"


def test_release_manifest(client: TestClient) -> None:
    response = client.get("/v1/releases/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "0.1.0"
    assert "darwin-aarch64" in payload["assets"]


def test_device_flow_uses_explicit_device_base_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KRUD_DATABASE_PATH", str(tmp_path / "test-device-url.db"))
    monkeypatch.setenv("KRUD_PUBLIC_BASE_URL", "https://api.dabcloud.in")
    monkeypatch.setenv("KRUD_DEVICE_BASE_URL", "https://dabcloud.in")
    monkeypatch.setenv("KRUD_BILLING_MODE", "mock")

    from importlib import reload

    import app.api.routes
    import app.core.auth
    import app.core.config
    import app.core.db
    import app.main
    import app.services.billing
    import app.services.llm

    reload(app.core.config)
    reload(app.core.db)
    reload(app.core.auth)
    reload(app.services.llm)
    reload(app.services.billing)
    reload(app.api.routes)
    reload(app.main)

    client = TestClient(app.main.app)
    start = client.post("/v1/device/start", json={"client_name": "pytest-cli"})
    assert start.status_code == 200
    payload = start.json()
    assert payload["verification_uri"] == "https://dabcloud.in/cli-auth"
    assert payload["verification_uri_complete"].startswith("https://dabcloud.in/cli-auth")
