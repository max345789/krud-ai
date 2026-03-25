# Krud AI MVP Runbook

## 1. Start the backend

```bash
cd /Users/sarath/Projects/krud-ai/backend
cp .env.example .env
. .venv/bin/activate
uvicorn app.main:app --reload
```

## 2. Build the Rust binaries

```bash
cd /Users/sarath/Projects/krud-ai
. "$HOME/.cargo/env"
cargo build -p krud-cli -p krudd
```

## 3. Log in and chat

```bash
cargo run -p krud-cli -- login
cargo run -p krud-cli -- chat "list files and show git status"
```

## 4. Install and start the daemon

```bash
cargo run -p krud-cli -- daemon install
cargo run -p krud-cli -- daemon start
cargo run -p krud-cli -- status
```

## 5. Test background queueing

```bash
cargo run -p krud-cli -- run "pwd"
sqlite3 ~/.krud/local.db "select id,command,status from local_tasks order by created_at desc limit 5;"
```

## 6. Package release assets for the installer

```bash
cd /Users/sarath/Projects/krud-ai
chmod +x scripts/package_release.sh
./scripts/package_release.sh 0.1.0
cd dist/releases
python3 -m http.server 9000
```

Then set:

```bash
export KRUD_DOWNLOAD_BASE_URL=http://127.0.0.1:9000
```

## 7. Optional live AI

Set `OPENAI_API_KEY` in `backend/.env` and restart `uvicorn`.

## 8. Optional live Stripe

Set:

- `KRUD_BILLING_MODE=stripe`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

Then restart `uvicorn`.
