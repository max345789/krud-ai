#!/usr/bin/env sh
# krud installer — https://dabcloud.in/install.sh | sh
set -e

KRUD_API="${KRUD_API:-https://api.dabcloud.in}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

# ── detect platform ────────────────────────────────────────────────────────────
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Darwin)
    case "$ARCH" in
      arm64)  PLATFORM="darwin-aarch64" ;;
      x86_64) PLATFORM="darwin-x86_64" ;;
      *)      echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  Linux)
    case "$ARCH" in
      x86_64) PLATFORM="linux-x86_64" ;;
      *)      echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
esac

# ── fetch latest release info ──────────────────────────────────────────────────
echo "Fetching latest krud release..."
RELEASE="$(curl -fsSL "$KRUD_API/v1/releases/latest")"

# extract version and asset URL with basic shell tools (no jq required)
VERSION="$(echo "$RELEASE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)"
ASSET_URL="$(echo "$RELEASE" | grep -o "\"$PLATFORM\":\"[^\"]*\"" | cut -d'"' -f4)"

if [ -z "$ASSET_URL" ]; then
  echo "No binary available for platform: $PLATFORM" >&2
  exit 1
fi

echo "Installing krud $VERSION for $PLATFORM..."

# ── download & install ─────────────────────────────────────────────────────────
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

curl -fsSL "$ASSET_URL" -o "$TMP_DIR/krud.tar.gz"
tar -xzf "$TMP_DIR/krud.tar.gz" -C "$TMP_DIR"

mkdir -p "$INSTALL_DIR"
cp "$TMP_DIR/krud" "$INSTALL_DIR/krud"
chmod +x "$INSTALL_DIR/krud"

# ── PATH hint ─────────────────────────────────────────────────────────────────
case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *)
    echo ""
    echo "Add krud to your PATH:"
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
    ;;
esac

echo ""
echo "krud $VERSION installed to $INSTALL_DIR/krud"
echo ""
echo "Get started:"
echo "  krud login"
echo "  krud chat"
