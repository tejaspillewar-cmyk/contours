# 🏔️ DXF → 3D Terrain Viewer

Convert 2D landscape survey DXF files into interactive 3D terrain surfaces — right in your browser.

---

## ⚡ Quick Start (Double-click to run)

1. **Double-click** `RUN_TERRAIN_VIEWER.bat`
2. Wait for first-time setup (installs dependencies automatically, ~1-2 min)
3. Your browser opens → upload a `.dxf` file → done!

> **No admin rights needed.** Everything installs into a local `.venv` folder inside this directory.

---

## 📋 Prerequisites

- **Python 3.9+** must be installed.  
  If it's not, install from the **Microsoft Store** (search "Python 3.12") — no admin rights required.

---

## 🔧 What the launcher does (automatically)

| Step | What happens |
|------|-------------|
| 1 | Finds Python on your system (checks `python`, `py`, common install paths) |
| 2 | Creates a virtual environment in `.venv/` (first run only) |
| 3 | Installs all required packages from `requirements.txt` (first run only) |
| 4 | Launches the Streamlit app in your default browser |

---

## 📦 Sharing with your team

1. **Zip** this entire folder (`D01_EXCAVATION/`)
2. Send it to your colleague
3. They **unzip** and **double-click** `RUN_TERRAIN_VIEWER.bat`

That's it. The `.venv` folder is auto-created on their machine — don't include it in the zip.

### What to include in the zip:
```
D01_EXCAVATION/
├── app.py                    ← Main application
├── requirements.txt          ← Python dependencies
├── RUN_TERRAIN_VIEWER.bat    ← One-click launcher
├── .streamlit/config.toml    ← Theme settings
└── README.md                 ← This file
```

### What to exclude:
```
.venv/    ← Auto-created on each machine (large, not portable)
```

---

## 🖥️ Features

- **DXF Upload** — Drag & drop or browse for `.dxf` survey files
- **Layer Inspection** — View entity counts and select elevation/boundary layers
- **2D Preview** — Interactive Plotly preview of DXF entities with elevation highlights
- **3D Terrain** — Delaunay-triangulated surface with:
  - Elevation-based colorscale (Earth, Viridis, Turbo, etc.)
  - Wireframe overlay
  - Contour lines at customizable intervals
  - Z-axis exaggeration control
  - Full zoom/pan/rotate
- **Boundary Clipping** — Optionally clip mesh to a site boundary polyline
- **Export** — Download as `.obj` (Blender/SketchUp) or `.dxf` (AutoCAD 3DFACE)

---

## 📏 Supported Elevation Text Formats

The parser recognizes these patterns in TEXT/MTEXT entities:

| Example | Parsed Value |
|---------|-------------|
| `12.45` | 12.45 |
| `+12.45` | 12.45 |
| `-3.20` | -3.20 |
| `12.45m` | 12.45 |
| `RL 104.2` | 104.2 |
| `EL: 98.76` | 98.76 |
| `LEVEL-12.5` | 12.5 |
| `FFL +3.500` | 3.500 |

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.12 from the Microsoft Store |
| Dependencies fail to install | Check your internet connection; re-run the `.bat` |
| App won't open in browser | Navigate to `http://localhost:8501` manually |
| No elevation points found | Check that you selected the correct layer, and that text entities contain numeric values |
| Need to reinstall dependencies | Delete the `.venv` folder and re-run the `.bat` |
