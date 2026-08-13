# AIFriends

**English** | [简体中文](README.md)

> An open-source platform for creating and interacting with AI characters. Users can define a character's personality and voice, then continue the conversation through text or speech.

Live demo: [https://app7804.acapp.acwing.com.cn/](https://app7804.acapp.acwing.com.cn/)

![AIFriends screenshot](https://github.com/user-attachments/assets/5aea2de6-edbe-4649-adff-0104b3580a96)

## About

AIFriends is a full-stack LLM application built for learning, experimentation, and open-source collaboration. It uses a Vue 3 frontend and a Django backend. LangChain, LangGraph, and an OpenAI-compatible API power character conversations, tool calls, knowledge retrieval, and long-term memory. The chat endpoint streams both text and synthesized audio back to the browser.

The repository began as an LLM application development course project and has now returned to active maintenance. The current focus is reliable deployment, safe configuration, repeatable tests, and a smoother contributor experience.

## Features

- Create, edit, delete, share, and befriend AI characters
- Configure avatars, chat backgrounds, personalities, system prompts, and voices
- Stream character responses from `deepseek-v4-flash-202605`
- Call LangGraph tools for time lookup and LanceDB knowledge retrieval
- Include recent messages and update long-term character memory
- Authenticate with JWT login, registration, token refresh, and profile management
- Transcribe speech through Alibaba Cloud real-time ASR
- Synthesize streaming speech through Tencent Cloud TTS while preserving legacy Alibaba Cloud voices
- Install the official demo dataset with an idempotent Django management command

## August 2026 Maintenance Update

This maintenance cycle includes the following changes:

- Added Tencent Cloud streaming text-to-speech with signed requests, READY/FINAL event handling, and MP3 chunk delivery.
- Preserved voice compatibility: `tencent:<VoiceType>` selects Tencent Cloud, while `aliyun:<voice>` and unprefixed legacy values continue to use Alibaba Cloud.
- Updated character chat and memory generation to the active TokenHub model, `deepseek-v4-flash-202605`.
- Added four official demo characters, four Tencent Cloud voices, a default avatar, character artwork, and baseline system prompts.
- Fixed the post-build Django template updater for an ESM frontend package.
- Added model configuration, Tencent TTS protocol, and demo seeding tests. The backend suite currently contains 14 tests.
- Verified the deployment on a Tencent Cloud server with a real model response, a real Tencent Cloud MP3 synthesis request, and a public HTTP health check.

Further documentation:

- [Tencent Cloud streaming TTS guide (Chinese)](docs/tencent-cloud-tts.md)
- [Official demo content guide (Chinese)](docs/demo-content.md)

## Tech Stack

### Frontend

- Vue 3.5
- Vite 7
- Vue Router 4
- Pinia 3
- Tailwind CSS 4 + daisyUI 5
- Axios and VAD Web

### Backend and AI

- Python 3.12+
- Django 6 + Django REST Framework
- Simple JWT
- LangChain + LangGraph
- OpenAI-compatible model API (currently Tencent Cloud TokenHub)
- LanceDB vector storage
- SQLite
- WebSocket + Server-Sent Events

### External Services

- Tencent Cloud TokenHub for character chat and long-term memory
- Tencent Cloud Text To Speech for streaming MP3 audio
- Alibaba Cloud DashScope for real-time ASR and the existing TTS/voice management path

## Architecture

```text
Browser
  │
  ├─ Vue 3 SPA
  │    ├─ REST API: authentication, characters, friends, history
  │    └─ SSE: response text and Base64-encoded MP3 chunks
  │
  └─ Django + DRF
       ├─ LangGraph: character prompt, recent context, tool calls
       ├─ OpenAI-compatible API: DeepSeek model
       ├─ LanceDB: knowledge retrieval
       ├─ Tencent Cloud TTS / Alibaba Cloud ASR
       └─ SQLite + media: application data and user images
```

## Repository Layout

```text
AIFriends/
├── backend/
│   ├── backend/                  # Django settings and entry points
│   ├── web/
│   │   ├── management/commands/ # Demo content command
│   │   ├── demo_assets/         # Official characters and default images
│   │   ├── documents/           # Knowledge data and LanceDB integration
│   │   ├── models/              # Users, characters, friends, and messages
│   │   ├── views/               # REST, SSE, ASR, TTS, and AI graphs
│   │   └── test_*.py            # Backend tests
│   ├── media/                   # User uploads (not tracked by Git)
│   ├── static/                  # Vite build output
│   └── manage.py
├── frontend/
│   ├── src/components/          # Shared components
│   ├── src/views/               # Pages and feature components
│   ├── src/router/              # Routes
│   ├── src/stores/              # Pinia stores
│   └── src/js/                  # API and runtime configuration
├── docs/                        # Integration and maintenance guides
├── Lessons/                     # Course notes
├── scripts/                     # uWSGI and build helpers
├── nginx.conf                   # Example Nginx configuration
└── deploy-frontend.ps1          # Windows frontend deployment helper
```

## Local Development

### Requirements

- Python 3.12+
- Node.js 20.19+ or 22.12+
- npm

### 1. Clone the Repository

```bash
git clone https://github.com/ppshuX/AIFriends.git
cd AIFriends
```

### 2. Configure the Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Install dependencies and initialize the database:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
```

Create `backend/.env` and add the services you plan to use. Never commit real credentials:

```dotenv
# TokenHub / OpenAI-compatible chat API
API_BASE=https://tokenhub.tencentmaas.com/v1
API_KEY=replace-with-your-api-key

# Alibaba Cloud real-time ASR and legacy TTS
WSS_URL=replace-with-your-dashscope-websocket-url

# Required for tencent:<VoiceType>
TENCENT_TTS_APP_ID=replace-with-your-app-id
TENCENT_TTS_SECRET_ID=replace-with-your-secret-id
TENCENT_TTS_SECRET_KEY=replace-with-your-secret-key
```

Optionally install the official demo content. The command is idempotent and does not delete other users' data:

```bash
python manage.py seed_demo_content
```

Start Django:

```bash
python manage.py runserver
```

### 3. Configure the Frontend

Open `frontend/src/js/config/config.js`. For local split frontend/backend development, change:

```js
const platform = 'cloud'
```

to:

```js
const platform = 'vue'
```

Then start Vite:

```bash
cd ../frontend
npm ci
npm run dev
```

Open [http://localhost:5173/](http://localhost:5173/). Django runs at `http://127.0.0.1:8000/` by default.

### 4. Build the Frontend

```bash
cd frontend
npm run build
```

Vite writes the build to `backend/static/frontend/`. The `postbuild` script runs `scripts/update-django-static.cjs` and updates the static asset references in the Django SPA template.

## Tests

Run the complete backend suite:

```bash
cd backend
python manage.py test web --verbosity 2
```

Run the maintenance tests separately:

```bash
python manage.py test web.test_model_configuration --verbosity 2
python manage.py test web.test_tencent_tts --verbosity 2
python manage.py test web.test_seed_demo_content --verbosity 2
```

Check the production frontend build:

```bash
cd frontend
npm ci
npm run build
```

The Tencent TTS tests use a simulated WebSocket. They do not call Tencent Cloud or require credentials. A live integration test consumes cloud quota.

## Deployment

The public instance currently runs on a Tencent Cloud server. The tracked `nginx.conf`, `scripts/uwsgi.ini`, and `deploy-frontend.ps1` files are deployment references, not a one-command deployment system. Adapt them to the server path, domain, and process manager you use.

A recommended production flow is:

1. Install backend dependencies and run database migrations.
2. Build the frontend and run `python manage.py collectstatic --noinput`.
3. Keep `db.sqlite3`, `media/`, and LanceDB data on persistent storage, and back them up before an update.
4. Inject credentials through server environment variables, a read-only `.env`, or a secret manager.
5. Run Django behind Gunicorn/uWSGI and let Nginx serve HTTPS, static files, and media files.
6. After deployment, verify the home page, login, character chat, model response, and real TTS audio.

## Known Limits and Security Notes

- `backend/backend/settings.py` still contains course-oriented development defaults, including `DEBUG = True`, an example `SECRET_KEY`, and fixed hosts. Move these values to environment variables and run `python manage.py check --deploy` before a public deployment.
- SQLite is suitable for local development and small demonstrations. Evaluate PostgreSQL/MySQL and external object storage before running multiple application instances or serving higher traffic.
- Tencent Cloud support currently covers numeric built-in `VoiceType` values. Voice cloning `FastVoiceType` values are not supported.
- The bundled knowledge data and character prompts are examples. A public community needs explicit content safety, privacy, and minor protection policies.
- Cloud APIs consume quota and may incur charges. Configure budget alerts, request limits, least-privilege CAM users, and credential rotation.

## Contributing

Issues and pull requests are welcome. Before submitting a change, run:

```bash
cd backend
python manage.py test web --verbosity 2

cd ../frontend
npm ci
npm run build
```

Keep each contribution focused on a verifiable problem. Explain why the change is needed, how it was tested, and what users will notice. Do not commit `.env` files, databases, media uploads, IDE settings, or cloud credentials.

## License

AIFriends is available under the [MIT License](LICENSE).
