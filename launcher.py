#!/usr/bin/env python3
"""
Craft Launcher - Schnellauswahl, Auto-Installer & Prozess-Manager für Kreativ- und Office-Tools
Beinhaltet:
- Original-App-Icons (aus icons/*.png)
- Vollautomatische 1-Klick-Bereitstellung (GitHub-Download -> Entpacken -> Kompilieren -> Direktstart)
- Option 1: Speicherplatz-Turbo (bereinigt Rust-Compiler-Zwischendateien deps/build/incremental, spart ~28 GB)
- Option 4: Favoriten (⭐), "Zuletzt verwendet"-Sortierung & Umschalter Liste (☰) <-> Kachel-Grid (⊞)
- Option 5: Neues Tool direkt per GitHub-URL hinzufügen (inkl. Auto-Erkennung & Icon-Download)
- Option 6: Live-Prozess-Überwachung ("🟢 Aktiv"-Badge + 1-Klick "⏹️ Stopp"-Button)
"""

import os
import re
import sys
import time
import json
import signal
import zipfile
import threading
import subprocess
import shutil
import glob
import urllib.request
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "tools_config.json"
VERSIONS_PATH = BASE_DIR / ".tool_versions.json"
AI_CONFIG_PATH = BASE_DIR / ".ai_config.json"
ICONS_DIR = BASE_DIR / "icons"
DEFAULT_WORKSPACE_DIR = BASE_DIR / "workspace"

for extra_bin in [Path.home() / ".local" / "bin", Path.home() / ".cargo" / "bin"]:
    if extra_bin.exists() and str(extra_bin) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{extra_bin}:{os.environ.get('PATH', '')}"

CSS_DATA = b"""
window {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

headerbar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    color: #cdd6f4;
    padding: 6px;
}

headerbar .title {
    font-weight: bold;
    font-size: 15px;
    color: #cdd6f4;
}

headerbar .subtitle {
    font-size: 11px;
    color: #a6adc8;
}

.search-box {
    border-radius: 8px;
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    padding: 6px 12px;
}

.search-box:focus {
    border-color: #89b4fa;
}

.category-bar {
    background-color: #181825;
    padding: 8px 16px;
    border-bottom: 1px solid #313244;
}

.filter-btn {
    border-radius: 20px;
    background-color: #313244;
    color: #bac2de;
    border: none;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 500;
}

.filter-btn:checked, .filter-btn:active {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
}

.filter-btn:hover {
    background-color: #45475a;
    color: #cdd6f4;
}

.status-banner {
    background-color: #11111b;
    padding: 6px 16px;
    border-bottom: 1px solid #313244;
    font-size: 11px;
    color: #a6adc8;
}

.tool-card {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 12px;
    padding: 12px 14px;
    margin: 5px 10px;
    transition: all 150ms ease;
}

.tool-card-grid {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 12px;
    padding: 12px;
    margin: 4px;
    transition: all 150ms ease;
}

.tool-card:hover, .tool-card-grid:hover {
    border-color: #89b4fa;
    background-color: #1e1e2e;
}

.tool-card-running {
    border-color: #a6e3a1;
}

.icon-badge {
    border-radius: 12px;
    min-width: 48px;
    min-height: 48px;
    font-size: 26px;
}

.tool-title {
    font-size: 15px;
    font-weight: bold;
    color: #cdd6f4;
}

.tool-subtitle {
    font-size: 11px;
    color: #a6adc8;
    background-color: #313244;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
}

.tool-desc {
    font-size: 12px;
    color: #a6adc8;
    margin-top: 3px;
}

.badge-status-ready {
    background-color: rgba(166, 227, 161, 0.15);
    color: #a6e3a1;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}

.badge-status-running {
    background-color: rgba(166, 227, 161, 0.28);
    color: #a6e3a1;
    border: 1px solid rgba(166, 227, 161, 0.5);
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}

.badge-status-zipped {
    background-color: rgba(249, 226, 175, 0.15);
    color: #f9e2af;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}

.badge-update {
    background-color: rgba(250, 179, 135, 0.2);
    color: #fab387;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}

.badge-ai {
    background-color: rgba(203, 166, 247, 0.18);
    color: #cba6f7;
    border: 1px solid rgba(203, 166, 247, 0.4);
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}

.btn-primary {
    background-color: #89b4fa;
    color: #11111b;
    border-radius: 8px;
    font-weight: bold;
    padding: 5px 14px;
    border: none;
}

.btn-primary:hover {
    background-color: #b4befe;
}

.btn-stop {
    background-color: #f38ba8;
    color: #11111b;
    border-radius: 8px;
    font-weight: bold;
    padding: 5px 12px;
    border: none;
}

.btn-stop:hover {
    background-color: #eba0ac;
}

.btn-update {
    background-color: #fab387;
    color: #11111b;
    border-radius: 8px;
    font-weight: bold;
    padding: 5px 12px;
    border: none;
}

.btn-update:hover {
    background-color: #f9e2af;
}

.btn-secondary {
    background-color: #313244;
    color: #cdd6f4;
    border-radius: 8px;
    padding: 5px 9px;
    border: none;
}

.btn-secondary:hover {
    background-color: #45475a;
}

.btn-star {
    background: transparent;
    border: none;
    padding: 2px 4px;
    font-size: 15px;
    box-shadow: none;
}

.btn-star:hover {
    background-color: #313244;
    border-radius: 6px;
}
"""


def check_command_available(cmd_name):
    return shutil.which(cmd_name) is not None


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden von {CONFIG_PATH}: {e}", file=sys.stderr)
    return {"workspace_dir": "workspace", "view_mode": "list", "tools": []}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Fehler beim Speichern von {CONFIG_PATH}: {e}", file=sys.stderr)


