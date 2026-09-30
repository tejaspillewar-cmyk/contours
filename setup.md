# Setup Guide – DXF → 3D Terrain Viewer

This guide is written for people with **no coding experience**. If you can install a program and double-click a file, you can do this. Allow about **15 minutes** the first time (most of it is waiting for downloads). After that, starting the app takes about 10 seconds.

**What the app does:** you give it a survey drawing (`.dxf` file) that has spot levels written as text, and it builds an interactive 3D ground model. It can then calculate cut & fill volumes for a plinth level, draw section cuts, and let you slice through the model with a moving plane.

---

## What you need

| Item | Notes |
|------|-------|
| A **Windows** PC (Windows 10 or 11) | Mac/Linux users: see [Mac / Linux](#mac--linux) at the bottom |
| An **internet connection** | Only for the first-time setup (about 400 MB of downloads) |
| About **1.5 GB** free disk space | For the app and its libraries |
| A modern browser | Chrome, Edge or Firefox |
| A survey **`.dxf`** file | Spot levels must be **TEXT or MTEXT** entities holding the level number (e.g. `101.35`) |

You do **not** need administrator rights if you install Python "for me only" (the default on the Microsoft Store).

---

## Step 1 – Install Python (one time only)

The app is written in Python, so Python must be installed first.

1. Open **https://www.python.org/downloads/** and click the big yellow **Download Python 3.12.x** button.
2. Run the downloaded installer.
3. ⚠️ **On the very first screen, tick the box "Add python.exe to PATH"** (bottom of the window). This is the step people most often miss.
4. Click **Install Now** and wait for "Setup was successful", then **Close**.

> **Already have Python?** Version **3.11 or newer** works (3.12 recommended). To check, press `Windows key + R`, type `cmd`, press Enter, then type `python --version` and press Enter.

---

## Step 2 – Get the app files

Pick **one** of the two ways.

### Option A – Download a ZIP (easiest)

1. Open the project page: **https://github.com/tejaspillewar-cmyk/contours**
2. Click the green **`<> Code`** button → **Download ZIP**.
3. Find the ZIP in your Downloads folder, **right-click → Extract All…**, and choose a place such as `C:\Terrain` or your Desktop.
4. ⚠️ **Extract it – do not run files from inside the ZIP.** Windows lets you open a ZIP like a folder, but the app will not work from there.

### Option B – With Git (if you already use it)

```
git clone https://github.com/tejaspillewar-cmyk/contours.git
```

---

## Step 3 – First run (installs everything automatically)

1. Open the extracted folder. You should see files like `app.py`, `setup.md` and **`SETUP_AND_RUN.bat`**.
2. **Double-click `SETUP_AND_RUN.bat`.**
3. If Windows shows a blue **"Windows protected your PC"** box: click **More info → Run anyway**. (This appears for any downloaded script. The file is plain text – you can right-click → Edit to read exactly what it does.)
4. A black window opens and shows progress:
   - `[1/3] Python found` – good.
   - `[2/3] Creating private environment` – makes a `.venv` folder inside the app folder. Nothing is installed system-wide.
   - `[3/3] Installing required packages` – **takes 2–5 minutes**. Lots of text scrolling past is normal. **Do not close the window.**
5. When it says **"Starting… your browser will open"**, your browser opens the app at `http://localhost:8501`.

> The black window is the "engine" of the app. **Keep it open while you work.** Closing it stops the app.

---

## Step 4 – Use the app

### 4.1 Load your drawing
1. In the **left sidebar**, click **Browse files** (or drag your `.dxf` onto it).
2. Under **Configuration**:
   - **Drawing units** – pick `m` or `ft` to match your drawing. Every area and volume is labelled with this.
   - **Elevation Text Layer** – choose the CAD layer that holds the level numbers. If you get "No elevation points extracted", try another layer.
   - *(Optional)* tick **Clip to boundary polygon** and pick the layer with the site boundary, to trim the model to the plot.
3. The sidebar now shows the min/max level, relief and number of points found.

### 4.2 Tabs

| Tab | What it is for |
|-----|----------------|
| **📐 2D Preview** | Check that the drawing and the detected level points look right |
| **🏔️ 3D Terrain & Sections** | The 3D model, the plinth plane, the ground block, section cuts and the Section Cutter |
| **📊 Cut & Fill Insights** | The cut/fill report, haulage estimate and a chart of volumes vs plinth level |
| **💾 Export** | Download the model as `.OBJ` (Blender, SketchUp…) or `.DXF` (AutoCAD) |

### 4.3 Plinth level and cut/fill (sidebar → "Plinth & Ground Block")
- **Show ground block** adds side walls and a base so it looks like a real piece of land. Set how deep below the lowest point it goes.
- **Plinth plane** choices:
  - **Off** – no plane.
  - **Manual level** – type any level (RL).
  - **Balanced (cut = fill)** – the level where the soil you dig equals the soil you need to fill. Nothing is carted in or out.
  - **Least earthwork** – the level that moves the smallest total amount of soil (cut + fill).
- The blue plane appears in 3D and a **red line** shows where the ground meets it. Full numbers are in the **Cut & Fill Insights** tab.
- **Cut** = ground *above* the plinth (dig it away). **Fill** = ground *below* the plinth (bring soil in). Volumes are exact for the ground model and are *in-situ* (bank) volumes. The haulage section lets you add swell and compaction allowances.

### 4.4 Drawing a section line
1. Scroll below the 3D model to **Section cuts** – you'll see a coloured plan map.
2. **Hold the left mouse button and drag** across the plan, then let go. That's it – the section is created.
3. Hold **Shift** while dragging to make the line perfectly **horizontal or vertical**.
4. For a section with bends, click **Polyline** in the small toolbar on the plan:
   - Drag to add each segment (each one starts where the last ended).
   - Press **Enter** (or double-click, or click **Finish ⏎**) when done.
   - **Backspace** / **Undo** removes the last point, **Esc** cancels.
5. The section appears on the 3D model (cyan line) and its **profile** is drawn underneath, with cut (red) and fill (blue) shaded against the plinth. You can download the profile as CSV.
6. Map controls: **right-mouse-drag** = move the map, **mouse wheel** = zoom, **Fit** = reset the view.

### 4.5 The Section Cutter (visual slicing tool)
1. In the 3D tab, switch on **✂️ Section Cutter**.
2. **Click and drag the cyan plane** to slice through the model. Drag anywhere else to rotate.
3. Choose **⟂ X**, **⟂ Y** or set any **Angle**. Use **Hide → side A/B** to remove one half and look inside.
4. Click **Section View** (top-left of the viewer) to see the slice as a flat profile, with cut/fill areas and level read-out under the mouse.
5. Switch the toggle off to return to the normal 3D view. This tool is only for looking – it is separate from the section lines above.

### 4.6 Mouse controls in the normal 3D view
**Drag** = rotate · **Shift + drag** or **right-drag** = move · **Scroll** = zoom · **Double-click** = reset. The **Camera view** menu jumps to top / north / south / east / west.

---

## Next time you want to use it

Just **double-click `SETUP_AND_RUN.bat` again**. It notices everything is already installed and starts in a few seconds.

**To stop the app:** close the black window (or click in it and press `Ctrl + C`).

**To update to a newer version:** download the new ZIP (Step 2) and extract it over the old folder, *keeping the `.venv` folder*. If the new version needs extra packages, delete the file `.venv\deps_installed.flag` and run `SETUP_AND_RUN.bat` again.

---

## Troubleshooting

| What you see | What to do |
|--------------|-----------|
| **"Python 3.11 or newer was not found"** | Install Python (Step 1) and make sure **"Add python.exe to PATH"** was ticked. If unsure, run the installer again → **Modify**/**Repair** and tick it. Then close the black window and double-click the file again. |
| Typing `python` opens the **Microsoft Store** | Windows has a placeholder. Install Python from python.org (Step 1), or turn off *Settings → Apps → Advanced app settings → App execution aliases → python.exe*. |
| **Setup fails while installing** | Check your internet connection (some office networks/firewalls block downloads – try a personal hotspot). Delete the `.venv` folder and run again. |
| **"Port 8501 is already in use"** | The app is already running in another black window. Close that one first (or just use it: open `http://localhost:8501`). |
| Browser doesn't open by itself | Open your browser and type `localhost:8501` in the address bar. |
| Page says **"This site can't be reached"** | The black window was closed or is still starting. Make sure it's open and wait 10–20 seconds. |
| **"No elevation points extracted"** | Pick a different *Elevation Text Layer*. The levels must be TEXT/MTEXT entities. If the drawing uses blocks with attributes or only contour polylines, they aren't read yet – explode the blocks or convert to text first. |
| Model looks flat / very stretched | Use **Z exag. (×)** in the 3D controls. Also check that *Drawing units* match your file. |
| Levels are read wrongly (e.g. include the sheet number) | Choose a layer that contains **only** spot levels. |
| Section drawing does nothing | Make sure you *drag* (a plain click is ignored) and that the line starts on the coloured map. |
| Cut/Fill numbers seem too big or small | Check *Drawing units*, and the plinth level shown in the sidebar. Remember values are volumes in cubic metres (m³) or cubic feet (ft³). |
| **Windows protected your PC** warning | Click **More info → Run anyway**. |
| Antivirus blocks `SETUP_AND_RUN.bat` | Allow it, or run the [manual commands](#manual-commands-alternative) below in a Command Prompt. |

Still stuck? Take a screenshot of the black window (it usually explains the problem in the last few lines) and share it with whoever maintains the project.

---

## Manual commands (alternative)

If you prefer typing commands, or the `.bat` file is blocked. Open the app folder, click the address bar, type `cmd` and press Enter, then:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

Next time you only need the last line.

## Mac / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501. Next time: `source .venv/bin/activate` and `streamlit run app.py`.

---

## What's in the folder

| File / folder | Purpose |
|---------------|---------|
| `SETUP_AND_RUN.bat` | One-click setup and launcher (use this) |
| `app.py` | The application |
| `section_canvas/` | The drag-to-draw section map |
| `cutter_view/` | The 3D Section Cutter (includes its own copy of the 3D library, so it works offline) |
| `requirements.txt` | List of Python packages installed automatically |
| `.streamlit/config.toml` | Dark colour theme |
| `README.md`, `WORKFLOW.md`, `COMPUTING_LOGIC.md` | Background information on how the app works and calculates |
| `RUN_TERRAIN_VIEWER.bat` | Launcher for the *portable ZIP edition* that ships with its own bundled Python (not needed if you used this guide) |
| `.venv/` | Created automatically on first run – the private Python setup. Safe to delete; it will be rebuilt |

**Privacy:** the app runs entirely on your own computer. Your DXF files are not uploaded anywhere. The internet is only used during the first-time package download.
