#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-0.1.0}"
OUT_DIR="${ROOT_DIR}/dist/releases/${VERSION}"

source "${HOME}/.cargo/env"

cd "${ROOT_DIR}"
cargo build -p krud-cli -p krudd

mkdir -p "${OUT_DIR}/darwin-aarch64"

cp "${ROOT_DIR}/target/debug/krud" "${OUT_DIR}/darwin-aarch64/krud"
cp "${ROOT_DIR}/target/debug/krudd" "${OUT_DIR}/darwin-aarch64/krudd"

tar -czf "${OUT_DIR}/krud-darwin-aarch64.tar.gz" -C "${OUT_DIR}/darwin-aarch64" krud krudd

(
  cd "${OUT_DIR}"
  shasum -a 256 krud-darwin-aarch64.tar.gz > krud-checksums.txt
)

cat <<EOF
Release assets created:
  ${OUT_DIR}/krud-darwin-aarch64.tar.gz
  ${OUT_DIR}/krud-checksums.txt

To serve them locally:
  cd ${ROOT_DIR}/dist/releases
  python3 -m http.server 9000
EOF
