#!/usr/bin/env bash
# Einmaliges Setup-Skript für frische Ubuntu/Debian-Systeme:
# Installiert die benötigten System-Bibliotheken, Rust/Cargo und den Desktop-Menüeintrag.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "  🛠️  Craft Launcher – Automatische System-Einrichtung"
echo "=========================================================="

echo "--> [1/3] Installiere benötigte System-Pakete (apt)..."
sudo apt update
sudo apt install -y \
    python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    build-essential pkg-config curl git cmake \
    libasound2-dev libglib2.0-dev libgtk-3-dev \
    libwebkit2gtk-4.1-dev libclang-dev

echo ""
echo "--> [2/3] Prüfe Rust & Cargo..."
if ! command -v cargo &> /dev/null && [ ! -f "$HOME/.cargo/bin/cargo" ]; then
    echo "    Installiere Rust (rustup)..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
else
    echo "    ✅ Rust/Cargo ist bereits installiert."
fi

echo ""
echo "--> [3/3] Richte Anwendungsmenü-Starter ein..."
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/craft-launcher.desktop" <<EOF
[Desktop Entry]
Name=Craft Launcher
Comment=Schnellauswahl & Auto-Installer für Kreativ- und Office-Tools
Exec=$SCRIPT_DIR/run_launcher.sh
Icon=$SCRIPT_DIR/craft-launcher.svg
Terminal=false
Type=Application
Categories=Graphics;Office;AudioVideo;Development;
StartupNotify=true
EOF
chmod +x "$SCRIPT_DIR/run_launcher.sh" "$SCRIPT_DIR/launcher.py"

echo ""
echo "=========================================================="
echo "  ✅ Einrichtung abgeschlossen!"
echo "  🚀 Starte den Launcher mit: ./run_launcher.sh"
echo "     (Alle 15 Tools werden beim ersten Klick automatisch"
echo "      im Hintergrund geladen, gebaut und gestartet!)"
echo "=========================================================="
