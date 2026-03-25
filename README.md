# Krud AI

Krud AI is a Mac-first terminal agent with:

- a Rust CLI: `krud`
- a Rust background daemon: `krudd`
- a FastAPI control plane for login, billing, chat orchestration, and release metadata

This repo now supports a full local MVP loop:

1. run the backend
2. log in from the CLI with browser approval
3. chat in the terminal
4. approve commands to run now or queue for the daemon
5. install/start the daemon with `launchd`
6. package release assets for the installer

## Layout

```text
krud-ai/
  backend/
  crates/
    krud-cli/
    krud-core/
    krudd/
  docs/
  install/
  launchd/
  scripts/
```

## MVP Quick Start

Backend:

```bash
cd /Users/sarath/Projects/krud-ai/backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Rust:

```bash
cd /Users/sarath/Projects/krud-ai
. "$HOME/.cargo/env"
cargo build -p krud-cli -p krudd
```

Login and chat:

```bash
cargo run -p krud-cli -- login
cargo run -p krud-cli -- chat "list files and show git status"
```

Daemon:

```bash
cargo run -p krud-cli -- daemon install
cargo run -p krud-cli -- daemon start
cargo run -p krud-cli -- status
```

Queue a task for the daemon:

```bash
cargo run -p krud-cli -- run "pwd"
sqlite3 ~/.krud/local.db "select id,command,status from local_tasks order by created_at desc limit 5;"
```

## Release Packaging

Create local installer assets:

```bash
cd /Users/sarath/Projects/krud-ai
chmod +x scripts/package_release.sh
./scripts/package_release.sh 0.1.0
cd dist/releases
python3 -m http.server 9000
```

If you want the backend manifest to point to the locally served assets:

```bash
export KRUD_DOWNLOAD_BASE_URL=http://127.0.0.1:9000
export KRUD_RELEASE_VERSION=0.1.0
```

## Environment

Root CLI example: [.env.example](/Users/sarath/Projects/krud-ai/.env.example)

Backend example: [backend/.env.example](/Users/sarath/Projects/krud-ai/backend/.env.example)

Important variables:

- `KRUD_API_BASE_URL`
- `KRUD_PUBLIC_BASE_URL`
- `KRUD_DOWNLOAD_BASE_URL`
- `KRUD_RELEASE_VERSION`
- `KRUD_BILLING_MODE`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

## What Works

- Browser device login
- Local trial/subscription enforcement
- Mock billing checkout and portal pages
- OpenAI-compatible chat planning with heuristic fallback
- Command approval in the CLI
- Queue-now-or-run-now behavior
- Local SQLite task/session history
- Background daemon processing through a Unix socket and `launchd`
- Release tarball packaging for the installer

## Validation

Backend:

```bash
cd /Users/sarath/Projects/krud-ai/backend
source .venv/bin/activate
pytest
python3 -m compileall app
```

Rust:

```bash
cd /Users/sarath/Projects/krud-ai
. "$HOME/.cargo/env"
cargo fmt --all
cargo check
```

## Next External Steps

These are not code gaps anymore; they require outside accounts or deployment:

- set `OPENAI_API_KEY` for live model-backed planning
- set Stripe secrets and `KRUD_BILLING_MODE=stripe` for live paid billing
- host the release assets behind a real public URL
- deploy the backend somewhere stable instead of localhost

More detailed walkthrough: [docs/mvp-runbook.md](/Users/sarath/Projects/krud-ai/docs/mvp-runbook.md)
