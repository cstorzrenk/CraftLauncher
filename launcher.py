#!/usr/bin/env python3
"""
Craft Launcher - Schnellauswahl & Starter für Kreativ- und Office-Tools
"""

import os
import sys
import json
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
DEFAULT_WORKSPACE_DIR = BASE_DIR / "workspace"

# Cargo / Rust & Local bin Verzeichnisse zu PATH hinzufügen
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
    padding: 14px;
    margin: 6px 12px;
    transition: all 150ms ease;
}

.tool-card:hover {
    border-color: #89b4fa;
    background-color: #1e1e2e;
}

.icon-badge {
    border-radius: 12px;
    min-width: 52px;
    min-height: 52px;
    font-size: 26px;
}

.tool-title {
    font-size: 16px;
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
    margin-top: 4px;
}

.badge-status-ready {
    background-color: rgba(166, 227, 161, 0.15);
    color: #a6e3a1;
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

.btn-primary {
    background-color: #89b4fa;
    color: #11111b;
    border-radius: 8px;
    font-weight: bold;
    padding: 6px 16px;
    border: none;
}

.btn-primary:hover {
    background-color: #b4befe;
}

.btn-update {
    background-color: #fab387;
    color: #11111b;
    border-radius: 8px;
    font-weight: bold;
    padding: 6px 12px;
    border: none;
}

.btn-update:hover {
    background-color: #f9e2af;
}

.btn-secondary {
    background-color: #313244;
    color: #cdd6f4;
    border-radius: 8px;
    padding: 6px 10px;
    border: none;
}

.btn-secondary:hover {
    background-color: #45475a;
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
    return {"workspace_dir": "workspace", "tools": []}

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

class ToolCard(Gtk.Box):
    def __init__(self, tool_data, app_window):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.tool = tool_data
        self.app = app_window
        self.get_style_context().add_class("tool-card")

        self.workspace_dir = BASE_DIR / self.app.config.get("workspace_dir", "workspace")
        self.extracted_path = self.workspace_dir / self.tool.get("extracted_dir", self.tool.get("id"))

        # Icon / Badge Box (Original-Logo bevorzugt, Emoji als Fallback)
        icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        icon_box.set_valign(Gtk.Align.CENTER)
        icon_box.get_style_context().add_class("icon-badge")

        icon_widget = None
        rel_icon = self.tool.get("icon_path") or f"icons/{self.tool.get('id', '')}.png"
        icon_file = BASE_DIR / rel_icon
        if icon_file.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_file), 48, 48, True)
                icon_widget = Gtk.Image.new_from_pixbuf(pixbuf)
            except Exception as e:
                print(f"Konnte Icon {icon_file} nicht laden: {e}", file=sys.stderr)

        if icon_widget is None:
            icon_label = Gtk.Label(label=self.tool.get("icon", "📦"))
            icon_label.set_use_markup(True)
            icon_label.set_markup(f"<span font='28'>{self.tool.get('icon', '📦')}</span>")
            icon_widget = icon_label

        icon_box.pack_start(icon_widget, True, True, 0)
        self.pack_start(icon_box, False, False, 4)

        # Middle Content Box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_hexpand(True)
        content_box.set_valign(Gtk.Align.CENTER)

        # Header Line (Title, Subtitle, Status)
        header_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{GLib.markup_escape_text(self.tool.get('name', 'Unbekannt'))}</b>")
        title_label.get_style_context().add_class("tool-title")
        title_label.set_xalign(0)
        header_line.pack_start(title_label, False, False, 0)

        if self.tool.get("subtitle"):
            sub_label = Gtk.Label(label=self.tool.get("subtitle"))
            sub_label.get_style_context().add_class("tool-subtitle")
            header_line.pack_start(sub_label, False, False, 0)

        # Status badge
        self.status_label = Gtk.Label()
        self.update_status_badge()
        header_line.pack_start(self.status_label, False, False, 0)

        # Update badge (shown when update available)
        self.update_badge = Gtk.Label()
        self.update_badge.get_style_context().add_class("badge-update")
        self.update_badge.set_no_show_all(True)
        header_line.pack_start(self.update_badge, False, False, 0)

        content_box.pack_start(header_line, False, False, 0)

        # Description
        desc_label = Gtk.Label(label=self.tool.get("description", ""))
        desc_label.get_style_context().add_class("tool-desc")
        desc_label.set_line_wrap(True)
        desc_label.set_xalign(0)
        content_box.pack_start(desc_label, False, False, 0)

        self.pack_start(content_box, True, True, 0)

        # Actions Box
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        actions_box.set_valign(Gtk.Align.CENTER)

        # Update Button (hidden until update found)
        self.update_btn = Gtk.Button(label="⬆️ Update")
        self.update_btn.get_style_context().add_class("btn-update")
        self.update_btn.set_tooltip_text("Neueste ZIP-Version von GitHub herunterladen & aktualisieren")
        self.update_btn.set_no_show_all(True)
        self.update_btn.connect("clicked", lambda b: self.perform_update())
        actions_box.pack_start(self.update_btn, False, False, 0)

        # Start Button
        self.start_btn = Gtk.Button(label="🚀 Starten")
        self.start_btn.get_style_context().add_class("btn-primary")
        self.start_btn.connect("clicked", self.on_start_clicked)
        actions_box.pack_start(self.start_btn, False, False, 0)

        # Terminal Button
        self.term_btn = Gtk.Button(label="📟 Terminal")
        self.term_btn.get_style_context().add_class("btn-secondary")
        self.term_btn.set_tooltip_text("Im Terminal starten (für Logs & Build-Ausgaben)")
        self.term_btn.connect("clicked", lambda b: self.on_start_clicked(b, in_terminal=True))
        actions_box.pack_start(self.term_btn, False, False, 0)

        # More Actions Menu
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

        m_sep1 = Gtk.SeparatorMenuItem()
        menu.append(m_sep1)

        if self.tool.get("repo"):
            m_check_upd = Gtk.MenuItem(label="🌐 Auf GitHub-Update prüfen")
            m_check_upd.connect("activate", lambda w: self.check_for_update(silent=False))
            menu.append(m_check_upd)

            m_force_upd = Gtk.MenuItem(label="⬇️ Neueste ZIP von GitHub laden & bauen")
            m_force_upd.connect("activate", lambda w: self.perform_update())
            menu.append(m_force_upd)

        m_reextract = Gtk.MenuItem(label="🔄 Neu entpacken (Lokale Zip überschreiben)")
        m_reextract.connect("activate", self.on_reextract)
        menu.append(m_reextract)

        m_edit = Gtk.MenuItem(label="⚙️ Startbefehl anpassen")
        m_edit.connect("activate", self.on_edit_command)
        menu.append(m_edit)

        menu.show_all()
        more_btn.set_popup(menu)
        actions_box.pack_start(more_btn, False, False, 0)

        self.pack_start(actions_box, False, False, 0)

        if self.tool.get("update_available"):
            self.show_update_indicator(self.tool.get("remote_sha", ""))

    def is_extracted(self):
        return self.extracted_path.exists() and self.extracted_path.is_dir()

    def update_status_badge(self):
        ctx = self.status_label.get_style_context()
        ctx.remove_class("badge-status-ready")
        ctx.remove_class("badge-status-zipped")

        zip_file = BASE_DIR / self.tool.get("zip_name", "")
        if self.is_extracted():
            self.status_label.set_text("📂 Entpackt")
            ctx.add_class("badge-status-ready")
        elif zip_file.exists():
            self.status_label.set_text("📦 Archiv")
            ctx.add_class("badge-status-zipped")
        else:
            self.status_label.set_text("☁️ GitHub")
            ctx.add_class("badge-status-zipped")

    def show_update_indicator(self, remote_sha=""):
        txt = f"⬆️ Update ({remote_sha})" if remote_sha else "⬆️ Update verfügbar"
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
                        # Initialen Stand merken
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

    def perform_update(self):
        repo = self.tool.get("repo")
        branch = self.tool.get("branch", "main")
        zip_name = self.tool.get("zip_name", f"{self.tool.get('id')}-{branch}.zip")
        if not repo:
            self.app.show_error("Kein GitHub-Repository für dieses Tool hinterlegt.")
            return

        self.start_btn.set_sensitive(False)
        self.update_btn.set_sensitive(False)
        self.start_btn.set_label("⬇️ Lade ZIP...")

        def update_worker():
            zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
            zip_path = BASE_DIR / zip_name
            tmp_zip = BASE_DIR / f".tmp_{zip_name}"
            try:
                req = urllib.request.Request(zip_url, headers={"User-Agent": "CraftLauncher/1.0"})
                with urllib.request.urlopen(req, timeout=60) as resp, open(tmp_zip, "wb") as out_f:
                    shutil.copyfileobj(resp, out_f)
                tmp_zip.replace(zip_path)

                GLib.idle_add(lambda: self.start_btn.set_label("📦 Entpacke..."))
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(self.workspace_dir)

                # Speichere neue Commit-SHA falls bekannt
                remote_sha = self.tool.get("remote_sha")
                if remote_sha:
                    versions = load_versions()
                    versions[self.tool.get("id")] = remote_sha
                    save_versions(versions)

                # Kompiliere im Hintergrund falls Rust
                pkg = self.tool.get("package_name")
                if self.tool.get("type") == "rust" and pkg and shutil.which("cargo"):
                    GLib.idle_add(lambda: self.start_btn.set_label("⚙️ Kompiliere..."))
                    subprocess.run(
                        ["cargo", "build", "--release", "-p", pkg],
                        cwd=str(self.extracted_path),
                        check=False
                    )

                GLib.idle_add(self.on_update_complete, True, None)
            except Exception as e:
                if tmp_zip.exists():
                    tmp_zip.unlink()
                GLib.idle_add(self.on_update_complete, False, str(e))

        threading.Thread(target=update_worker, daemon=True).start()

    def on_update_complete(self, success, error_msg=None):
        self.start_btn.set_sensitive(True)
        self.update_btn.set_sensitive(True)
        self.start_btn.set_label("🚀 Starten")
        self.update_status_badge()
        if success:
            self.tool["update_available"] = False
            self.update_badge.hide()
            self.update_btn.hide()
            self.app.show_info_toast(f"{self.tool.get('name')} wurde erfolgreich aktualisiert!")
        else:
            self.app.show_error(f"Update für {self.tool.get('name')} fehlgeschlagen:\n{error_msg}")

    def ensure_extracted(self, callback_after):
        if self.is_extracted():
            callback_after(True)
            return

        zip_file = BASE_DIR / self.tool.get("zip_name", "")
        if not zip_file.exists():
            if self.tool.get("repo"):
                # Automatisch von GitHub herunterladen, falls ZIP lokal noch nicht liegt
                self.perform_update()
                callback_after(False)
                return
            self.app.show_error(f"Archivdatei nicht gefunden: {zip_file}")
            callback_after(False)
            return

        # Disable button & show spinner
        self.start_btn.set_sensitive(False)
        self.start_btn.set_label("⏳ Entpacke...")

        def extract_worker():
            try:
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    zf.extractall(self.workspace_dir)
                GLib.idle_add(lambda: self.on_extraction_complete(True, callback_after))
            except Exception as e:
                print(f"Fehler beim Entpacken: {e}", file=sys.stderr)
                GLib.idle_add(lambda: self.on_extraction_complete(False, callback_after, error=str(e)))

        threading.Thread(target=extract_worker, daemon=True).start()

    def on_extraction_complete(self, success, callback_after, error=None):
        self.start_btn.set_sensitive(True)
        self.start_btn.set_label("🚀 Starten")
        self.update_status_badge()
        if not success:
            self.app.show_error(f"Fehler beim Entpacken von {self.tool.get('name')}:\n{error}")
            callback_after(False)
        else:
            callback_after(True)

    def on_start_clicked(self, widget, in_terminal=False):
        self.ensure_extracted(lambda success: self.launch_tool(in_terminal) if success else None)

    def launch_tool(self, in_terminal=False):
        command = self.tool.get("command", "")
        if not command:
            self.app.show_error(f"Kein Startbefehl für {self.tool.get('name')} konfiguriert.")
            return

        working_dir = self.extracted_path
        if not working_dir.exists():
            working_dir = self.workspace_dir

        tool_name = self.tool.get("name", "Tool")
        tool_type = self.tool.get("type", "custom")

        # Create helper runner script that checks environment and runs command
        runner_script = working_dir / ".run_tool.sh"
        script_content = f"""#!/usr/bin/env bash
echo "=========================================================="
echo "  🚀 Starte {tool_name}"
echo "  📂 Pfad: {working_dir}"
echo "  ⚡ Befehl: {command}"
echo "=========================================================="
echo ""

# Environment vorbereiten
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
fi
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# Prüfe Abhängigkeiten
if [[ "{tool_type}" == "rust" ]]; then
    if ! command -v cargo &> /dev/null; then
        echo "⚠️  HINWEIS: Rust/Cargo ist noch nicht installiert!"
        echo "   {tool_name} benötigt Rust, um kompiliert und gestartet zu werden."
        echo ""
        echo "   Möchtest du Rust jetzt installieren? (curl https://sh.rustup.rs)"
        read -p "   Rust jetzt installieren? [j/N]: " answer
        if [[ "$answer" =~ ^[jJyY]$ ]]; then
            curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            if [ -f "$HOME/.cargo/env" ]; then
                source "$HOME/.cargo/env"
            fi
            export PATH="$HOME/.cargo/bin:$PATH"
        else
            echo "Abbruch. Bitte installiere Rust mit: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            exec bash
        fi
    fi
elif [[ "{tool_type}" == "node/python" ]]; then
    if ! command -v node &> /dev/null && ! command -v npm &> /dev/null; then
        echo "⚠️  HINWEIS: Node.js/npm ist noch nicht installiert!"
    fi
fi

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
            runner_script.chmod(0o755)
        except Exception as e:
            print(f"Fehler beim Erstellen des Runner-Skripts: {e}", file=sys.stderr)

        # Run in terminal or background
        terminal_cmd = None
        if shutil.which("gnome-terminal"):
            terminal_cmd = ["gnome-terminal", f"--title={tool_name}", "--", "bash", str(runner_script)]
        elif shutil.which("xterm"):
            terminal_cmd = ["xterm", "-T", tool_name, "-e", f"bash '{runner_script}'"]

        if terminal_cmd:
            try:
                subprocess.Popen(terminal_cmd, cwd=str(working_dir))
                self.app.show_info_toast(f"'{tool_name}' im Terminal gestartet.")
            except Exception as e:
                self.app.show_error(f"Fehler beim Starten des Terminals: {e}")
        else:
            # Fallback to direct subprocess
            try:
                subprocess.Popen(["bash", str(runner_script)], cwd=str(working_dir))
                self.app.show_info_toast(f"'{tool_name}' gestartet.")
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
            text=f"Möchtest du '{self.tool.get('name')}' wirklich neu entpacken?"
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
            self.ensure_extracted(lambda success: self.app.show_info_toast(f"'{self.tool.get('name')}' erfolgreich neu entpackt.") if success else None)

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
        self.set_default_size(900, 680)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.config = load_config()
        self.auto_discover_new_zips()

        self.active_category = "Alle"
        self.search_query = ""

        self.setup_css()
        self.build_ui()
        self.refresh_list()

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
                # Add discovered zip
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
        header.props.subtitle = "Schnellauswahl für Kreativ- & Office-Tools"
        self.set_titlebar(header)

        # Open Workspace button in header
        btn_ws = Gtk.Button(label="📁 Workspace")
        btn_ws.set_tooltip_text("Arbeitsordner öffnen")
        btn_ws.connect("clicked", lambda b: subprocess.Popen(["xdg-open", str(BASE_DIR / self.config.get("workspace_dir", "workspace"))]))
        header.pack_end(btn_ws)

        # Refresh button
        btn_refresh = Gtk.Button(label="🔄")
        btn_refresh.set_tooltip_text("Tools & Status neu laden")
        btn_refresh.connect("clicked", self.on_refresh_clicked)
        header.pack_end(btn_refresh)

        # Check all updates button
        self.btn_check_updates = Gtk.Button(label="🌐 Updates prüfen")
        self.btn_check_updates.set_tooltip_text("Alle Tools auf neuere Versionen auf GitHub prüfen")
        self.btn_check_updates.connect("clicked", self.on_check_all_updates)
        header.pack_end(self.btn_check_updates)

        # Search Bar
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_box.get_style_context().add_class("category-bar")

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("🔍 Suche nach Tool, Funktion oder Alternative (z. B. Photoshop, Excel, CAD, Video)...")
        self.search_entry.set_hexpand(True)
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)
        main_box.pack_start(search_box, False, False, 0)

        # Category Filter Pills
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cat_box.get_style_context().add_class("category-bar")

        self.categories = [
            "Alle",
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

        # System Info Banner
        self.banner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.banner_box.get_style_context().add_class("status-banner")
        
        has_cargo = check_command_available("cargo")
        has_node = check_command_available("node")
        has_python = check_command_available("python3")

        cargo_text = "Rust/Cargo: <span color='#a6e3a1'>✅ Bereit</span>" if has_cargo else "Rust/Cargo: <span color='#f38ba8'>⚠️ Nicht installiert</span>"
        python_text = "Python: <span color='#a6e3a1'>✅ 3.12</span>" if has_python else "Python: ⚠️ Nicht gefunden"
        node_text = "Node.js: <span color='#a6e3a1'>✅ Bereit</span>" if has_node else "Node.js: ℹ️ Optional"

        info_lbl = Gtk.Label()
        info_lbl.set_use_markup(True)
        info_lbl.set_markup(f"<b>System:</b>  {cargo_text}  │  {python_text}  │  {node_text}")
        self.banner_box.pack_start(info_lbl, False, False, 0)

        if not has_cargo:
            install_btn = Gtk.Button(label="ℹ️ Rust Schnellinstallation")
            install_btn.get_style_context().add_class("btn-secondary")
            install_btn.connect("clicked", self.show_rust_help)
            self.banner_box.pack_end(install_btn, False, False, 0)

        main_box.pack_start(self.banner_box, False, False, 0)

        # Scrolled List of Tools
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.cards_box.set_border_width(8)
        scrolled.add(self.cards_box)

        main_box.pack_start(scrolled, True, True, 0)

    def show_rust_help(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Rust & Cargo Installation"
        )
        dialog.format_secondary_text(
            "Die meisten Craft-Tools basieren auf modernem Rust.\n\n"
            "Um sie direkt ausführen zu können, kannst du Rust mit folgendem Befehl im Terminal installieren:\n\n"
            "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh\n\n"
            "Wenn du ein Tool startest, bietet der Launcher dir die Installation auch automatisch an."
        )
        dialog.run()
        dialog.destroy()

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
            # Prevent unchecking all
            if not any(b.get_active() for b in self.cat_buttons):
                button.set_active(True)

    def on_refresh_clicked(self, widget):
        self.config = load_config()
        self.auto_discover_new_zips()
        self.refresh_list()
        self.show_info_toast("Liste aktualisiert.")

    def on_check_all_updates(self, widget):
        self.btn_check_updates.set_sensitive(False)
        self.btn_check_updates.set_label("⏳ Prüfe...")
        cards = [c for c in self.cards_box.get_children() if isinstance(c, ToolCard)]
        if not cards:
            self.btn_check_updates.set_sensitive(True)
            self.btn_check_updates.set_label("🌐 Updates prüfen")
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
                    self.btn_check_updates.set_label("✅ Alle aktuell")
                    GLib.timeout_add_seconds(3, lambda: self.btn_check_updates.set_label("🌐 Updates prüfen") or False)

        for card in cards:
            card.check_for_update(silent=True, on_done=card_done)

    def refresh_list(self):
        # Clear existing cards
        for child in self.cards_box.get_children():
            self.cards_box.remove(child)

        tools = self.config.get("tools", [])
        visible_count = 0

        for t in tools:
            # Check category filter
            cat = t.get("category", "")
            if self.active_category != "Alle" and cat != self.active_category:
                continue

            # Check search query
            if self.search_query:
                name = t.get("name", "").lower()
                subtitle = t.get("subtitle", "").lower()
                desc = t.get("description", "").lower()
                tags = [tag.lower() for tag in t.get("tags", [])]
                query = self.search_query

                match = (
                    query in name or
                    query in subtitle or
                    query in desc or
                    any(query in tag for tag in tags)
                )
                if not match:
                    continue

            card = ToolCard(t, self)
            self.cards_box.pack_start(card, False, False, 0)
            visible_count += 1

        if visible_count == 0:
            empty_lbl = Gtk.Label(label="Keine Tools für diese Suche oder Kategorie gefunden.")
            empty_lbl.get_style_context().add_class("tool-desc")
            empty_lbl.set_margin_top(40)
            self.cards_box.pack_start(empty_lbl, True, True, 0)

        self.cards_box.show_all()

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
        # We can display a gentle info or print to stdout
        print(f"[Craft Launcher] {message}")


def main():
    app = CraftLauncherWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

