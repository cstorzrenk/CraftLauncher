# 🎨 Craft Launcher

Ein moderner grafischer Desktop-Launcher (GTK3) zur Schnellauswahl, Verwaltung und Aktualisierung von Open-Source Kreativ- und Office-Tools unter Linux.

---

## ✨ Features

* **Schnellsuche & Kategorie-Filter:** Sofortiges Filtern nach Tool-Name, Funktion oder bekannten Alternativen (*Photoshop*, *Illustrator*, *InDesign*, *Excel*, *Word*, *AutoCAD*, *Premiere* u.v.m.).
* **Automatisches Entpacken & Bauen:** Lädt oder entpackt die hinterlegten `.zip`-Archive automatisch in den isolierten Arbeitsordner `workspace/` und startet die kompilierte Release-Binärdatei ohne Verzögerung.
* **Integrierte GitHub-Update-Funktion:** Prüft per Klick auf `🌐 Updates prüfen` gegen die GitHub-API, ob für die Tools neue Commits vorliegen, lädt bei Bedarf das aktuelle ZIP-Archiv herunter und kompiliert das Update im Hintergrund.
* **Entwickler-Integration:** Direktes Öffnen einzelner Tools im Terminal (`📟`), in VS Code (`💻`) oder im Dateimanager (`📁`).

---

## 📦 Unterstützte Tools (`tools_config.json`)

| Icon | Tool | Kategorie | Beschreibung / Alternative zu |
| :---: | :--- | :--- | :--- |
| 🖼️ | **PhotoCraft** | Grafik & Bild | Ebenenbasierte Bildbearbeitung (*Adobe Photoshop*) |
| 📐 | **VectorCraft** | Grafik & Bild | Vektorillustration & SVG (*Adobe Illustrator*) |
| 📑 | **DesignCraft** | Dokumente & Layout | Desktop Publishing & Layout (*Adobe InDesign*) |
| 📄 | **PdfCraft** | Dokumente & Layout | PDF-Reader, Editor & Organizer (*Adobe Acrobat*) |
| 🎬 | **FilmCraft** | Video & Audio | Nichtlinearer Videoschnitt (*Adobe Premiere Pro*) |
| 🎵 | **SoundCraft** | Video & Audio | Digitale Audio-Workstation / DAW (*Adobe Audition*) |
| ✨ | **EffectCraft** | Video & Audio | Motion Graphics & VFX Compositing (*Adobe After Effects*) |
| 🏗️ | **CadCraft** | 3D & CAD | 2D/3D CAD & Konstruktion (*AutoCAD*) |
| 🖌️ | **ArtCraft** | 3D & CAD | Interaktive KI-Kreativ-IDE & 2D/3D-Compositing |
| 📊 | **GridCraft** | Office | Reaktive Tabellenkalkulation (*Microsoft Excel*) |
| 📝 | **WordCraft** | Office | Textverarbeitung & DOCX (*Microsoft Word*) |
| 🎴 | **DeckCraft** | Präsentationen & KI | KI-gestützter Präsentationsgenerator (FastAPI + Next.js) |

---

## 🚀 Installation & Start

### Voraussetzungen (Ubuntu / Debian)
* Python 3 mit PyGObject (`python3-gi`, `gir1.2-gtk-3.0`)
* Rust & Cargo (`rustup`) zum Kompilieren der Rust-basierten Tools
* System-Bibliotheken für Audio/GUI-Builds:
  ```bash
  sudo apt update && sudo apt install -y libasound2-dev libglib2.0-dev libwebkit2gtk-4.1-dev libclang-dev git cmake
  ```

### Launcher starten
```bash
./run_launcher.sh
```
*(Oder direkt über das Anwendungsmenü, sofern `craft-launcher.desktop` unter `~/.local/share/applications/` hinterlegt ist.)*