def load_versions():
    if VERSIONS_PATH.exists():
        try:
            with open(VERSIONS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_versions(ver):
    try:
        with open(VERSIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(ver, f, indent=2)
    except Exception as e:
        print(f"Fehler beim Speichern der Versionen: {e}", file=sys.stderr)


DEFAULT_AI_CONFIG = {
    "active_provider": "google",
    "auto_update_models": True,
    "last_checked": 0,
    "providers": {
        "google": {
            "name": "Google Gemini",
            "api_key": "",
            "model": "gemini-2.5-pro",
            "latest_model": "gemini-2.5-pro",
            "available_models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
        },
        "openai": {
            "name": "OpenAI (ChatGPT / Codex)",
            "api_key": "",
            "model": "gpt-4.1",
            "latest_model": "gpt-4.1",
            "available_models": ["gpt-4.1", "gpt-4o", "o3", "o4-mini"]
        },
        "anthropic": {
            "name": "Anthropic Claude",
            "api_key": "",
            "model": "claude-sonnet-4-20250514",
            "latest_model": "claude-sonnet-4-20250514",
            "available_models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-7-sonnet-latest"]
        },
        "xai": {
            "name": "xAI Grok",
            "api_key": "",
            "model": "grok-3",
            "latest_model": "grok-3",
            "available_models": ["grok-3", "grok-3-mini"]
        },
        "ollama": {
            "name": "Ollama (Lokal & Kostenlos)",
            "url": "http://localhost:11434",
            "model": "llama3.3",
            "latest_model": "llama3.3",
            "available_models": ["llama3.3", "qwen2.5-coder", "deepseek-r1", "gemma3"]
        }
    },
    "media_keys": {
        "pexels_api_key": "",
        "pixabay_api_key": "",
        "fal_api_key": ""
    }
}


def load_ai_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_AI_CONFIG))
    if AI_CONFIG_PATH.exists():
        try:
            with open(AI_CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg["active_provider"] = saved.get("active_provider", cfg["active_provider"])
            cfg["auto_update_models"] = saved.get("auto_update_models", True)
            cfg["last_checked"] = saved.get("last_checked", 0)
            for pid, pdata in saved.get("providers", {}).items():
                if pid in cfg["providers"] and isinstance(pdata, dict):
                    cfg["providers"][pid].update(pdata)
            if isinstance(saved.get("media_keys"), dict):
                cfg["media_keys"].update(saved["media_keys"])
        except Exception as e:
            print(f"Fehler beim Laden von {AI_CONFIG_PATH}: {e}", file=sys.stderr)
    return cfg


def save_ai_config(cfg: dict):
    try:
        with open(AI_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.chmod(AI_CONFIG_PATH, 0o600)
    except Exception as e:
        print(f"Fehler beim Speichern von {AI_CONFIG_PATH}: {e}", file=sys.stderr)


def fetch_provider_latest_models(provider_id: str, pdata: dict) -> tuple[str | None, list[str]]:
    """
    Fragt live die offizielle Modell-API des jeweiligen KI-Anbieters ab,
    ermittelt alle verfügbaren Chat-/Generierungsmodelle und bestimmt automatisch
    das aktuellste Flaggschiff-Modell (latest_model).
    """
    api_key = (pdata.get("api_key") or "").strip()
    try:
        if provider_id == "google":
            if not api_key:
                return None, []
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "CraftLauncher/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                methods = m.get("supportedGenerationMethods", [])
                name = m.get("name", "").replace("models/", "")
                if "generateContent" in methods and name.startswith("gemini-"):
                    if any(skip in name for skip in ("embedding", "aqa", "vision", "tts", "image", "1.0")):
                        continue
                    models.append(name)
            if not models:
                return None, []

            def gemini_rank(m_name: str):
                ver_m = re.search(r"gemini-(\d+)\.(\d+)", m_name)
                major = int(ver_m.group(1)) if ver_m else 1
                minor = int(ver_m.group(2)) if ver_m else 0
                is_stable = "exp" not in m_name and "preview" not in m_name
                is_pro = "-pro" in m_name and "lite" not in m_name
                is_flash = "-flash" in m_name and "lite" not in m_name
                return (major, minor, is_stable, is_pro, is_flash, m_name)

            models_sorted = sorted(set(models), key=gemini_rank, reverse=True)
            return models_sorted[0], models_sorted[:20]

        elif provider_id == "openai":
            if not api_key:
                return None, []
            url = "https://api.openai.com/v1/models"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "CraftLauncher/1.0"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            chat_models = []
            for m in data.get("data", []):
                mid = m.get("id", "")
                if not re.match(r"^(gpt-[456]|o[134])", mid):
                    continue
                if any(skip in mid for skip in (
                    "realtime", "audio", "transcribe", "tts", "instruct", "search", "image", "preview"
                )):
                    continue
                chat_models.append((mid, int(m.get("created", 0))))
            if not chat_models:
                return None, []

            def openai_rank(item):
                mid, created = item
                is_main = not any(x in mid for x in ("mini", "nano", "chat-latest"))
                has_date = bool(re.search(r"-\d{4}-\d{2}-\d{2}$", mid))
                ver_m = re.search(r"gpt-(\d+)(?:\.(\d+))?", mid)
                maj = int(ver_m.group(1)) if ver_m else 4
                min_v = int(ver_m.group(2)) if (ver_m and ver_m.group(2)) else 0
                return (is_main, not has_date, maj, min_v, created)

            sorted_items = sorted(chat_models, key=openai_rank, reverse=True)
            model_names = []
            for mid, _ in sorted_items:
                if mid not in model_names:
                    model_names.append(mid)
            return model_names[0], model_names[:20]

        elif provider_id == "anthropic":
            if not api_key:
                return None, []
            url = "https://api.anthropic.com/v1/models"
            req = urllib.request.Request(url, headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "User-Agent": "CraftLauncher/1.0"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            # Anthropic liefert die neuesten Modelle zuerst zurück
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            if not models:
                return None, []
            # Bevorzuge Sonnet/Opus als Standard-Flaggschiff vor Haiku
            flagships = [m for m in models if "sonnet" in m or "opus" in m]
            latest = flagships[0] if flagships else models[0]
            return latest, models[:20]

        elif provider_id == "xai":
            if not api_key:
                return None, []
            url = "https://api.x.ai/v1/models"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "CraftLauncher/1.0"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            models = [
                m.get("id") for m in data.get("data", [])
                if m.get("id", "").startswith("grok-") and "image" not in m.get("id", "") and "vision" not in m.get("id", "")
            ]
            if not models:
                return None, []
            models_sorted = sorted(set(models), key=lambda x: ("mini" not in x, x), reverse=True)
            return models_sorted[0], models_sorted[:20]

        elif provider_id == "ollama":
            base_url = (pdata.get("url") or "http://localhost:11434").rstrip("/")
            url = f"{base_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "CraftLauncher/1.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.loads(r.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            if not models:
                return None, []
            return models[0], models

    except Exception:
        return None, []

    return None, []


def build_ai_env_vars(ai_cfg: dict) -> dict[str, str]:
    """
    Erzeugt die Umgebungsvariablen für alle KI-fähigen Tools (DeckCraft, SolidCraft, ArtCraft).
    """
    env_From_ai = {}
    providers = ai_cfg.get("providers", {})
    active = ai_cfg.get("active_provider", "google")
    env_From_ai["LLM"] = active

    g_key = providers.get("google", {}).get("api_key", "").strip()
    g_mod = providers.get("google", {}).get("model", "gemini-2.5-pro").strip()
    if g_key:
        env_From_ai["GOOGLE_API_KEY"] = g_key
        env_From_ai["GEMINI_API_KEY"] = g_key
    if g_mod:
        env_From_ai["GOOGLE_MODEL"] = g_mod
        env_From_ai["GEMINI_MODEL"] = g_mod

    o_key = providers.get("openai", {}).get("api_key", "").strip()
    o_mod = providers.get("openai", {}).get("model", "gpt-4.1").strip()
    if o_key:
        env_From_ai["OPENAI_API_KEY"] = o_key
        env_From_ai["CODEX_API_KEY"] = o_key
    if o_mod:
        env_From_ai["OPENAI_MODEL"] = o_mod

    a_key = providers.get("anthropic", {}).get("api_key", "").strip()
    a_mod = providers.get("anthropic", {}).get("model", "claude-sonnet-4-20250514").strip()
    if a_key:
        env_From_ai["ANTHROPIC_API_KEY"] = a_key
    if a_mod:
        env_From_ai["ANTHROPIC_MODEL"] = a_mod

    x_key = providers.get("xai", {}).get("api_key", "").strip()
    x_mod = providers.get("xai", {}).get("model", "grok-3").strip()
    if x_key:
        env_From_ai["XAI_API_KEY"] = x_key
    if x_mod:
        env_From_ai["XAI_MODEL"] = x_mod

    ol_url = providers.get("ollama", {}).get("url", "http://localhost:11434").strip()
    ol_mod = providers.get("ollama", {}).get("model", "llama3.3").strip()
    if ol_url:
        env_From_ai["OLLAMA_URL"] = ol_url
    if ol_mod:
        env_From_ai["OLLAMA_MODEL"] = ol_mod

    m_keys = ai_cfg.get("media_keys", {})
    if m_keys.get("pexels_api_key", "").strip():
        env_From_ai["PEXELS_API_KEY"] = m_keys["pexels_api_key"].strip()
    if m_keys.get("pixabay_api_key", "").strip():
        env_From_ai["PIXABAY_API_KEY"] = m_keys["pixabay_api_key"].strip()
    if m_keys.get("fal_api_key", "").strip():
        env_From_ai["FAL_KEY"] = m_keys["fal_api_key"].strip()

    return env_From_ai


def sync_ai_to_deckcraft(ai_cfg: dict, workspace_dir: Path):
    """
    Schreibt die zentralen KI-Keys und aktuellsten Modelle direkt in
    workspace/DeckCraft-master/app_data/userConfig.json, damit DeckCraft
    ohne manuelle Browser-Einrichtung sofort startklar ist.
    """
    deckcraft_dir = workspace_dir / "DeckCraft-master"
    if not deckcraft_dir.exists():
        return
    app_data = deckcraft_dir / "app_data"
    app_data.mkdir(parents=True, exist_ok=True)
    cfg_file = app_data / "userConfig.json"

    existing = {}
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    env_map = build_ai_env_vars(ai_cfg)
    # DeckCraft unterstützt als LLM: google, openai, anthropic, ollama, custom
    llm_choice = ai_cfg.get("active_provider", "google")
    if llm_choice == "xai":
        existing["LLM"] = "custom"
        existing["CUSTOM_LLM_URL"] = "https://api.x.ai/v1"
        existing["CUSTOM_LLM_API_KEY"] = env_map.get("XAI_API_KEY", "")
        existing["CUSTOM_MODEL"] = env_map.get("XAI_MODEL", "grok-3")
    else:
        existing["LLM"] = llm_choice

    for k in [
        "GOOGLE_API_KEY", "GOOGLE_MODEL",
        "OPENAI_API_KEY", "OPENAI_MODEL",
        "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL",
        "OLLAMA_URL", "OLLAMA_MODEL",
        "PEXELS_API_KEY", "PIXABAY_API_KEY"
    ]:
        if env_map.get(k):
            existing[k] = env_map[k]

    if env_map.get("PEXELS_API_KEY") and not existing.get("IMAGE_PROVIDER"):
        existing["IMAGE_PROVIDER"] = "pexels"
    elif env_map.get("PIXABAY_API_KEY") and not existing.get("IMAGE_PROVIDER"):
        existing["IMAGE_PROVIDER"] = "pixabay"

    try:
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Konnte DeckCraft userConfig.json nicht synchronisieren: {e}", file=sys.stderr)

    # Synchronisiere Fal.ai API-Key direkt nach ~/Artcraft/credentials/fal.api_key.txt für ArtCraft Native
    fal_key = (ai_cfg.get("media_keys", {}).get("fal_api_key") or "").strip()
    if fal_key:
        try:
            artcraft_creds_dir = Path.home() / "Artcraft" / "credentials"
            artcraft_creds_dir.mkdir(parents=True, exist_ok=True)
            fal_file = artcraft_creds_dir / "fal.api_key.txt"
            fal_file.write_text(fal_key, encoding="utf-8")
            os.chmod(fal_file, 0o600)
        except Exception as e:
            print(f"Konnte ArtCraft fal.api_key.txt nicht schreiben: {e}", file=sys.stderr)



def clean_rust_target_cache(extracted_path: Path, bin_path: Path) -> int:
    """
    Option 1 (Speicherplatz-Turbo):
    Löscht temporäre Compiler-Artefakte (deps, build, .fingerprint, incremental, .rlib, .d)
    im Ordner target/, behält aber die ausführbare Release-Binärdatei!
    Gibt die eingesparten Bytes zurück.
    """
    if not bin_path.exists():
        return 0

    target_dir = extracted_path / "target"
    if not target_dir.exists():
        return 0

    freed_bytes = 0

    def dir_size(p: Path) -> int:
        total = 0
        for root, _dirs, files in os.walk(p):
            for f in files:
                fp = Path(root) / f
                if not fp.is_symlink():
                    try:
                        total += fp.stat().st_size
                    except OSError:
                        pass
        return total

    # Lösche debug/ komplett, falls vorhanden
    debug_dir = target_dir / "debug"
    if debug_dir.exists():
        freed_bytes += dir_size(debug_dir)
        shutil.rmtree(debug_dir, ignore_errors=True)

    # Lösche schwere Unterordner in target/release/
    rel_dir = target_dir / "release"
    if rel_dir.exists():
        for sub in ["deps", "build", ".fingerprint", "incremental", "examples"]:
            sp = rel_dir / sub
            if sp.exists():
                freed_bytes += dir_size(sp)
                shutil.rmtree(sp, ignore_errors=True)
        for item in rel_dir.iterdir():
            if item.is_file() and item != bin_path and item.suffix in (".d", ".rlib"):
                try:
                    freed_bytes += item.stat().st_size
                    item.unlink()
                except OSError:
                    pass

    return freed_bytes


def get_directory_size_gb(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        out = subprocess.check_output(["du", "-sb", str(path)], stderr=subprocess.DEVNULL).decode()
        b = int(out.split()[0])
        return b / (1024 ** 3)
    except Exception:
        return 0.0


class ToolCard(Gtk.Box):
    def __init__(self, tool_data, app_window, compact=False):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL if compact else Gtk.Orientation.HORIZONTAL,
            spacing=8 if compact else 14
        )
        self.tool = tool_data
        self.app = app_window
        self.compact = compact
        self.get_style_context().add_class("tool-card-grid" if compact else "tool-card")

        self.workspace_dir = BASE_DIR / self.app.config.get("workspace_dir", "workspace")
        self.extracted_path = self.workspace_dir / self.tool.get("extracted_dir", self.tool.get("id"))

        # Icon Widget (Original-Logo bevorzugt, Emoji als Fallback)
        icon_size = 42 if compact else 48
        icon_widget = None
        rel_icon = self.tool.get("icon_path") or f"icons/{self.tool.get('id', '')}.png"
        icon_file = BASE_DIR / rel_icon
        if icon_file.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_file), icon_size, icon_size, True)
                icon_widget = Gtk.Image.new_from_pixbuf(pixbuf)
            except Exception:
                pass
        if icon_widget is None:
            icon_label = Gtk.Label()
            icon_label.set_markup(f"<span font='24'>{self.tool.get('icon', '📦')}</span>")
            icon_widget = icon_label

        # Favorite Star Button (Option 4)
        self.star_btn = Gtk.Button()
        self.star_btn.get_style_context().add_class("btn-star")
        self.star_btn.set_tooltip_text("Als Favorit oben anheften / lösen")
        self.update_star_label()
        self.star_btn.connect("clicked", self.on_toggle_favorite)

        # Title, Subtitle, Badges
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{GLib.markup_escape_text(self.tool.get('name', 'Unbekannt'))}</b>")
        title_label.get_style_context().add_class("tool-title")
        title_label.set_xalign(0)

        self.status_label = Gtk.Label()

        # AI Badge (falls Tool KI-Anbindung unterstützt)
        self.ai_badge = None
        if self.tool.get("ai_capable"):
            self.ai_badge = Gtk.Label(label="🤖 KI")
            self.ai_badge.get_style_context().add_class("badge-ai")
            ai_tip = self.tool.get("ai_info") or "Nutzt die zentrale KI-Anbindung des Launchers"
            self.ai_badge.set_tooltip_text(ai_tip)

        # Live Running Badge (Option 6)
        self.running_badge = Gtk.Label(label="🟢 Aktiv")
        self.running_badge.get_style_context().add_class("badge-status-running")
        self.running_badge.set_no_show_all(True)

        # Update Badge
        self.update_badge = Gtk.Label()
        self.update_badge.get_style_context().add_class("badge-update")
        self.update_badge.set_no_show_all(True)

        # Buttons
        self.update_btn = Gtk.Button(label="⬆️")
        self.update_btn.get_style_context().add_class("btn-update")
        self.update_btn.set_tooltip_text("Update von GitHub laden & bauen")
        self.update_btn.set_no_show_all(True)
        self.update_btn.connect("clicked", lambda b: self.perform_update(launch_after=False))

        # Stop Button (Option 6 - hidden unless running)
        self.stop_btn = Gtk.Button(label="⏹️ Stopp")
        self.stop_btn.get_style_context().add_class("btn-stop")
        self.stop_btn.set_tooltip_text("Laufenden Prozess beenden")
        self.stop_btn.set_no_show_all(True)
        self.stop_btn.connect("clicked", self.on_stop_clicked)

        self.start_btn = Gtk.Button(label="🚀 Starten")
        self.start_btn.get_style_context().add_class("btn-primary")
        self.start_btn.connect("clicked", self.on_start_clicked)

        self.term_btn = Gtk.Button(label="📟" if compact else "📟 Terminal")
        self.term_btn.get_style_context().add_class("btn-secondary")
        self.term_btn.set_tooltip_text("Im Terminal starten")
        self.term_btn.connect("clicked", lambda b: self.on_start_clicked(b, in_terminal=True))

        more_btn = self._build_more_menu_button()

        if compact:
            # --- KOMPAKTE KACHEL-ANSICHT (Grid Mode) ---
            self.set_size_request(280, -1)
            top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            top_row.pack_start(icon_widget, False, False, 0)

            title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            title_line.pack_start(title_label, False, False, 0)
            title_line.pack_end(self.star_btn, False, False, 0)
            title_col.pack_start(title_line, False, False, 0)

            if self.tool.get("subtitle"):
                sub_label = Gtk.Label(label=self.tool.get("subtitle"))
                sub_label.get_style_context().add_class("tool-subtitle")
                sub_label.set_xalign(0)
                sub_label.set_ellipsize(Pango.EllipsizeMode.END)
                title_col.pack_start(sub_label, False, False, 0)

            top_row.pack_start(title_col, True, True, 0)
            self.pack_start(top_row, False, False, 0)

            badge_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            badge_row.pack_start(self.status_label, False, False, 0)
            if self.ai_badge:
                badge_row.pack_start(self.ai_badge, False, False, 0)
            badge_row.pack_start(self.running_badge, False, False, 0)
            badge_row.pack_start(self.update_badge, False, False, 0)
            self.pack_start(badge_row, False, False, 0)

            act_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            act_row.pack_start(self.start_btn, True, True, 0)
            act_row.pack_start(self.stop_btn, False, False, 0)
            act_row.pack_start(self.update_btn, False, False, 0)
            act_row.pack_start(self.term_btn, False, False, 0)
            act_row.pack_start(more_btn, False, False, 0)
            self.pack_start(act_row, False, False, 0)
        else:
            # --- DETAIL-LISTEN-ANSICHT ---
            icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            icon_box.set_valign(Gtk.Align.CENTER)
            icon_box.get_style_context().add_class("icon-badge")
            icon_box.pack_start(icon_widget, True, True, 0)
            self.pack_start(icon_box, False, False, 2)

            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            content_box.set_hexpand(True)
            content_box.set_valign(Gtk.Align.CENTER)

            header_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            header_line.pack_start(self.star_btn, False, False, 0)
            header_line.pack_start(title_label, False, False, 0)

            if self.tool.get("subtitle"):
                sub_label = Gtk.Label(label=self.tool.get("subtitle"))
                sub_label.get_style_context().add_class("tool-subtitle")
                header_line.pack_start(sub_label, False, False, 0)

            header_line.pack_start(self.status_label, False, False, 0)
            if self.ai_badge:
                header_line.pack_start(self.ai_badge, False, False, 0)
            header_line.pack_start(self.running_badge, False, False, 0)
            header_line.pack_start(self.update_badge, False, False, 0)
            content_box.pack_start(header_line, False, False, 0)

            desc_label = Gtk.Label(label=self.tool.get("description", ""))
            desc_label.get_style_context().add_class("tool-desc")
            desc_label.set_line_wrap(True)
            desc_label.set_xalign(0)
            content_box.pack_start(desc_label, False, False, 0)
            self.pack_start(content_box, True, True, 0)

            actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            actions_box.set_valign(Gtk.Align.CENTER)
            actions_box.pack_start(self.update_btn, False, False, 0)
            actions_box.pack_start(self.stop_btn, False, False, 0)
            actions_box.pack_start(self.start_btn, False, False, 0)
            actions_box.pack_start(self.term_btn, False, False, 0)
            actions_box.pack_start(more_btn, False, False, 0)
            self.pack_start(actions_box, False, False, 0)

        self.update_status_badge()
        self.update_running_state()

        if self.tool.get("update_available"):
            self.show_update_indicator(self.tool.get("remote_sha", ""))

    def _build_more_menu_button(self):
        more_btn = Gtk.MenuButton()
        more_btn.set_label("⋮")
        more_btn.get_style_context().add_class("btn-secondary")
        more_btn.set_tooltip_text("Weitere Aktionen")

        menu = Gtk.Menu()

        m_code = Gtk.MenuItem(label="💻 In VS Code öffnen")
        m_code.connect("activate", self.on_open_code)
        menu.append(m_code)

        m_folder = Gtk.MenuItem(label="📁 Im Dateimanager öffnen")
        m_folder.connect("activate", self.on_open_folder)
        menu.append(m_folder)

        menu.append(Gtk.SeparatorMenuItem())

        if self.tool.get("repo"):
            m_check_upd = Gtk.MenuItem(label="🌐 Auf GitHub-Update prüfen")
            m_check_upd.connect("activate", lambda w: self.check_for_update(silent=False))
            menu.append(m_check_upd)

            m_force_upd = Gtk.MenuItem(label="⬇️ Von GitHub neu herunterladen & kompilieren")
            m_force_upd.connect("activate", lambda w: self.perform_update(launch_after=False))
            menu.append(m_force_upd)

        if self.tool.get("type") == "rust":
            m_clean = Gtk.MenuItem(label="🧹 Build-Cache dieses Tools bereinigen")
            m_clean.connect("activate", self.on_clean_single_cache)
            menu.append(m_clean)

        m_reextract = Gtk.MenuItem(label="🔄 Neu entpacken & bauen")
        m_reextract.connect("activate", self.on_reextract)
        menu.append(m_reextract)

        m_edit = Gtk.MenuItem(label="⚙️ Startbefehl anpassen")
        m_edit.connect("activate", self.on_edit_command)
        menu.append(m_edit)

        menu.show_all()
        more_btn.set_popup(menu)
        return more_btn

    def update_star_label(self):
        is_fav = bool(self.tool.get("favorite"))
        self.star_btn.set_label("⭐" if is_fav else "☆")

    def on_toggle_favorite(self, _widget):
        self.tool["favorite"] = not bool(self.tool.get("favorite"))
        save_config(self.app.config)
        self.app.refresh_list()

    def on_clean_single_cache(self, _widget):
        freed = clean_rust_target_cache(self.extracted_path, self.get_binary_path())
        mb = freed / (1024 * 1024)
        self.app.update_disk_usage_label()
        self.app.show_info_toast(f"{self.tool.get('name')}: {mb:.1f} MB Compiler-Cache freigegeben.")

    def is_extracted(self):
        return self.extracted_path.exists() and self.extracted_path.is_dir()

    def get_binary_path(self):
        pkg = self.tool.get("package_name") or self.tool.get("id", "")
        bin_name = pkg.replace("_", "-")
        return self.extracted_path / "target" / "release" / bin_name

    def is_built(self):
        if not self.is_extracted():
            return False
        ttype = self.tool.get("type", "custom")
        if ttype == "rust":
            bp = self.get_binary_path()
            return bp.exists() and os.access(bp, os.X_OK)
        elif ttype == "node/python":
            return (
                (self.extracted_path / "packages" / "web" / "node_modules").exists()
                and (self.extracted_path / "packages" / "api" / ".venv").exists()
            )
        return True

    def is_running(self) -> bool:
        tid = self.tool.get("id", "")
        proc = self.app.running_procs.get(tid)
        if proc is not None and proc.poll() is None:
            return True

        ttype = self.tool.get("type", "custom")
        if ttype == "rust":
            bin_name = (self.tool.get("package_name") or tid).replace("_", "-")
            if bin_name:
                res = subprocess.run(["pgrep", "-x", bin_name[:15]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
        elif ttype == "node/python" and tid == "deckcraft":
            res = subprocess.run(["fuser", "8000/tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
        return False

    def update_running_state(self):
        running = self.is_running()
        ctx = self.get_style_context()
        if running:
            ctx.add_class("tool-card-running")
            self.running_badge.show()
            self.stop_btn.show()
        else:
            ctx.remove_class("tool-card-running")
            self.running_badge.hide()
            self.stop_btn.hide()

    def on_stop_clicked(self, _widget):
        tid = self.tool.get("id", "")
        ttype = self.tool.get("type", "custom")

        proc = self.app.running_procs.pop(tid, None)
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

        if ttype == "rust":
            bin_name = (self.tool.get("package_name") or tid).replace("_", "-")
            subprocess.run(["pkill", "-x", bin_name[:15]], stderr=subprocess.DEVNULL)
        elif ttype == "node/python" and tid == "deckcraft":
            subprocess.run(["fuser", "-k", "8000/tcp"], stderr=subprocess.DEVNULL)
            subprocess.run(["fuser", "-k", "3000/tcp"], stderr=subprocess.DEVNULL)

        GLib.timeout_add(300, lambda: self.update_running_state() or False)

    def update_status_badge(self):
        ctx = self.status_label.get_style_context()
        ctx.remove_class("badge-status-ready")
        ctx.remove_class("badge-status-zipped")

        zip_file = BASE_DIR / self.tool.get("zip_name", "")
        if self.is_built():
            self.status_label.set_text("✅ Startbereit")
            ctx.add_class("badge-status-ready")
            if hasattr(self, "start_btn"):
                self.start_btn.set_label("🚀 Starten")
        elif self.is_extracted():
            self.status_label.set_text("⚙️ Noch nicht gebaut")
            ctx.add_class("badge-status-zipped")
            if hasattr(self, "start_btn"):
                self.start_btn.set_label("⚙️ Bauen & Starten")
        elif zip_file.exists():
            self.status_label.set_text("📦 Archiv lokal")
            ctx.add_class("badge-status-zipped")
            if hasattr(self, "start_btn"):
                self.start_btn.set_label("📦 Einrichten & Starten")
        else:
            self.status_label.set_text("☁️ Auto-Download")
            ctx.add_class("badge-status-zipped")
            if hasattr(self, "start_btn"):
                self.start_btn.set_label("⬇️ Installieren & Starten")

    def show_update_indicator(self, remote_sha=""):
        txt = f"⬆️ Update ({remote_sha})" if remote_sha else "⬆️ Update"
        self.update_badge.set_text(txt)
        self.update_badge.show()
        self.update_btn.show()

    def check_for_update(self, silent=False, on_done=None):
        repo = self.tool.get("repo")
        branch = self.tool.get("branch", "main")
        if not repo:
            if on_done:
                GLib.idle_add(lambda: on_done(False))
            return

        def worker():
            url = f"https://api.github.com/repos/{repo}/commits/{branch}"
            req = urllib.request.Request(url, headers={"User-Agent": "CraftLauncher/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    remote_sha = data.get("sha", "")[:7]
                    versions = load_versions()
                    tid = self.tool.get("id")
                    local_sha = versions.get(tid)

                    if not local_sha:
                        versions[tid] = remote_sha
                        save_versions(versions)
                        if not silent:
                            GLib.idle_add(lambda: self.app.show_info_toast(
                                f"{self.tool.get('name')} ist aktuell (Commit {remote_sha})."
                            ))
                        if on_done:
                            GLib.idle_add(lambda: on_done(False))
                    elif local_sha != remote_sha:
                        self.tool["update_available"] = True
                        self.tool["remote_sha"] = remote_sha
                        GLib.idle_add(lambda: self.show_update_indicator(remote_sha))
                        if on_done:
                            GLib.idle_add(lambda: on_done(True))
                    else:
                        if not silent:
                            GLib.idle_add(lambda: self.app.show_info_toast(
                                f"{self.tool.get('name')} ist bereits auf dem neuesten Stand ({remote_sha})."
                            ))
                        if on_done:
                            GLib.idle_add(lambda: on_done(False))
            except Exception as e:
                print(f"Update-Prüfung fehlgeschlagen für {repo}: {e}", file=sys.stderr)
                if not silent:
                    GLib.idle_add(lambda: self.app.show_error(f"Update-Prüfung fehlgeschlagen:\n{e}"))
                if on_done:
                    GLib.idle_add(lambda: on_done(False))

        threading.Thread(target=worker, daemon=True).start()

    def _compile_or_setup_sync(self):
        ttype = self.tool.get("type", "custom")
        pkg = self.tool.get("package_name") or self.tool.get("id", "")
        log_dir = self.workspace_dir / ".build_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{pkg}.log"

        if ttype == "rust" and pkg:
            if not shutil.which("cargo"):
                GLib.idle_add(lambda: self.start_btn.set_label("⏳ Installiere Rust..."))
                subprocess.run(
                    ["bash", "-c", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"],
                    check=True
                )
                cargo_bin = str(Path.home() / ".cargo" / "bin")
                if cargo_bin not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = f"{cargo_bin}:{os.environ.get('PATH', '')}"

            GLib.idle_add(lambda: self.start_btn.set_label("⚙️ Kompiliere..."))
            with open(log_file, "w", encoding="utf-8") as lf:
                res = subprocess.run(
                    ["cargo", "build", "--release", "-p", pkg],
                    cwd=str(self.extracted_path),
                    stdout=lf,
                    stderr=subprocess.STDOUT,
                    check=False
                )
            if res.returncode != 0:
                raise RuntimeError(
                    f"Kompilierung von '{pkg}' fehlgeschlagen (Exit-Code {res.returncode}).\n"
                    f"Details im Log: {log_file}\n\n"
                    f"Tipp: Prüfe mit './setup.sh', ob alle System-Pakete installiert sind."
                )
            # Option 1: Nach erfolgreichem Build direkt den mehrere GB großen Zwischen-Cache leeren!
            clean_rust_target_cache(self.extracted_path, self.get_binary_path())

        elif ttype == "node/python":
            GLib.idle_add(lambda: self.start_btn.set_label("⚙️ Richte Backend ein..."))
            api_dir = self.extracted_path / "packages" / "api"
            web_dir = self.extracted_path / "packages" / "web"
            with open(log_file, "w", encoding="utf-8") as lf:
                if api_dir.exists() and shutil.which("uv"):
                    subprocess.run(["uv", "sync"], cwd=str(api_dir), stdout=lf, stderr=subprocess.STDOUT, check=False)
                GLib.idle_add(lambda: self.start_btn.set_label("⚙️ Richte Web ein..."))
                if web_dir.exists() and shutil.which("npm"):
                    subprocess.run(["npm", "install"], cwd=str(web_dir), stdout=lf, stderr=subprocess.STDOUT, check=False)

    def perform_update(self, launch_after=False, in_terminal=False, on_done=None, force_download=True):
        repo = self.tool.get("repo")
        branch = self.tool.get("branch", "main")
        zip_name = self.tool.get("zip_name", f"{self.tool.get('id')}-{branch}.zip")

        self.start_btn.set_sensitive(False)
        self.term_btn.set_sensitive(False)
        self.update_btn.set_sensitive(False)

        def pipeline_worker():
            zip_path = BASE_DIR / zip_name
            tmp_zip = BASE_DIR / f".tmp_{zip_name}"
            try:
                need_download = force_download or (not self.is_extracted() and not zip_path.exists())
                if need_download:
                    if not repo:
                        raise RuntimeError("Kein GitHub-Repository für dieses Tool hinterlegt.")
                    zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
                    GLib.idle_add(lambda: self.start_btn.set_label("⬇️ Lade von GitHub..."))
                    req = urllib.request.Request(zip_url, headers={"User-Agent": "CraftLauncher/1.0"})
                    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp_zip, "wb") as out_f:
                        downloaded = 0
                        while True:
                            chunk = resp.read(256 * 1024)
                            if not chunk:
                                break
                            out_f.write(chunk)
                            downloaded += len(chunk)
                            mb = downloaded / (1024 * 1024)
                            GLib.idle_add(lambda m=mb: self.start_btn.set_label(f"⬇️ Lade ({m:.1f} MB)..."))
                    tmp_zip.replace(zip_path)

                if force_download or not self.is_extracted():
                    GLib.idle_add(lambda: self.start_btn.set_label("📦 Entpacke..."))
                    self.workspace_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(self.workspace_dir)

                remote_sha = self.tool.get("remote_sha")
                if remote_sha:
                    versions = load_versions()
                    versions[self.tool.get("id")] = remote_sha
                    save_versions(versions)

                if force_download or not self.is_built():
                    self._compile_or_setup_sync()

                GLib.idle_add(self.on_pipeline_complete, True, None, launch_after, in_terminal, on_done)
            except Exception as e:
                if tmp_zip.exists():
                    try:
                        tmp_zip.unlink()
                    except Exception:
                        pass
                GLib.idle_add(self.on_pipeline_complete, False, str(e), False, in_terminal, on_done)

        threading.Thread(target=pipeline_worker, daemon=True).start()

    def on_pipeline_complete(self, success, error_msg=None, launch_after=False, in_terminal=False, on_done=None):
        self.start_btn.set_sensitive(True)
        self.term_btn.set_sensitive(True)
        self.update_btn.set_sensitive(True)
        self.update_status_badge()
        self.app.update_disk_usage_label()

        if success:
            self.tool["update_available"] = False
            self.update_badge.hide()
            self.update_btn.hide()
            self.app.show_info_toast(f"{self.tool.get('name')} ist startbereit!")
            if launch_after:
                self.launch_tool(in_terminal=in_terminal)
        else:
            self.app.show_error(f"Einrichtung für {self.tool.get('name')} fehlgeschlagen:\n\n{error_msg}")

        if on_done:
            on_done(success)

    def ensure_extracted(self, callback_after):
        if self.is_extracted():
            callback_after(True)
            return
        self.perform_update(
            launch_after=False,
            force_download=not (BASE_DIR / self.tool.get("zip_name", "")).exists(),
            on_done=lambda ok: callback_after(ok)
        )

    def on_start_clicked(self, widget, in_terminal=False):
        if self.is_built():
            self.launch_tool(in_terminal=in_terminal)
        else:
            self.perform_update(
                launch_after=True,
                in_terminal=in_terminal,
                force_download=False
            )

    def launch_tool(self, in_terminal=False):
        command = self.tool.get("command", "")
        if not command:
            self.app.show_error(f"Kein Startbefehl für {self.tool.get('name')} konfiguriert.")
            return

        # Option 4: Merke letzten Startzeitpunkt für "Zuletzt verwendet"-Sortierung
        self.tool["last_used"] = int(time.time())
        save_config(self.app.config)

        working_dir = self.extracted_path
        if not working_dir.exists():
            working_dir = self.workspace_dir

        tool_id = self.tool.get("id", "")
        tool_name = self.tool.get("name", "Tool")
        tool_type = self.tool.get("type", "custom")

        # Zentrale KI-Konfiguration laden, an DeckCraft synchronisieren & als Env-Variablen übergeben
        ai_cfg = load_ai_config()
        sync_ai_to_deckcraft(ai_cfg, self.workspace_dir)
        ai_env_vars = build_ai_env_vars(ai_cfg)
        child_env = os.environ.copy()
        child_env.update(ai_env_vars)

        if not in_terminal and tool_type == "rust" and self.is_built():
            bin_path = self.get_binary_path()
            try:
                proc = subprocess.Popen([str(bin_path)], cwd=str(working_dir), env=child_env)
                self.app.running_procs[tool_id] = proc
                self.update_running_state()
                self.app.show_info_toast(f"'{tool_name}' gestartet.")
                return
            except Exception as e:
                print(f"Direktstart fehlgeschlagen, nutze Terminal-Fallback: {e}", file=sys.stderr)

        env_exports = "\n".join(
            f'export {k}="{v.replace(chr(34), chr(92) + chr(34))}"'
            for k, v in ai_env_vars.items()
        )

        runner_script = working_dir / ".run_tool.sh"
        script_content = f"""#!/usr/bin/env bash
echo "=========================================================="
echo "  🚀 Starte {tool_name}"
echo "  📂 Pfad: {working_dir}"
echo "  ⚡ Befehl: {command}"
echo "=========================================================="
echo ""

if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
fi
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
{env_exports}

cd "{working_dir}" || exit 1
{command}
exit_code=$?

echo ""
echo "=========================================================="
if [ $exit_code -eq 0 ]; then
    echo "  ✅ Prozess beendet (Code: 0)."
else
    echo "  ❌ Prozess beendet mit Fehlercode: $exit_code."
fi
echo "  Drücke Enter zum Schließen des Fensters."
echo "=========================================================="
read -r
"""
        try:
            with open(runner_script, "w", encoding="utf-8") as f:
                f.write(script_content)
            runner_script.chmod(0o700)
        except Exception as e:
            print(f"Fehler beim Erstellen des Runner-Skripts: {e}", file=sys.stderr)

        terminal_cmd = None
        if shutil.which("gnome-terminal"):
            terminal_cmd = ["gnome-terminal", f"--title={tool_name}", "--", "bash", str(runner_script)]
        elif shutil.which("xterm"):
            terminal_cmd = ["xterm", "-T", tool_name, "-e", f"bash '{runner_script}'"]

        try:
            if terminal_cmd:
                proc = subprocess.Popen(terminal_cmd, cwd=str(working_dir), env=child_env)
            else:
                proc = subprocess.Popen(["bash", str(runner_script)], cwd=str(working_dir), env=child_env)
            self.app.running_procs[tool_id] = proc
            GLib.timeout_add(500, lambda: self.update_running_state() or False)
        except Exception as e:
            self.app.show_error(f"Fehler beim Starten: {e}")

    def on_open_code(self, widget):
        self.ensure_extracted(lambda success: self._open_in_code() if success else None)

    def _open_in_code(self):
        if shutil.which("code"):
            subprocess.Popen(["code", str(self.extracted_path)])
        else:
            self.app.show_error("VS Code ('code') wurde auf diesem System nicht gefunden.")

    def on_open_folder(self, widget):
        self.ensure_extracted(lambda success: self._open_in_fm() if success else None)

    def _open_in_fm(self):
        target = self.extracted_path if self.extracted_path.exists() else self.workspace_dir
        subprocess.Popen(["xdg-open", str(target)])

    def on_reextract(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self.app,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Möchtest du '{self.tool.get('name')}' wirklich neu entpacken & bauen?"
        )
        dialog.format_secondary_text("Bereits vorhandene Dateien im Arbeitsordner werden überschrieben.")
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            if self.extracted_path.exists():
                try:
                    shutil.rmtree(self.extracted_path)
                except Exception as e:
                    self.app.show_error(f"Fehler beim Löschen des Ordners: {e}")
                    return
            self.update_status_badge()
            self.perform_update(
                launch_after=False,
                force_download=not (BASE_DIR / self.tool.get("zip_name", "")).exists()
            )

    def on_edit_command(self, widget):
        dialog = Gtk.Dialog(
            title=f"Startbefehl für {self.tool.get('name')} bearbeiten",
            transient_for=self.app,
            flags=0
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(14)

        lbl = Gtk.Label(label="Befehl zum Ausführen des Tools im Arbeitsordner:")
        lbl.set_xalign(0)
        box.pack_start(lbl, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(self.tool.get("command", ""))
        entry.set_width_chars(50)
        box.pack_start(entry, False, False, 0)

        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_cmd = entry.get_text().strip()
            self.tool["command"] = new_cmd
            save_config(self.app.config)
            self.app.show_info_toast("Startbefehl gespeichert.")
        dialog.destroy()


class CraftLauncherWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Craft Launcher - Tool Schnellauswahl")
        self.set_default_size(980, 720)
        self.set_position(Gtk.WindowPosition.CENTER)
        launcher_icon = BASE_DIR / "craft-launcher.svg"
        if launcher_icon.exists():
            try:
                self.set_icon_from_file(str(launcher_icon))
            except Exception:
                pass

        self.config = load_config()
        self.ai_config = load_ai_config()
        self.running_procs = {}
        self.active_cards = []
        self.view_mode = self.config.get("view_mode", "list")

        self.auto_discover_new_zips()

        self.active_category = "Alle"
        self.search_query = ""

        self.setup_css()
        self.build_ui()
        self.refresh_list()
        self.update_disk_usage_label()
        self.update_ai_header_button()

        # Prüfe beim Start automatisch im Hintergrund, ob noch Tools gebaut werden müssen
        GLib.timeout_add_seconds(1, self._auto_prepare_missing_on_startup)
        # Option 6: Alle 2 Sekunden laufende Prozesse aktualisieren
        GLib.timeout_add_seconds(2, self._poll_running_processes)
        # Zentrale KI: Beim Start (nach 3 Sek.) & danach regelmäßig alle 30 Min. auf neueste Modelle prüfen
        GLib.timeout_add_seconds(3, lambda: self.check_ai_models_background(silent=True) or False)
        GLib.timeout_add_seconds(1800, lambda: self.check_ai_models_background(silent=True) or True)

    def _auto_prepare_missing_on_startup(self):
        missing = [c for c in self.active_cards if not c.is_built()]
        if missing:
            self.on_prepare_all_tools(self.btn_prepare_all)
        return False

    def _poll_running_processes(self):
        for card in self.active_cards:
            card.update_running_state()
        return True

    def setup_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_DATA)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def auto_discover_new_zips(self):
        existing_zips = {t.get("zip_name") for t in self.config.get("tools", [])}
        all_zips = sorted([os.path.basename(p) for p in glob.glob(str(BASE_DIR / "*.zip"))])

        updated = False
        for z in all_zips:
            if z not in existing_zips:
                base_name = z.replace(".zip", "")
                clean_name = base_name.replace("-main", "").replace("-master", "")
                self.config["tools"].append({
                    "id": clean_name.lower(),
                    "zip_name": z,
                    "extracted_dir": base_name,
                    "name": clean_name.capitalize(),
                    "subtitle": "Importiertes Tool",
                    "description": f"Automatisch erkanntes Tool aus {z}",
                    "category": "Eigene Tools",
                    "tags": [clean_name.lower()],
                    "icon": "📦",
                    "color": "#89b4fa",
                    "type": "custom",
                    "command": "bash"
                })
                updated = True
        if updated:
            save_config(self.config)

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_box)

        # HeaderBar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "🎨 Craft Launcher"
        header.props.subtitle = "Schnellauswahl & Auto-Installer für Kreativ- & Office-Tools"
        self.set_titlebar(header)

        # Left Header Buttons: View Mode Toggle (Option 4), Add GitHub Tool (Option 5) & Central AI Settings
        self.btn_view_mode = Gtk.Button(
            label="⊞ Kacheln" if self.view_mode == "list" else "☰ Liste"
        )
        self.btn_view_mode.set_tooltip_text("Zwischen Listen-Ansicht und kompakter Kachel-Ansicht (Grid) wechseln")
        self.btn_view_mode.connect("clicked", self.on_toggle_view_mode)
        header.pack_start(self.btn_view_mode)

        btn_add_tool = Gtk.Button(label="➕ GitHub-Tool")
        btn_add_tool.set_tooltip_text("Neues Tool direkt per GitHub-Link hinzufügen & automatisch einrichten")
        btn_add_tool.connect("clicked", self.on_add_github_tool_dialog)
        header.pack_start(btn_add_tool)

        self.btn_ai_settings = Gtk.Button(label="🔑 KI & Modelle")
        self.btn_ai_settings.set_tooltip_text(
            "Zentrale KI-API-Verknüpfung & automatischer Modell-Updater für DeckCraft, SolidCraft & ArtCraft"
        )
        self.btn_ai_settings.connect("clicked", self.on_ai_settings_dialog)
        header.pack_start(self.btn_ai_settings)

        # Right Header Buttons
        btn_ws = Gtk.Button(label="📁")
        btn_ws.set_tooltip_text("Workspace-Ordner im Dateimanager öffnen")
        btn_ws.connect("clicked", lambda b: subprocess.Popen(["xdg-open", str(BASE_DIR / self.config.get("workspace_dir", "workspace"))]))
        header.pack_end(btn_ws)

        btn_refresh = Gtk.Button(label="🔄")
        btn_refresh.set_tooltip_text("Tools & Status neu laden")
        btn_refresh.connect("clicked", self.on_refresh_clicked)
        header.pack_end(btn_refresh)

        # Option 1: Clean Build Cache Button
        self.btn_clean_cache = Gtk.Button(label="🧹 Speicherplatz")
        self.btn_clean_cache.set_tooltip_text(
            "Speicherplatz-Turbo: Löscht unnötige Rust-Compiler-Zwischendateien (spart bis zu 28 GB!), alle Programme bleiben startbereit"
        )
        self.btn_clean_cache.connect("clicked", self.on_clean_all_caches)
        header.pack_end(self.btn_clean_cache)

        self.btn_check_updates = Gtk.Button(label="🌐 Updates")
        self.btn_check_updates.set_tooltip_text("Alle Tools auf neuere Versionen auf GitHub prüfen")
        self.btn_check_updates.connect("clicked", self.on_check_all_updates)
        header.pack_end(self.btn_check_updates)

        self.btn_prepare_all = Gtk.Button(label="⬇️ Alle bereitstellen")
        self.btn_prepare_all.set_tooltip_text(
            "Lädt, entpackt und kompiliert alle noch fehlenden Tools vollautomatisch im Hintergrund"
        )
        self.btn_prepare_all.connect("clicked", self.on_prepare_all_tools)
        header.pack_end(self.btn_prepare_all)

        # Search Bar
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_box.get_style_context().add_class("category-bar")

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("🔍 Suche nach Tool, Funktion oder Alternative (z. B. Photoshop, Lightroom, Figma, Excel, CAD)...")
        self.search_entry.set_hexpand(True)
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)
        main_box.pack_start(search_box, False, False, 0)

        # Category Filter Pills (inkl. ⭐ Favoriten)
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cat_box.get_style_context().add_class("category-bar")

        self.categories = [
            "Alle",
            "⭐ Favoriten",
            "Grafik & Bild",
            "Video & Audio",
            "Dokumente & Layout",
            "Office",
            "3D & CAD",
            "Präsentationen & KI"
        ]

        self.cat_buttons = []
        for cat in self.categories:
            btn = Gtk.ToggleButton(label=cat)
            btn.get_style_context().add_class("filter-btn")
            if cat == "Alle":
                btn.set_active(True)
            btn.connect("toggled", self.on_category_toggled, cat)
            cat_box.pack_start(btn, False, False, 0)
            self.cat_buttons.append(btn)

        main_box.pack_start(cat_box, False, False, 0)

        # System & Disk Info Banner
        self.banner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.banner_box.get_style_context().add_class("status-banner")

        has_cargo = check_command_available("cargo")
        has_node = check_command_available("node")
        has_python = check_command_available("python3")

        cargo_text = "Rust: <span color='#a6e3a1'>✅ Bereit</span>" if has_cargo else "Rust: <span color='#f9e2af'>⏳ Auto-Install</span>"
        python_text = "Python: <span color='#a6e3a1'>✅ Bereit</span>" if has_python else "Python: ⚠️"
        node_text = "Node.js: <span color='#a6e3a1'>✅ Bereit</span>" if has_node else "Node.js: ℹ️"

        info_lbl = Gtk.Label()
        info_lbl.set_use_markup(True)
        info_lbl.set_markup(
            f"<b>System:</b>  {cargo_text}  │  {python_text}  │  {node_text}  │  "
            f"<i>⭐ Favoriten stehen automatisch oben • Sortiert nach zuletzt genutzt</i>"
        )
        self.banner_box.pack_start(info_lbl, False, False, 0)

        self.disk_label = Gtk.Label()
        self.disk_label.set_use_markup(True)
        self.banner_box.pack_end(self.disk_label, False, False, 0)

        main_box.pack_start(self.banner_box, False, False, 0)

        # Scrolled Container
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_vexpand(True)

        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.cards_box.set_border_width(8)
        self.scrolled.add(self.cards_box)

        main_box.pack_start(self.scrolled, True, True, 0)

    def update_disk_usage_label(self):
        def worker():
            ws = BASE_DIR / self.config.get("workspace_dir", "workspace")
            gb = get_directory_size_gb(ws)
            color = "#a6e3a1" if gb < 5.0 else "#f9e2af"
            GLib.idle_add(
                lambda: self.disk_label.set_markup(f"💾 Workspace: <span color='{color}'><b>{gb:.1f} GB</b></span>")
            )
        threading.Thread(target=worker, daemon=True).start()

    # --- Option 1: Alle Compiler-Caches leeren ---
    def on_clean_all_caches(self, _widget):
        self.btn_clean_cache.set_sensitive(False)
        self.btn_clean_cache.set_label("🧹 Räume auf...")

        def worker():
            ws = BASE_DIR / self.config.get("workspace_dir", "workspace")
            total_freed = 0
            for t in self.config.get("tools", []):
                if t.get("type") == "rust":
                    ext = ws / t.get("extracted_dir", t.get("id", ""))
                    pkg = t.get("package_name") or t.get("id", "")
                    bp = ext / "target" / "release" / pkg.replace("_", "-")
                    total_freed += clean_rust_target_cache(ext, bp)
            gb = total_freed / (1024 ** 3)
            mb = total_freed / (1024 ** 2)

            def done():
                self.btn_clean_cache.set_sensitive(True)
                if gb >= 0.1:
                    self.btn_clean_cache.set_label(f"✅ {gb:.1f} GB frei!")
                else:
                    self.btn_clean_cache.set_label(f"✅ {mb:.0f} MB frei!")
                self.update_disk_usage_label()
                GLib.timeout_add_seconds(4, lambda: self.btn_clean_cache.set_label("🧹 Speicherplatz") or False)

            GLib.idle_add(done)

        threading.Thread(target=worker, daemon=True).start()

    # --- Option 4: Umschalter Liste <-> Kacheln (Grid) ---
    def on_toggle_view_mode(self, _widget):
        self.view_mode = "grid" if self.view_mode == "list" else "list"
        self.config["view_mode"] = self.view_mode
        save_config(self.config)
        self.btn_view_mode.set_label("⊞ Kacheln" if self.view_mode == "list" else "☰ Liste")
        self.refresh_list()

    # --- Option 5: Neues Tool per GitHub-Link hinzufügen ---
    def on_add_github_tool_dialog(self, _widget):
        dialog = Gtk.Dialog(
            title="➕ Neues Tool von GitHub hinzufügen",
            transient_for=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "🔍 Automatisch einrichten", Gtk.ResponseType.OK
        )
        dialog.set_default_size(520, -1)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(16)

        lbl_info = Gtk.Label()
        lbl_info.set_use_markup(True)
        lbl_info.set_markup(
            "<b>GitHub-Repository-Link oder <tt>owner/repo</tt> eingeben:</b>\n"
            "<span size='small' color='#a6adc8'>Der Launcher liest Name, Beschreibung, Branch, Cargo-Paket und App-Icon "
            "automatisch aus und kompiliert das Tool im Hintergrund.</span>"
        )
        lbl_info.set_line_wrap(True)
        lbl_info.set_xalign(0)
        box.pack_start(lbl_info, False, False, 0)

        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("z. B. https://github.com/storytold/lightcraft")
        box.pack_start(url_entry, False, False, 0)

        cat_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cat_lbl = Gtk.Label(label="Kategorie:")
        cat_combo = Gtk.ComboBoxText()
        for c in ["Grafik & Bild", "Video & Audio", "Dokumente & Layout", "Office", "3D & CAD", "Präsentationen & KI"]:
            cat_combo.append_text(c)
        cat_combo.set_active(0)
        cat_row.pack_start(cat_lbl, False, False, 0)
        cat_row.pack_start(cat_combo, True, True, 0)
        box.pack_start(cat_row, False, False, 0)

        sub_entry = Gtk.Entry()
        sub_entry.set_placeholder_text("Optional: Untertitel (z. B. Adobe Lightroom Alternative)")
        box.pack_start(sub_entry, False, False, 0)

        dialog.show_all()
        resp = dialog.run()
        raw_url = url_entry.get_text().strip()
        chosen_cat = cat_combo.get_active_text() or "Grafik & Bild"
        chosen_sub = sub_entry.get_text().strip()
        dialog.destroy()

        if resp != Gtk.ResponseType.OK or not raw_url:
            return

        # Parse owner/repo from URL
        m = re.search(r"github\.com/([^/]+/[^/#?]+)", raw_url)
        repo_slug = m.group(1) if m else raw_url.strip("/")
        repo_slug = re.sub(r"\.git$", "", repo_slug)
        if "/tree/" in repo_slug:
            repo_slug = repo_slug.split("/tree/")[0]

        if "/" not in repo_slug:
            self.show_error(f"Ungültige GitHub-Adresse: {raw_url}")
            return

        self.btn_prepare_all.set_label(f"⏳ Füge {repo_slug} hinzu...")

        def add_worker():
            try:
                api_url = f"https://api.github.com/repos/{repo_slug}"
                req = urllib.request.Request(api_url, headers={"User-Agent": "CraftLauncher/1.0"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    meta = json.loads(r.read().decode("utf-8"))

                branch = meta.get("default_branch", "main")
                repo_name = meta.get("name", repo_slug.split("/")[1])
                tid = repo_name.lower()
                desc = meta.get("description") or f"Open-Source Tool aus {repo_slug}"
                lang = (meta.get("language") or "").lower()
                ttype = "rust" if lang == "rust" else "custom"

                # Versuche offizielles App-Icon direkt von GitHub herunterzuladen
                ICONS_DIR.mkdir(parents=True, exist_ok=True)
                icon_dest = ICONS_DIR / f"{tid}.png"
                icon_candidates = [
                    f"https://raw.githubusercontent.com/{repo_slug}/{branch}/assets/app-icon/hicolor/256x256/apps/ai.storyteller.{tid}.png",
                    f"https://raw.githubusercontent.com/{repo_slug}/{branch}/assets/app-icon/{tid}-256.png",
                    f"https://raw.githubusercontent.com/{repo_slug}/{branch}/assets/app-icon/{tid}-1024.png",
                    f"https://raw.githubusercontent.com/{repo_slug}/{branch}/assets/icons/app/linux/exports/hicolor/256x256/apps/ai.storyteller.{tid}.png",
                ]
                for ic_url in icon_candidates:
                    try:
                        ic_req = urllib.request.Request(ic_url, headers={"User-Agent": "CraftLauncher/1.0"})
                        with urllib.request.urlopen(ic_req, timeout=6) as ic_resp, open(icon_dest, "wb") as ic_f:
                            shutil.copyfileobj(ic_resp, ic_f)
                        break
                    except Exception:
                        continue

                new_tool = {
                    "id": tid,
                    "zip_name": f"{repo_name}-{branch}.zip",
                    "extracted_dir": f"{repo_name}-{branch}",
                    "name": repo_name.capitalize() if repo_name.islower() else repo_name,
                    "subtitle": chosen_sub or f"{meta.get('language') or 'Open-Source'} App",
                    "description": desc,
                    "category": chosen_cat,
                    "tags": [tid, chosen_cat.lower()],
                    "icon": "🛠️",
                    "icon_path": f"icons/{tid}.png",
                    "color": "#89b4fa",
                    "type": ttype,
                    "command": f"if [ -x target/release/{tid} ]; then ./target/release/{tid} \"$@\"; else cargo run --release -p {tid} -- \"$@\"; fi" if ttype == "rust" else "bash",
                    "repo": repo_slug,
                    "branch": branch,
                    "package_name": tid
                }

                def finish_add():
                    # Ersetze falls ID schon existiert, sonst anhängen
                    tools = [t for t in self.config.get("tools", []) if t.get("id") != tid]
                    tools.append(new_tool)
                    self.config["tools"] = tools
                    save_config(self.config)
                    self.btn_prepare_all.set_label("⬇️ Alle bereitstellen")
                    self.refresh_list()
                    # Starte direkt Download & Build für das neue Tool
                    for c in self.active_cards:
                        if c.tool.get("id") == tid:
                            c.perform_update(launch_after=False, force_download=True)
                            break

                GLib.idle_add(finish_add)
            except Exception as e:
                GLib.idle_add(lambda: self.btn_prepare_all.set_label("⬇️ Alle bereitstellen"))
                GLib.idle_add(lambda: self.show_error(f"Konnte Repository '{repo_slug}' nicht abrufen:\n{e}"))

        threading.Thread(target=add_worker, daemon=True).start()

    def on_search_changed(self, entry):
        self.search_query = entry.get_text().strip().lower()
        self.refresh_list()

    def on_category_toggled(self, button, cat_name):
        if button.get_active():
            for b in self.cat_buttons:
                if b != button:
                    b.set_active(False)
            self.active_category = cat_name
            self.refresh_list()
        else:
            if not any(b.get_active() for b in self.cat_buttons):
                button.set_active(True)

    def on_refresh_clicked(self, widget):
        self.config = load_config()
        self.auto_discover_new_zips()
        self.refresh_list()
        self.update_disk_usage_label()
        self.show_info_toast("Liste aktualisiert.")

    def on_prepare_all_tools(self, widget):
        cards = [c for c in self.active_cards if not c.is_built()]
        if not cards:
            self.btn_prepare_all.set_label("✅ Alle startbereit!")
            GLib.timeout_add_seconds(3, lambda: self.btn_prepare_all.set_label("⬇️ Alle bereitstellen") or False)
            return

        self.btn_prepare_all.set_sensitive(False)
        total = len(cards)

        def process_next(idx):
            if idx >= total:
                self.btn_prepare_all.set_sensitive(True)
                self.btn_prepare_all.set_label("✅ Alle bereit!")
                self.update_disk_usage_label()
                GLib.timeout_add_seconds(4, lambda: self.btn_prepare_all.set_label("⬇️ Alle bereitstellen") or False)
                return
            card = cards[idx]
            self.btn_prepare_all.set_label(f"⚙️ Baue ({idx + 1}/{total}): {card.tool.get('name')}")
            card.perform_update(
                launch_after=False,
                force_download=False,
                on_done=lambda _ok: process_next(idx + 1)
            )

        process_next(0)

    def on_check_all_updates(self, widget):
        self.btn_check_updates.set_sensitive(False)
        self.btn_check_updates.set_label("⏳ Prüfe...")
        cards = list(self.active_cards)
        if not cards:
            self.btn_check_updates.set_sensitive(True)
            self.btn_check_updates.set_label("🌐 Updates")
            return

        remaining = [len(cards)]
        updates_found = [0]

        def card_done(has_upd):
            if has_upd:
                updates_found[0] += 1
            remaining[0] -= 1
            if remaining[0] <= 0:
                self.btn_check_updates.set_sensitive(True)
                if updates_found[0] > 0:
                    self.btn_check_updates.set_label(f"⬆️ {updates_found[0]} Update(s)")
                else:
                    self.btn_check_updates.set_label("✅ Aktuell")
                    GLib.timeout_add_seconds(3, lambda: self.btn_check_updates.set_label("🌐 Updates") or False)

        for card in cards:
            card.check_for_update(silent=True, on_done=card_done)

    def refresh_list(self):
        for child in self.cards_box.get_children():
            self.cards_box.remove(child)
        self.active_cards = []

        tools = list(self.config.get("tools", []))
        # Option 4: Sortiere Favoriten (⭐) nach oben, danach nach zuletzt verwendet (last_used)
        tools.sort(key=lambda t: (bool(t.get("favorite")), int(t.get("last_used", 0))), reverse=True)

        filtered = []
        for t in tools:
            cat = t.get("category", "")
            if self.active_category == "⭐ Favoriten":
                if not t.get("favorite"):
                    continue
            elif self.active_category != "Alle" and cat != self.active_category:
                continue

            if self.search_query:
                name = t.get("name", "").lower()
                subtitle = t.get("subtitle", "").lower()
                desc = t.get("description", "").lower()
                tags = [tag.lower() for tag in t.get("tags", [])]
                query = self.search_query
                if not (query in name or query in subtitle or query in desc or any(query in tag for tag in tags)):
                    continue

            filtered.append(t)

        if not filtered:
            empty_lbl = Gtk.Label(label="Keine Tools für diese Suche oder Kategorie gefunden.")
            empty_lbl.get_style_context().add_class("tool-desc")
            empty_lbl.set_margin_top(40)
            self.cards_box.pack_start(empty_lbl, True, True, 0)
            self.cards_box.show_all()
            return

        if self.view_mode == "grid":
            flow = Gtk.FlowBox()
            flow.set_valign(Gtk.Align.START)
            flow.set_max_children_per_line(3)
            flow.set_min_children_per_line(2)
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_row_spacing(6)
            flow.set_column_spacing(6)
            for t in filtered:
                card = ToolCard(t, self, compact=True)
                self.active_cards.append(card)
                flow.add(card)
            self.cards_box.pack_start(flow, False, False, 0)
        else:
            for t in filtered:
                card = ToolCard(t, self, compact=False)
                self.active_cards.append(card)
                self.cards_box.pack_start(card, False, False, 0)

        self.cards_box.show_all()

    # --- Zentrale KI-Konfiguration & Automatischer Modell-Updater ---
    def update_ai_header_button(self):
        self.ai_config = load_ai_config()
        active_id = self.ai_config.get("active_provider", "google")
        providers = self.ai_config.get("providers", {})
        active_p = providers.get(active_id, {})
        cur_mod = active_p.get("model", "")
        lat_mod = active_p.get("latest_model", "")

        has_newer = any(
            (p.get("api_key") or pid == "ollama")
            and p.get("latest_model")
            and p.get("model") != p.get("latest_model")
            for pid, p in providers.items()
        )
        has_any_key = any(bool(p.get("api_key")) for p in providers.values()) or active_id == "ollama"

        if has_newer and not self.ai_config.get("auto_update_models", True):
            self.btn_ai_settings.set_label("🔑 KI (⬆️ Neues Modell)")
        elif has_any_key and cur_mod:
            self.btn_ai_settings.set_label(f"🔑 KI: {cur_mod}")
        else:
            self.btn_ai_settings.set_label("🔑 KI & Modelle")

    def check_ai_models_background(self, silent=True, on_done=None):
        """
        Prüft für alle konfigurierten KI-Anbieter (mit hinterlegtem API-Key bzw. lokales Ollama)
        live gegen die offizielle Anbieter-API, welches das aktuellste Flaggschiff-Modell ist.
        Wenn 'auto_update_models' aktiv ist, wird automatisch auf das neueste Modell umgestellt.
        """
        def worker():
            cfg = load_ai_config()
            providers = cfg.get("providers", {})
            auto_upd = cfg.get("auto_update_models", True)
            upgraded = []
            available_upgrades = []

            for pid, pdata in providers.items():
                has_cred = bool((pdata.get("api_key") or "").strip()) if pid != "ollama" else True
                if not has_cred:
                    continue
                latest, all_models = fetch_provider_latest_models(pid, pdata)
                if latest:
                    pdata["latest_model"] = latest
                if all_models:
                    pdata["available_models"] = all_models

                cur = pdata.get("model", "")
                if latest and cur != latest:
                    if auto_upd:
                        pdata["model"] = latest
                        upgraded.append(f"{pdata.get('name', pid)} → {latest}")
                    else:
                        available_upgrades.append(f"{pdata.get('name', pid)}: {cur} → {latest}")

            cfg["last_checked"] = int(time.time())
            save_ai_config(cfg)
            ws = BASE_DIR / self.config.get("workspace_dir", "workspace")
            sync_ai_to_deckcraft(cfg, ws)

            def finish():
                self.ai_config = cfg
                self.update_ai_header_button()
                if upgraded:
                    msg = "KI-Modelle automatisch aktualisiert: " + ", ".join(upgraded)
                    self.show_info_toast(msg)
                if on_done:
                    on_done(upgraded, available_upgrades)

            GLib.idle_add(finish)

        threading.Thread(target=worker, daemon=True).start()

    def on_ai_settings_dialog(self, _widget):
        cfg = load_ai_config()
        dialog = Gtk.Dialog(
            title="🔑 Zentrale KI-Anbindung & Automatischer Modell-Updater",
            transient_for=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "💾 Speichern & Synchronisieren", Gtk.ResponseType.OK
        )
        dialog.set_default_size(680, 620)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(14)

        intro = Gtk.Label()
        intro.set_use_markup(True)
        intro.set_markup(
            "<b>Einmal zentral hinterlegen – in allen KI-fähigen Tools sofort nutzbar</b>\n"
            "<span size='small' color='#a6adc8'>"
            "• Übergibt API-Keys &amp; Modellnamen automatisch an <b>DeckCraft</b>, <b>SolidCraft</b> (AI-Chat) und <b>ArtCraft</b>.\n"
            "• Speichert Keys geschützt (Berechtigung <tt>0600</tt>) lokal in <tt>.ai_config.json</tt> (durch <tt>.gitignore</tt> vor GitHub geschützt)."
            "</span>"
        )
        intro.set_line_wrap(True)
        intro.set_xalign(0)
        box.pack_start(intro, False, False, 0)

        # Top Controls: Standard-Anbieter + Auto-Update-Checkbox + Live-Check-Button
        top_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        top_frame.get_style_context().add_class("tool-card")

        prov_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        prov_lbl = Gtk.Label()
        prov_lbl.set_markup("<b>Standard-KI-Anbieter (für DeckCraft &amp; Standard-Chat):</b>")
        prov_combo = Gtk.ComboBoxText()
        provider_order = ["google", "openai", "anthropic", "xai", "ollama"]
        for pid in provider_order:
            p_name = cfg["providers"][pid]["name"]
            prov_combo.append(pid, p_name)
        prov_combo.set_active_id(cfg.get("active_provider", "google"))
        prov_row.pack_start(prov_lbl, False, False, 0)
        prov_row.pack_start(prov_combo, True, True, 0)
        top_frame.pack_start(prov_row, False, False, 0)

        auto_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auto_chk = Gtk.CheckButton(
            label="⚡ Immer automatisch auf das aktuellste Flaggschiff-Modell aktualisieren (Prüfung beim Start & alle 30 Min.)"
        )
        auto_chk.set_active(cfg.get("auto_update_models", True))
        auto_row.pack_start(auto_chk, True, True, 0)

        btn_check_now = Gtk.Button(label="🔄 Jetzt aktuellste Modelle prüfen")
        btn_check_now.get_style_context().add_class("btn-update")
        auto_row.pack_end(btn_check_now, False, False, 0)
        top_frame.pack_start(auto_row, False, False, 0)

        status_check_lbl = Gtk.Label()
        status_check_lbl.set_use_markup(True)
        status_check_lbl.set_xalign(0)
        last_ts = cfg.get("last_checked", 0)
        if last_ts > 0:
            t_str = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(last_ts))
            status_check_lbl.set_markup(f"<span size='small' color='#a6adc8'>Zuletzt auf Modell-Updates geprüft: {t_str}</span>")
        else:
            status_check_lbl.set_markup("<span size='small' color='#a6adc8'>Trage unten einen API-Key ein und klicke auf „Jetzt aktuellste Modelle prüfen“.</span>")
        top_frame.pack_start(status_check_lbl, False, False, 0)

        box.pack_start(top_frame, False, False, 0)

        # Scrolled area for all providers
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        prov_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll.add(prov_list_box)
        box.pack_start(scroll, True, True, 0)

        widgets_map = {}

        for pid in provider_order:
            pdata = cfg["providers"][pid]
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.get_style_context().add_class("tool-card")

            hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            title = Gtk.Label()
            title.set_markup(f"<b>{GLib.markup_escape_text(pdata['name'])}</b>")
            title.set_xalign(0)
            hdr.pack_start(title, False, False, 0)

            badge_lbl = Gtk.Label()
            badge_lbl.set_use_markup(True)
            cur_m = pdata.get("model", "")
            lat_m = pdata.get("latest_model", cur_m)
            if cur_m == lat_m:
                badge_lbl.set_markup(f"<span size='small' color='#a6e3a1'>✅ Aktuellstes Modell ({GLib.markup_escape_text(cur_m)})</span>")
            else:
                badge_lbl.set_markup(f"<span size='small' color='#fab387'>⬆️ Neu verfügbar: <b>{GLib.markup_escape_text(lat_m)}</b></span>")
            hdr.pack_end(badge_lbl, False, False, 0)
            card.pack_start(hdr, False, False, 0)

            # Key / URL Row
            key_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            if pid == "ollama":
                k_lbl = Gtk.Label(label="Server-URL:")
                k_entry = Gtk.Entry()
                k_entry.set_text(pdata.get("url", "http://localhost:11434"))
                k_entry.set_placeholder_text("http://localhost:11434")
                key_row.pack_start(k_lbl, False, False, 0)
                key_row.pack_start(k_entry, True, True, 0)
            else:
                k_lbl = Gtk.Label(label="API-Key:")
                k_entry = Gtk.Entry()
                k_entry.set_visibility(False)
                k_entry.set_text(pdata.get("api_key", ""))
                k_entry.set_placeholder_text(f"API-Key für {pdata['name']} eingeben...")
                toggle_vis = Gtk.ToggleButton(label="👁️")
                toggle_vis.set_tooltip_text("API-Key ein-/ausblenden")
                toggle_vis.connect("toggled", lambda btn, ent=k_entry: ent.set_visibility(btn.get_active()))
                key_row.pack_start(k_lbl, False, False, 0)
                key_row.pack_start(k_entry, True, True, 0)
                key_row.pack_start(toggle_vis, False, False, 0)
            card.pack_start(key_row, False, False, 0)

            # Model ComboBoxEntry + "Use Latest" Button
            mod_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            m_lbl = Gtk.Label(label="Aktives Modell:")
            m_combo = Gtk.ComboBoxText.new_with_entry()
            avail = list(pdata.get("available_models", []))
            if cur_m and cur_m not in avail:
                avail.insert(0, cur_m)
            for m_item in avail:
                m_combo.append_text(m_item)
            m_combo.get_child().set_text(cur_m)

            btn_use_latest = Gtk.Button(label=f"⚡ Auf {lat_m} setzen")
            btn_use_latest.get_style_context().add_class("btn-secondary")
            btn_use_latest.set_tooltip_text("Übernimmt sofort das neueste erkannte Modell dieses Anbieters")

            def on_use_latest(_b, combo=m_combo, p=pdata, b_lbl=badge_lbl):
                target_m = p.get("latest_model", "")
                if target_m:
                    combo.get_child().set_text(target_m)
                    b_lbl.set_markup(f"<span size='small' color='#a6e3a1'>✅ Aktuellstes Modell ({GLib.markup_escape_text(target_m)})</span>")

            btn_use_latest.connect("clicked", on_use_latest)

            mod_row.pack_start(m_lbl, False, False, 0)
            mod_row.pack_start(m_combo, True, True, 0)
            mod_row.pack_start(btn_use_latest, False, False, 0)
            card.pack_start(mod_row, False, False, 0)

            prov_list_box.pack_start(card, False, False, 0)
            widgets_map[pid] = {
                "key_entry": k_entry,
                "model_combo": m_combo,
                "badge_lbl": badge_lbl,
                "btn_latest": btn_use_latest,
                "pdata": pdata
            }

        # Stock-Media Keys (Pexels / Pixabay / Fal.ai) für DeckCraft & ArtCraft
        media_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        media_card.get_style_context().add_class("tool-card")
        m_hdr = Gtk.Label()
        m_hdr.set_markup("<b>📸 Zusatz-APIs für Bilder &amp; Medien (Optional für DeckCraft &amp; ArtCraft)</b>")
        m_hdr.set_xalign(0)
        media_card.pack_start(m_hdr, False, False, 0)

        pexels_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pexels_row.pack_start(Gtk.Label(label="Pexels API-Key (DeckCraft Fotos):"), False, False, 0)
        pexels_entry = Gtk.Entry()
        pexels_entry.set_visibility(False)
        pexels_entry.set_text(cfg.get("media_keys", {}).get("pexels_api_key", ""))
        pexels_row.pack_start(pexels_entry, True, True, 0)
        media_card.pack_start(pexels_row, False, False, 0)

        fal_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        fal_row.pack_start(Gtk.Label(label="Fal.ai API-Key (ArtCraft Generierung):"), False, False, 0)
        fal_entry = Gtk.Entry()
        fal_entry.set_visibility(False)
        fal_entry.set_text(cfg.get("media_keys", {}).get("fal_api_key", ""))
        fal_row.pack_start(fal_entry, True, True, 0)
        media_card.pack_start(fal_row, False, False, 0)

        prov_list_box.pack_start(media_card, False, False, 0)

        # Live Check Handler inside Dialog
        def on_live_check_clicked(_btn):
            btn_check_now.set_sensitive(False)
            btn_check_now.set_label("⏳ Prüfe Anbieter-APIs...")
            status_check_lbl.set_markup("<span size='small' color='#f9e2af'>Frage live verfügbare Modelle bei den konfigurierten Anbietern ab...</span>")

            # Übernehme aktuelle Eingaben aus den Textfeldern vor der Abfrage
            for pid, w in widgets_map.items():
                val = w["key_entry"].get_text().strip()
                if pid == "ollama":
                    w["pdata"]["url"] = val or "http://localhost:11434"
                else:
                    w["pdata"]["api_key"] = val
                w["pdata"]["model"] = w["model_combo"].get_child().get_text().strip()

            def check_worker():
                found_count = 0
                upgraded_count = 0
                is_auto = auto_chk.get_active()
                for pid, w in widgets_map.items():
                    p = w["pdata"]
                    has_cred = bool(p.get("api_key")) if pid != "ollama" else True
                    if not has_cred:
                        continue
                    latest, all_mods = fetch_provider_latest_models(pid, p)
                    if latest:
                        found_count += 1
                        p["latest_model"] = latest
                        if all_mods:
                            p["available_models"] = all_mods
                        if is_auto and p.get("model") != latest:
                            p["model"] = latest
                            upgraded_count += 1

                def update_dialog_ui():
                    btn_check_now.set_sensitive(True)
                    btn_check_now.set_label("🔄 Jetzt aktuellste Modelle prüfen")
                    for pid, w in widgets_map.items():
                        p = w["pdata"]
                        cur_m = p.get("model", "")
                        lat_m = p.get("latest_model", cur_m)
                        combo = w["model_combo"]
                        combo.remove_all()
                        for m_item in p.get("available_models", []):
                            combo.append_text(m_item)
                        combo.get_child().set_text(cur_m)
                        w["btn_latest"].set_label(f"⚡ Auf {lat_m} setzen")
                        if cur_m == lat_m:
                            w["badge_lbl"].set_markup(
                                f"<span size='small' color='#a6e3a1'>✅ Aktuellstes Modell ({GLib.markup_escape_text(cur_m)})</span>"
                            )
                        else:
                            w["badge_lbl"].set_markup(
                                f"<span size='small' color='#fab387'>⬆️ Neu verfügbar: <b>{GLib.markup_escape_text(lat_m)}</b></span>"
                            )
                    now_str = time.strftime("%H:%M:%S")
                    if found_count == 0:
                        status_check_lbl.set_markup(
                            "<span size='small' color='#f9e2af'>⚠️ Keine erreichbaren APIs (bitte gültigen API-Key eintragen oder Ollama starten).</span>"
                        )
                    elif upgraded_count > 0:
                        status_check_lbl.set_markup(
                            f"<span size='small' color='#a6e3a1'>✅ Geprüft ({now_str}): {upgraded_count} Anbieter automatisch auf das neueste Modell aktualisiert!</span>"
                        )
                    else:
                        status_check_lbl.set_markup(
                            f"<span size='small' color='#a6e3a1'>✅ Geprüft ({now_str}): Alle {found_count} erreichbaren Anbieter sind auf dem neuesten Stand!</span>"
                        )

                GLib.idle_add(update_dialog_ui)

            threading.Thread(target=check_worker, daemon=True).start()

        btn_check_now.connect("clicked", on_live_check_clicked)

        dialog.show_all()
        resp = dialog.run()
        if resp == Gtk.ResponseType.OK:
            cfg["active_provider"] = prov_combo.get_active_id() or "google"
            cfg["auto_update_models"] = auto_chk.get_active()
            for pid, w in widgets_map.items():
                val = w["key_entry"].get_text().strip()
                if pid == "ollama":
                    cfg["providers"][pid]["url"] = val or "http://localhost:11434"
                else:
                    cfg["providers"][pid]["api_key"] = val
                cfg["providers"][pid]["model"] = w["model_combo"].get_child().get_text().strip()
            cfg["media_keys"]["pexels_api_key"] = pexels_entry.get_text().strip()
            cfg["media_keys"]["fal_api_key"] = fal_entry.get_text().strip()

            save_ai_config(cfg)
            ws = BASE_DIR / self.config.get("workspace_dir", "workspace")
            sync_ai_to_deckcraft(cfg, ws)
            self.update_ai_header_button()
            # Prüfe nach dem Speichern direkt im Hintergrund, ob mit neu eingegebenen Keys ein neueres Modell existiert
            self.check_ai_models_background(silent=False)

        dialog.destroy()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Fehler"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show_info_toast(self, message):
        print(f"[Craft Launcher] {message}")


def main():
    app = CraftLauncherWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

