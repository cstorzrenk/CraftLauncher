# 🎨 Craft Launcher

Ein moderner grafischer Desktop-Launcher (GTK3) zur Schnellauswahl, Verwaltung und Aktualisierung von Open-Source Kreativ- und Office-Tools unter Linux.

---

## ✨ Features

* **Vollautomatische 1-Klick-Bereitstellung (Zero-Config):** Niemand muss die einzelnen GitHub-Repositories manuell besuchen oder Code herunterladen! Beim ersten Klick auf **`⬇️ Installieren & Starten`** (oder über **`⬇️ Alle bereitstellen`** oben rechts) lädt der Launcher den Quellcode automatisch im Hintergrund von GitHub, entpackt ihn nach `workspace/`, kompiliert die schnelle Release-Version und startet das Programm sofort.
* **Original-App-Icons:** Zeigt für jedes der 15 Tools das offizielle hochauflösende App-Logo (`icons/*.png`) an.
* **Schnellsuche & Kategorie-Filter:** Sofortiges Filtern nach Tool-Name, Funktion oder bekannten Alternativen (*Photoshop*, *Lightroom*, *Illustrator*, *Figma*, *InDesign*, *Excel*, *Word*, *AutoCAD*, *SolidWorks*, *Premiere* u.v.m.).
* **Integrierte GitHub-Update-Funktion:** Prüft per Klick auf `🌐 Updates prüfen` gegen die GitHub-API, ob für die Tools neue Commits vorliegen, und aktualisiert sie bei Bedarf vollautomatisch im Hintergrund.
* **Entwickler-Integration:** Direktes Öffnen einzelner Tools im Terminal (`📟`), in VS Code (`💻`) oder im Dateimanager (`📁`).

---

## 📦 Unterstützte Tools (`tools_config.json` – 15 Tools)

| Logo | Tool | Kategorie | Beschreibung / Alternative zu |
| :---: | :--- | :--- | :--- |
| <img src="icons/photocraft.png" width="28"> | **PhotoCraft** | Grafik & Bild | Ebenenbasierte Bildbearbeitung (*Adobe Photoshop*) |
| <img src="icons/lightcraft.png" width="28"> | **LightCraft** | Grafik & Bild | Zerstörungsfreie RAW-Fotoentwicklung & Katalog (*Adobe Lightroom*) |
| <img src="icons/vectorcraft.png" width="28"> | **VectorCraft** | Grafik & Bild | Vektorillustration & SVG (*Adobe Illustrator*) |
| <img src="icons/figcraft.png" width="28"> | **FigCraft** | Grafik & Bild | UI/UX Interface-Design & Prototyping (*Figma*) |
| <img src="icons/designcraft.png" width="28"> | **DesignCraft** | Dokumente & Layout | Desktop Publishing & Layout (*Adobe InDesign*) |
| <img src="icons/pdfcraft.png" width="28"> | **PdfCraft** | Dokumente & Layout | PDF-Reader, Editor & Organizer (*Adobe Acrobat*) |
| <img src="icons/filmcraft.png" width="28"> | **FilmCraft** | Video & Audio | Nichtlinearer Videoschnitt (*Adobe Premiere Pro*) |
| <img src="icons/soundcraft.png" width="28"> | **SoundCraft** | Video & Audio | Digitale Audio-Workstation / DAW (*Adobe Audition*) |
| <img src="icons/effectcraft.png" width="28"> | **EffectCraft** | Video & Audio | Motion Graphics & VFX Compositing (*Adobe After Effects*) |
| <img src="icons/cadcraft.png" width="28"> | **CadCraft** | 3D & CAD | Technisches 2D/3D CAD & Konstruktion (*AutoCAD*) |
| <img src="icons/solidcraft.png" width="28"> | **SolidCraft** | 3D & CAD | Parametrisches 3D-CAD & Volumenmodellierung (*SolidWorks / Fusion 360*) |
| <img src="icons/artcraft.png" width="28"> | **ArtCraft** | 3D & CAD | Interaktive KI-Kreativ-IDE & 2D/3D-Compositing |
| <img src="icons/gridcraft.png" width="28"> | **GridCraft** | Office | Reaktive Tabellenkalkulation (*Microsoft Excel*) |
| <img src="icons/wordcraft.png" width="28"> | **WordCraft** | Office | Textverarbeitung & DOCX (*Microsoft Word*) |
| <img src="icons/deckcraft.png" width="28"> | **DeckCraft** | Präsentationen & KI | KI-gestützter Präsentationsgenerator (FastAPI + Next.js) |

---

## 🚀 Schnellstart (für neue Nutzer / Zweit-PC)

```bash
git clone https://github.com/cstorzrenk/CraftLauncher.git
cd CraftLauncher
./setup.sh          # Einmalig System-Pakete & Rust einrichten
./run_launcher.sh   # Launcher starten – Tools laden & bauen sich automatisch per Klick!
```
