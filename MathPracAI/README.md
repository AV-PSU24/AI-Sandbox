# MathPracAI

A soft, code-font Algebra 2 practice generator powered by Python.

## Run Locally

From this folder, run:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Then open:

```text
http://localhost:8010
```

## Architecture Notes

- `app.py` creates the Flask app and registers route blueprints.
- `routes/practice_routes.py` handles practice/test request flow.
- `routes/auth_routes.py` handles login, logout, and signup.
- `routes/dashboard_routes.py` handles tutor/admin dashboards, profiles, workspaces, and code endpoints.
- `routes/milo_routes.py` handles the Milo AI Tutor HTTP endpoint.
- `views/auth_views.py`, `views/dashboard_views.py`, and `views/shared_views.py` handle HTML rendering helpers.
- `firebase_backend/config.py` initializes Firebase Admin SDK and Firestore.
- `firebase_backend/auth_service.py`, `firebase_backend/firestore_service.py`, and `firebase_backend/code_service.py` keep backend logic out of route files.
- `services/milo/` contains Milo session modeling, runtime selection, prompt assembly, context formatting, orchestration, and response shaping.
- `llm/client.py` exposes the provider-neutral LLM interface.
- `llm/gemini_client.py` contains Gemini-specific API communication.
- `prompts/milo/` contains editable Milo prompt contracts and runtime prompt assets.
- `scripts/smoke_milo.py` runs a no-cost Milo endpoint smoke with the LLM call stubbed.
- `scripts/smoke_llm.py` runs a live provider smoke for the configured LLM.
- `math_engine/generators.py` handles problem generation.
- `math_engine/models.py` handles the `Problem` object and serialization.
- `math_engine/validators.py` handles answer validation.
- `math_engine/renderers.py` handles practice/test HTML rendering.
- `math_engine/formatters.py` handles math text formatting.
- `static/script.js` handles browser-side interactions.
- `static/styles.css` handles styling.

## Environment

Create a local `.env` file in this folder. The application loads it automatically at startup, so developers do not need to manually export values in the terminal.

```text
FIREBASE_WEB_API_KEY=...
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
MATHPRACAI_SECRET_KEY=replace-in-production
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash-lite
```

`FIREBASE_SERVICE_ACCOUNT_JSON` can be used instead of `FIREBASE_SERVICE_ACCOUNT_PATH`.
`GEMINI_MODEL` defaults to `gemini-2.5-flash-lite` when omitted.
