#!/usr/bin/env bash
# Craft Launcher Start-Skript

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Cargo / Rust Environment laden falls vorhanden
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
fi
export PATH="$HOME/.cargo/bin:$PATH"

python3 "$SCRIPT_DIR/launcher.py" "$@"

