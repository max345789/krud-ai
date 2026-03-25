#!/usr/bin/env sh
set -eu

API_BASE_URL="${KRUD_API_BASE_URL:-https://api.krud.ai}"
CHANNEL="${KRUD_CHANNEL:-stable}"
INSTALL_ROOT="${KRUD_INSTALL_ROOT:-$HOME/.krud}"
BIN_DIR="$INSTALL_ROOT/bin"
TMP_DIR="$(mktemp -d)"
MANIFEST="$TMP_DIR/release.json"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT INT TERM

arch="$(uname -m)"
case "$arch" in
  arm64) target="darwin-aarch64" ;;
  x86_64) target="darwin-x86_64" ;;
  *)
    echo "Unsupported macOS architecture: $arch" >&2
    exit 1
    ;;
esac

mkdir -p "$BIN_DIR"

echo "Fetching Krud AI release manifest from $API_BASE_URL ..."
curl -fsSL "$API_BASE_URL/v1/releases/latest?channel=$CHANNEL" -o "$MANIFEST"

asset_url="$(python3 - "$MANIFEST" "$target" <<'PY'
import json
import sys
manifest_path, target_name = sys.argv[1], sys.argv[2]
with open(manifest_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload["assets"][target_name])
PY
)"

archive="$TMP_DIR/krud.tar.gz"
echo "Downloading $asset_url ..."
curl -fsSL "$asset_url" -o "$archive"
tar -xzf "$archive" -C "$TMP_DIR"

install -m 0755 "$TMP_DIR/krud" "$BIN_DIR/krud"
install -m 0755 "$TMP_DIR/krudd" "$BIN_DIR/krudd"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    shell_profile="$HOME/.zshrc"
    printf '\nexport PATH="%s:$PATH"\n' "$BIN_DIR" >> "$shell_profile"
    echo "Added $BIN_DIR to PATH in $shell_profile"
    ;;
esac

cat <<EOF
Krud AI installed.

Next steps:
  1. Open a new terminal
  2. Run: krud login
  3. Optional daemon setup: krud daemon install && krud daemon start
EOF

