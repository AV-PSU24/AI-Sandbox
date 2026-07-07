import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from llm.client import LLMResponse


def fake_generate_text(prompt):
    return LLMResponse(
        text="Stubbed Milo reply.",
        model="stub-model",
        provider="stub",
        raw_response={"prompt": prompt},
    )


def main():
    app = create_app()
    client = app.test_client()

    with patch("services.milo.service.generate_text", fake_generate_text):
        response = client.post(
            "/ai-tutor/chat",
            json={"studentMessage": "Hello, say hi in one short sentence."},
        )
        payload = response.get_json()

        empty_response = client.post("/ai-tutor/chat", json={"studentMessage": ""})
        auth_response = client.get("/auth")

    print("POST /ai-tutor/chat status:", response.status_code)
    print("POST /ai-tutor/chat ok:", bool(payload and payload.get("ok") is True))
    print("POST /ai-tutor/chat helpStatus:", payload.get("helpStatus") if payload else None)
    print("Empty message status:", empty_response.status_code)
    print("GET /auth status:", auth_response.status_code)

    if response.status_code != 200 or not payload or payload.get("ok") is not True:
        return 1
    if empty_response.status_code != 400:
        return 1
    if auth_response.status_code >= 500:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
