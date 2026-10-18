#!/usr/bin/env bash
# DeckCraft Starter & Auto-Patcher:
# Stellt sicher, dass alle Linux-/Proxy-/Auth-Fixes nach dem Entpacken angewendet sind
# und startet anschließend Backend (FastAPI) & Frontend (Next.js).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Falls aus dem Haupt-Repo (/scripts/run_deckcraft.sh) aufgerufen, wechsle in workspace/DeckCraft-master
if [ -d "$SCRIPT_DIR/../workspace/DeckCraft-master" ] && [ "$(basename "$SCRIPT_DIR")" = "scripts" ]; then
    DECKCRAFT_DIR="$(cd "$SCRIPT_DIR/../workspace/DeckCraft-master" && pwd)"
else
    DECKCRAFT_DIR="$SCRIPT_DIR"
fi

cd "$DECKCRAFT_DIR" || exit 1

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# Pflicht-Umgebungsvariablen für DeckCraft Backend & Frontend setzen
export APP_DATA_DIRECTORY="$DECKCRAFT_DIR/app_data"
export TEMP_DIRECTORY="/tmp/deckcraft"
export USER_CONFIG_PATH="$APP_DATA_DIRECTORY/userConfig.json"
export FAST_API_INTERNAL_URL="http://127.0.0.1:8000"
export CAN_CHANGE_KEYS="true"
export DISABLE_AUTH="true"
export DISABLE_ANONYMOUS_TELEMETRY="true"

# Benötigte App-Data-Ordner und initiale userConfig.json anlegen
mkdir -p "$APP_DATA_DIRECTORY"/{exports,images,uploads,fonts,pptx-to-html} "$TEMP_DIRECTORY"
if [ ! -f "$USER_CONFIG_PATH" ]; then
    echo "{}" > "$USER_CONFIG_PATH"
fi

# Auto-Patches für frische GitHub-ZIP-Entpackungen unter Linux anwenden:
# 1. providers.tsx: '../store/store' -> '@/state/store'
if [ -f "packages/web/app/providers.tsx" ]; then
    sed -i "s|from '../store/store'|from '@/state/store'|g" packages/web/app/providers.tsx
fi
# 2. Home.tsx: './OnBoarding/DeckCraftMode' -> './OnBoarding/deckcraftMode' (Linux Case-Sensitivity)
if [ -f "packages/web/shared/Home.tsx" ]; then
    sed -i 's|./OnBoarding/DeckCraftMode|./OnBoarding/deckcraftMode|g' packages/web/shared/Home.tsx
fi
# 3. mixpanel.ts: Deaktiviere hartcodierten Mixpanel-Token ohne Persistenz
if [ -f "packages/web/lib/mixpanel.ts" ]; then
    sed -i "s|const MIXPANEL_TOKEN = 'd726e8bea8ec147f4c7720060cb2e6d1';|const MIXPANEL_TOKEN = process.env.NEXT_PUBLIC_MIXPANEL_TOKEN || '';|g" packages/web/lib/mixpanel.ts
fi

echo "=========================================================="
echo "  🎴 Starte DeckCraft (AI Presentation Generator)"
echo "  📂 Verzeichnis: $DECKCRAFT_DIR"
echo "  💾 App-Daten:   $APP_DATA_DIRECTORY"
echo "=========================================================="

# Alte noch laufende DeckCraft-Prozesse auf Port 8000/3000 sauber beenden
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true

# 1. Python Backend (FastAPI) starten
echo ""
echo "--> [1/2] Starte Backend Server (FastAPI auf Port 8000)..."
cd "$DECKCRAFT_DIR/packages/api" || exit 1
uv run uvicorn server:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Trap: Bei Beenden des Fensters auch das Backend stoppen
trap "echo 'Stoppe Backend...'; kill $BACKEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

# Warten bis Backend auf Port 8000 antwortet (max. 15 Sekunden)
for _ in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/v1/auth/status >/dev/null 2>&1; then
        echo "    ✅ Backend (Login- & API-Service) ist bereit!"
        break
    fi
    sleep 0.5
done

# 2. Web Frontend (Next.js) vorbereiten und starten
cd "$DECKCRAFT_DIR/packages/web" || exit 1

if [ ! -d "node_modules" ]; then
    echo ""
    echo "--> [2/2] Installiere Frontend-Abhängigkeiten (npm install - nur beim ersten Mal)..."
    npm install
fi

echo ""
echo "--> [2/2] Starte Frontend Server auf http://localhost:3000..."
echo "    🌐 Öffne Browser unter: http://localhost:3000"
echo ""

# Nach 3 Sekunden Browser automatisch öffnen
( sleep 3 && xdg-open "http://localhost:3000" 2>/dev/null || true ) &

npm run dev
