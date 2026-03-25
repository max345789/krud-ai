# Architecture

## Control plane

The Python service owns:

- Device-code sign-in
- Trial/subscription state
- Chat session creation and message responses
- Release metadata for installers and updates

For local development it uses SQLite. The service boundaries match the production plan, so a Postgres-backed repository can replace the storage layer without changing the API.

## Local runtime

The Rust side is split into:

- `krud-cli`: user-facing terminal entrypoint
- `krud-core`: shared types, path discovery, auth storage, IPC messages
- `krudd`: background daemon listening on a Unix socket

The daemon is intentionally minimal in V1 scaffolding: it proves the socket/LaunchAgent contract and can be extended with queue runners later.

## Security model

- All shell commands surfaced by chat are proposals, not auto-executed actions.
- Login state is stored in the macOS Keychain through the `security` command.
- Background automation must be explicit and local.

