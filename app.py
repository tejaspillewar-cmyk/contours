"""
DXF → 3D Terrain Surface Viewer
================================
A Streamlit application that converts 2D landscape survey DXF files
into interactive 3D terrain surfaces with Delaunay triangulation.

Author  : ET Survey Tools
Version : 1.0.0
"""

import hashlib
import io
import os
import re
import tempfile
from pathlib import Path

import ezdxf
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components
import shapely
from scipy.spatial import Delaunay
from shapely.geometry import Polygon

pio.templates["plotly_dark"].layout.font.size = 11   # smaller chart text everywhere

# ──────────────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DXF → 3D Terrain",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────
# Custom Styles
# ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Sidebar ─────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #38bdf8 !important;
    }

    /* ── Metric cards ────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
    }

    /* compact metrics inside the sidebar */
    section[data-testid="stSidebar"] div[data-testid="stMetric"] {
        padding: 6px 10px;
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] div[data-testid="stMetric"] label,
    section[data-testid="stSidebar"] div[data-testid="stMetric"] label p {
        font-size: 0.62rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMetricValue"],
    section[data-testid="stSidebar"] div[data-testid="stMetricValue"] * {
        font-size: 1.05rem !important;
        line-height: 1.3 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 { font-size: 1rem !important; }
    section[data-testid="stSidebar"] .stMarkdown h2 { font-size: 1.15rem !important; }
    section[data-testid="stSidebar"] label p { font-size: 0.82rem !important; }
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
        font-size: 0.72rem !important;
    }

    /* ── File uploader ───────────────────────────────── */
    section[data-testid="stFileUploader"] {
        border: 2px dashed #475569;
        border-radius: 12px;
        padding: 12px;
        transition: border-color 0.2s;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: #38bdf8;
    }

    /* ── Plotly chart container ───────────────────────── */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }

    /* ── Expander headers ───────────────────────────── */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #38bdf8 !important;
    }

    /* ── Global density: smaller type, tighter spacing ─── */
    html { font-size: 14px; }
    .block-container { padding: 4.2rem 1.6rem 2rem !important; max-width: 100% !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.6rem; }
    hr { margin: 0.6rem 0 !important; }
    h1 { font-size: 1.45rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.05rem !important; }
    h4 { font-size: 0.95rem !important; font-weight: 650 !important; margin: 0.2rem 0 0.1rem !important; padding: 0 !important; }
    h5 { font-size: 0.85rem !important; font-weight: 600 !important; color: #94a3b8; margin: 0.4rem 0 0 !important; padding: 0 !important; }
    p, li { font-size: 0.86rem; }
    div[data-testid="stCaptionContainer"], .stCaption { font-size: 0.74rem !important; color: #7c8ba3; }
    div[data-testid="stWidgetLabel"] p { font-size: 0.74rem !important; color: #94a3b8; }
    div[data-testid="stCheckbox"] label p, div[data-testid="stToggle"] label p, div[data-testid="stRadio"] label p {
        font-size: 0.82rem !important; color: #cbd5e1;
    }
    input, textarea { font-size: 0.82rem !important; }
    div[data-baseweb="select"] > div, div[data-testid="stNumberInput"] > div > div { min-height: 2rem; font-size: 0.82rem; }
    .stButton > button, .stDownloadButton > button {
        font-size: 0.78rem; padding: 0.2rem 0.75rem; min-height: 1.9rem; border-radius: 7px;
    }
    /* tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid #26344f; }
    .stTabs [data-baseweb="tab"] { padding: 0.35rem 0.9rem; height: auto; }
    .stTabs [data-baseweb="tab"] p { font-size: 0.82rem; font-weight: 600; }
    /* metric cards */
    div[data-testid="stMetric"] { padding: 8px 12px; border-radius: 9px; box-shadow: none; }
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] label p {
        font-size: 0.64rem !important; letter-spacing: 0.04em;
    }
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * { font-size: 1.2rem !important; }
    div[data-testid="stMetricDelta"], div[data-testid="stMetricDelta"] * { font-size: 0.7rem !important; }
    div[data-testid="stDataFrame"] { font-size: 0.8rem; }
    div[data-testid="stAlert"] { padding: 0.5rem 0.75rem; }
    div[data-testid="stAlert"] p { font-size: 0.82rem; }
    .stPlotlyChart { box-shadow: none; border: 1px solid #1e2a44; }
    section[data-testid="stSidebar"][aria-expanded="true"] { width: 270px !important; min-width: 270px !important; }
    section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] > div { padding-top: 0.6rem; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0.45rem; }

    /* Hide Streamlit branding */
    #MainMenu, footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────
ELEVATION_RE = re.compile(
    r"""
    (?:RL|EL|ELEV|LEVEL|FL|FFL|SSL|NGL|TBM)?   # optional prefix
    \s*[:\-]?\s*                                  # separator
    ([+-]?\d+(?:\.\d+)?)                         # numeric value (captured)
    \s*(?:m|M|mtr|ft|')?                         # optional unit suffix
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Label -> valid Plotly colorscale (name or explicit stops).
# "Terrain" is not a built-in Plotly name, so it is defined as explicit stops.
# Drag-to-draw plan canvas (custom Streamlit component, no build step needed)
section_canvas = components.declare_component(
    "section_canvas", path=str(Path(__file__).parent / "section_canvas")
)

# Interactive 3D section cutter (three.js, vendored in ./cutter_view)
section_cutter = components.declare_component(
    "section_cutter", path=str(Path(__file__).parent / "cutter_view")
)

# Drawing units (set from the sidebar); volumes/areas are derived from it.
UNITS = {"u": "m"}


def u1() -> str:
    return UNITS["u"]


def u2() -> str:
    return UNITS["u"] + "²"


def u3() -> str:
    return UNITS["u"] + "³"


COLORSCALES = {
    "Earth": "earth",
    "Terrain": [
        [0.00, "#2b6cb0"],  # low  – water/blue
        [0.15, "#2f855a"],  # green
        [0.40, "#a3bf5e"],  # light green
        [0.60, "#e6d690"],  # sand
        [0.80, "#a0785a"],  # brown
        [1.00, "#f7fafc"],  # high – snow
    ],
    "Viridis": "viridis",
    "Turbo": "turbo",
    "Inferno": "inferno",
    "Cividis": "cividis",
    "Hot": "hot",
}

CAMERAS = {
    "Isometric": dict(eye=dict(x=1.4, y=-1.4, z=1.0), up=dict(x=0, y=0, z=1)),
    "Top (plan)": dict(eye=dict(x=0.0, y=0.0, z=2.6), up=dict(x=0, y=1, z=0)),
    "South": dict(eye=dict(x=0.0, y=-2.4, z=0.35), up=dict(x=0, y=0, z=1)),
    "East": dict(eye=dict(x=2.4, y=0.0, z=0.35), up=dict(x=0, y=0, z=1)),
    "North": dict(eye=dict(x=0.0, y=2.4, z=0.35), up=dict(x=0, y=0, z=1)),
    "West": dict(eye=dict(x=-2.4, y=0.0, z=0.35), up=dict(x=0, y=0, z=1)),
}

# ──────────────────────────────────────────────────────────────────────
# Rendering budgets
# ──────────────────────────────────────────────────────────────────────
# Survey DXFs can hold hundreds of thousands of spot levels (a 2.5 m grid
# over a large parcel easily reaches 300 000). Triangulating all of them
# gives ~2 triangles per point, and handing that many primitives to Plotly
# or to the three.js views locks up the browser. Everything below these
# ceilings is drawn in full; above them the app thins or skips, and says so.
MAX_SURFACE_POINTS = 25_000     # default cap for the triangulated surface
MAX_PREVIEW_LINE_PTS = 150_000  # vertices in the 2D background-geometry trace
MAX_PREVIEW_MARKERS = 20_000    # markers per 2D scatter trace
MAX_POINT_LABELS = 1_000        # per-point text labels (slowest Plotly mark)
MAX_WIREFRAME_TRIS = 40_000     # triangles drawn as a wireframe overlay
MAX_CONTOUR_SEGMENTS = 120_000  # contour segments across all levels
MAX_WARNINGS = 200              # warnings kept from one extraction pass

PLOT_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "doubleClick": "reset",
    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2, "filename": "terrain_3d"},
}


# ══════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════
def file_sig(file_bytes: bytes) -> str:
    """Cheap, stable identity for an uploaded file, used as a cache key.

    Hashing 100+ MB on every rerun would itself be a bottleneck, so only the
    length plus the head and tail of the payload go into the digest.
    """
    h = hashlib.sha1()
    h.update(str(len(file_bytes)).encode())
    h.update(file_bytes[:262144])
    h.update(file_bytes[-262144:])
    return h.hexdigest()


# The ezdxf document is held with cache_resource, NOT cache_data: cache_data
# pickles its value and unpickles a fresh copy on every lookup, which for a
# large survey DXF is ~100 MB of serialisation on every single widget change.
@st.cache_resource(show_spinner=False, max_entries=1)
def parse_dxf(_file_bytes: bytes, sig: str):
    """Read a DXF from raw bytes and return the ezdxf document."""
    tmp = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
    try:
        tmp.write(_file_bytes)
        tmp.close()
        return ezdxf.readfile(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# Every helper below walks the whole model space, so each one is cached on the
# document signature. `_doc` is underscore-prefixed so Streamlit skips hashing
# it and keys on `sig` instead.
@st.cache_data(show_spinner=False, max_entries=2)
def scan_dxf(_doc, sig: str) -> tuple[list[str], dict]:
    """One pass over model space: sorted layer names and per-type entity counts."""
    summary: dict[str, int] = {}
    layers: set[str] = set()
    for e in _doc.modelspace():
        layers.add(e.dxf.layer)
        t = e.dxftype()
        summary[t] = summary.get(t, 0) + 1
    return sorted(layers), summary


@st.cache_data(show_spinner=False, max_entries=8)
def extract_elevation_points(_doc, layer: str, sig: str) -> tuple[np.ndarray, list[str], list]:
    """
    Extract (X, Y, Z) points from TEXT / MTEXT on *layer*.

    Returns
    -------
    points : ndarray of shape (N, 3)
    labels : list of raw text strings
    warnings : list of warning messages (capped at MAX_WARNINGS)
    """
    points, labels, warnings = [], [], []
    seen_xy: dict[tuple, float] = {}
    suppressed = 0

    def warn(msg: str) -> None:
        nonlocal suppressed
        if len(warnings) < MAX_WARNINGS:
            warnings.append(msg)
        else:
            suppressed += 1

    msp = _doc.modelspace()
    for entity in msp:
        if entity.dxf.layer != layer:
            continue
        if entity.dxftype() not in ("TEXT", "MTEXT"):
            continue

        # Coordinates
        if entity.dxftype() == "TEXT":
            ins = entity.dxf.insert
            raw = entity.dxf.text
        else:  # MTEXT
            ins = entity.dxf.insert
            raw = entity.text  # plain text content

        x, y = float(ins[0]), float(ins[1])

        # Parse elevation
        m = ELEVATION_RE.search(raw)
        if m is None:
            warn(f"⚠️ Non-numeric text ignored: '{raw}' at ({x:.2f}, {y:.2f})")
            continue
        z = float(m.group(1))

        # Deduplicate
        key = (round(x, 4), round(y, 4))
        if key in seen_xy and abs(seen_xy[key] - z) > 0.001:
            warn(
                f"⚠️ Duplicate XY ({x:.2f}, {y:.2f}) with different Z "
                f"({seen_xy[key]:.3f} vs {z:.3f}) — keeping first."
            )
            continue
        seen_xy[key] = z

        points.append([x, y, z])
        if len(labels) < MAX_POINT_LABELS:
            labels.append(raw.strip())

    if suppressed:
        warnings.append(f"… and {suppressed:,} more similar warnings (not listed).")
    if not points:
        return np.empty((0, 3)), labels, warnings
    return np.array(points), labels, warnings


def decimate_points(points: np.ndarray, max_points: int) -> np.ndarray:
    """
    Thin a dense point cloud down to roughly *max_points*, on a regular XY grid.

    A 2.5 m spot-level grid over a large parcel can hold 300 000 points; the
    resulting TIN has ~600 000 triangles, which no browser will draw. One point
    per grid cell is kept (the one nearest the cell centre, so the sample stays
    even), plus the highest and lowest points so relief is never clipped.
    """
    if max_points <= 0 or len(points) <= max_points:
        return points

    x, y = points[:, 0], points[:, 1]
    x0, x1 = float(x.min()), float(x.max())
    y0, y1 = float(y.min()), float(y.max())
    span_x, span_y = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    ratio = span_x / span_y

    def thin(cells: int) -> np.ndarray:
        """Indices of one point per occupied cell of a `cells`-cell grid."""
        ny = max(int(np.sqrt(cells / ratio)), 1)
        nx = max(cells // ny, 1)
        cx = np.clip(((x - x0) / span_x * nx).astype(np.int64), 0, nx - 1)
        cy = np.clip(((y - y0) / span_y * ny).astype(np.int64), 0, ny - 1)
        cell = cx * ny + cy
        # Distance to the cell centre, so each cell gives up its most central
        # point and the surviving sample stays evenly spread.
        mid_x = x0 + (cx + 0.5) * span_x / nx
        mid_y = y0 + (cy + 0.5) * span_y / ny
        dist = (x - mid_x) ** 2 + (y - mid_y) ** 2
        order = np.lexsort((dist, cell))
        return order[np.unique(cell[order], return_index=True)[1]]

    keep = thin(max_points)
    # Sites are rarely rectangular, so a fair share of cells come out empty and
    # the first pass undershoots. Scale the grid up by the measured shortfall.
    if len(keep) < 0.9 * max_points:
        scaled = int(max_points * max_points / max(len(keep), 1))
        retry = thin(min(scaled, 8 * max_points))
        if max_points >= len(retry) > len(keep):
            keep = retry

    keep = np.union1d(keep, [int(points[:, 2].argmin()), int(points[:, 2].argmax())])
    return points[keep]


@st.cache_data(show_spinner=False, max_entries=8)
def extract_boundary(_doc, layer: str, sig: str) -> Polygon | None:
    """Return the first LWPOLYLINE / POLYLINE on *layer* as a Shapely Polygon."""
    msp = _doc.modelspace()
    for entity in msp:
        if entity.dxf.layer != layer:
            continue
        if entity.dxftype() == "LWPOLYLINE":
            coords = [(p[0], p[1]) for p in entity.get_points(format="xyb")]
            if len(coords) >= 3:
                return Polygon(coords)
        elif entity.dxftype() == "POLYLINE":
            coords = [(v.dxf.location[0], v.dxf.location[1]) for v in entity.vertices]
            if len(coords) >= 3:
                return Polygon(coords)
    return None


@st.cache_data(show_spinner=False, max_entries=2)
def extract_all_entities_2d(_doc, sig: str, with_texts: bool = True) -> dict[str, list]:
    """
    Extract lightweight 2D geometry for every entity in model space.

    Returns a dict of flat coordinate lists ready for Plotly traces. Line
    vertices stop accumulating at MAX_PREVIEW_LINE_PTS and text positions are
    skipped entirely when *with_texts* is false, so a drawing with a quarter of
    a million labels still yields a payload the browser can render.
    """
    lines_x, lines_y = [], []
    pts_x, pts_y = [], []
    txt_x, txt_y, txt_labels = [], [], []
    truncated = False

    msp = _doc.modelspace()
    for e in msp:
        if len(lines_x) > MAX_PREVIEW_LINE_PTS:
            truncated = True
            break
        dtype = e.dxftype()
        try:
            if dtype == "LINE":
                lines_x += [e.dxf.start[0], e.dxf.end[0], None]
                lines_y += [e.dxf.start[1], e.dxf.end[1], None]
            elif dtype == "LWPOLYLINE":
                pts = list(e.get_points(format="xy"))
                if e.closed:
                    pts.append(pts[0])
                for p in pts:
                    lines_x.append(p[0])
                    lines_y.append(p[1])
                lines_x.append(None)
                lines_y.append(None)
            elif dtype == "POLYLINE":
                verts = [(v.dxf.location[0], v.dxf.location[1]) for v in e.vertices]
                if e.is_closed:
                    verts.append(verts[0])
                for v in verts:
                    lines_x.append(v[0])
                    lines_y.append(v[1])
                lines_x.append(None)
                lines_y.append(None)
            elif dtype == "CIRCLE":
                cx, cy = e.dxf.center[0], e.dxf.center[1]
                r = e.dxf.radius
                theta = np.linspace(0, 2 * np.pi, 64)
                lines_x += (cx + r * np.cos(theta)).tolist() + [None]
                lines_y += (cy + r * np.sin(theta)).tolist() + [None]
            elif dtype == "ARC":
                cx, cy = e.dxf.center[0], e.dxf.center[1]
                r = e.dxf.radius
                a1 = np.radians(e.dxf.start_angle)
                a2 = np.radians(e.dxf.end_angle)
                if a2 < a1:
                    a2 += 2 * np.pi
                theta = np.linspace(a1, a2, 64)
                lines_x += (cx + r * np.cos(theta)).tolist() + [None]
                lines_y += (cy + r * np.sin(theta)).tolist() + [None]
            elif dtype == "POINT":
                pts_x.append(e.dxf.location[0])
                pts_y.append(e.dxf.location[1])
            elif dtype in ("TEXT", "MTEXT"):
                if not with_texts or len(txt_x) >= MAX_PREVIEW_MARKERS:
                    continue
                ins = e.dxf.insert
                txt_x.append(ins[0])
                txt_y.append(ins[1])
                txt_labels.append(e.dxf.text if dtype == "TEXT" else e.text)
            elif dtype == "INSERT":
                pts_x.append(e.dxf.insert[0])
                pts_y.append(e.dxf.insert[1])
        except Exception:
            continue

    return {
        "lines_x": lines_x,
        "lines_y": lines_y,
        "pts_x": pts_x[:MAX_PREVIEW_MARKERS],
        "pts_y": pts_y[:MAX_PREVIEW_MARKERS],
        "txt_x": txt_x,
        "txt_y": txt_y,
        "txt_labels": txt_labels,
        "truncated": truncated,
    }


def build_2d_preview(
    entities_2d: dict,
    elev_points: np.ndarray | None = None,
    boundary: Polygon | None = None,
) -> go.Figure:
    """Build an interactive 2D Plotly preview of DXF entities."""
    fig = go.Figure()

    # Background geometry. Scattergl keeps these large traces on the GPU;
    # the SVG renderer stalls the tab well before 100 000 vertices.
    if entities_2d["lines_x"]:
        fig.add_trace(
            go.Scattergl(
                x=entities_2d["lines_x"],
                y=entities_2d["lines_y"],
                mode="lines",
                line=dict(color="#475569", width=0.8),
                name="DXF Geometry",
                hoverinfo="skip",
            )
        )
    if entities_2d["pts_x"]:
        fig.add_trace(
            go.Scattergl(
                x=entities_2d["pts_x"],
                y=entities_2d["pts_y"],
                mode="markers",
                marker=dict(size=3, color="#64748b"),
                name="Points / Blocks",
                hoverinfo="skip",
            )
        )
    if entities_2d["txt_x"]:
        fig.add_trace(
            go.Scattergl(
                x=entities_2d["txt_x"],
                y=entities_2d["txt_y"],
                mode="markers",
                marker=dict(size=4, color="#94a3b8", symbol="diamond"),
                name="All Texts",
                text=entities_2d["txt_labels"],
                hovertemplate="<b>%{text}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>",
            )
        )

    # Elevation points highlight
    if elev_points is not None and len(elev_points) > 0:
        shown = decimate_points(elev_points, MAX_PREVIEW_MARKERS)
        # Per-point text labels are the single most expensive Plotly mark;
        # past a thousand or so they are illegible anyway, so hover only.
        labelled = len(shown) <= MAX_POINT_LABELS
        fig.add_trace(
            go.Scattergl(
                x=shown[:, 0],
                y=shown[:, 1],
                mode="markers+text" if labelled else "markers",
                marker=dict(
                    size=9 if labelled else 5,
                    color=shown[:, 2],
                    colorscale="Turbo",
                    showscale=True,
                    colorbar=dict(title="Elev", thickness=14, len=0.5),
                    line=dict(width=1 if labelled else 0, color="white"),
                ),
                text=[f"{z:.2f}" for z in shown[:, 2]] if labelled else None,
                textposition="top center",
                textfont=dict(size=9, color="#38bdf8"),
                name="Elevation Points",
                hovertemplate="<b>Z = %{marker.color:.3f}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>",
            )
        )

    # Boundary
    if boundary is not None:
        bx, by = boundary.exterior.xy
        fig.add_trace(
            go.Scattergl(
                x=list(bx),
                y=list(by),
                mode="lines",
                line=dict(color="#f97316", width=2.5, dash="dash"),
                name="Boundary",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        xaxis=dict(
            scaleanchor="y",
            scaleratio=1,
            showgrid=True,
            gridcolor="#1e293b",
            zeroline=False,
        ),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", zeroline=False),
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(
            bgcolor="rgba(15,23,42,0.8)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(size=11),
        ),
        height=550,
    )
    return fig


def mesh_sig(points: np.ndarray, simplices: np.ndarray) -> str:
    """Cheap identity for a (points, simplices) mesh, for use as a cache key."""
    return (
        f"{points.shape}|{simplices.shape}|"
        f"{float(points[:, 0].sum()):.6f}|{float(points[:, 2].sum()):.6f}|"
        f"{int(simplices.sum())}"
    )


@st.cache_data(show_spinner=False, max_entries=4)
def triangulate(
    points: np.ndarray, _boundary: Polygon | None = None, bsig: str = ""
) -> tuple[np.ndarray, np.ndarray, bool]:
    """
    Perform 2D Delaunay triangulation and optionally clip to boundary.

    Returns
    -------
    points : original points array (N, 3)
    simplices : triangle index array (M, 3)
    clip_failed : True when the boundary removed every triangle (mesh unclipped)
    """
    tri = Delaunay(points[:, :2])
    simplices = tri.simplices
    clip_failed = False

    if _boundary is not None:
        # One vectorised point-in-polygon test; the per-triangle Python loop
        # it replaces took minutes on a half-million-triangle mesh.
        c = points[simplices, :2].mean(axis=1)
        inside = shapely.contains_xy(_boundary, c[:, 0], c[:, 1])
        if inside.any():
            simplices = simplices[inside]
        else:
            clip_failed = True

    return points, simplices, clip_failed


def build_3d_figure(
    points: np.ndarray,
    simplices: np.ndarray,
    colorscale="earth",
    show_wireframe: bool = True,
    contour_interval: float | None = None,
    z_exaggeration: float = 1.0,
    base_depth: float | None = None,
    plinth: float | None = None,
    sections: list[dict] | None = None,
    camera: dict | None = None,
) -> go.Figure:
    """Render 3D terrain mesh with optional wireframe and contours."""
    x, y, z = points[:, 0], points[:, 1], points[:, 2] * z_exaggeration
    i, j, k = simplices[:, 0], simplices[:, 1], simplices[:, 2]

    fig = go.Figure()

    # Main mesh
    fig.add_trace(
        go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            intensity=points[:, 2],  # color by real Z, not exaggerated
            colorscale=colorscale,
            colorbar=dict(
                title=dict(text=f"RL ({u1()})", font=dict(size=12)),
                thickness=18,
                len=0.6,
                tickfont=dict(size=10),
            ),
            opacity=1.0,
            flatshading=False,
            lighting=dict(ambient=0.55, diffuse=0.8, specular=0.15, roughness=0.7, fresnel=0.1),
            lightposition=dict(x=1000, y=1000, z=2000),
            name="Terrain",
            hovertemplate="X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{customdata:.3f}<extra></extra>",
            customdata=points[:, 2],
        )
    )

    z_lo, z_hi = float(points[:, 2].min()), float(points[:, 2].max())

    # Solid base (side walls + floor) so the terrain reads as a block of land
    if base_depth is not None and base_depth > 0:
        base = build_base_solid(points, simplices, z_lo - base_depth, z_exaggeration)
        if base is not None:
            fig.add_trace(base)

    # Plinth plane + cut/fill line (where the ground meets the plane)
    if plinth is not None:
        x0, x1 = float(points[:, 0].min()), float(points[:, 0].max())
        y0, y1 = float(points[:, 1].min()), float(points[:, 1].max())
        pz = plinth * z_exaggeration
        fig.add_trace(
            go.Mesh3d(
                x=[x0, x1, x1, x0], y=[y0, y0, y1, y1], z=[pz] * 4,
                i=[0, 0], j=[1, 2], k=[2, 3],
                color="#38bdf8", opacity=0.35, flatshading=True,
                name=f"Plinth {plinth:.3f}",
                hovertemplate=f"Plinth level: {plinth:.3f}<extra></extra>",
                showlegend=True,
            )
        )
        for tr in _compute_contour_lines(
            points, simplices, np.array([plinth]), z_exaggeration, color="#ef4444", width=5
        ):
            tr.name, tr.showlegend = "Cut/Fill line", True
            fig.add_trace(tr)

    # Section lines draped on the terrain
    for idx, sec in enumerate(sections or []):
        spath = section_path(sec)
        ch, sx, sy, sz = sample_path(points, simplices, spath, n=300)
        lift = 0.01 * max(z_hi - z_lo, 1e-6) * z_exaggeration
        fig.add_trace(
            go.Scatter3d(
                x=sx, y=sy, z=sz * z_exaggeration + lift,
                mode="lines",
                line=dict(color="#22d3ee", width=6),
                name=sec["name"], hoverinfo="name",
            )
        )
        for lbl, (px, py) in ((f"{sec['name']}", spath[0]), (f"{sec['name']}'", spath[-1])):
            j = int(np.nanargmin(np.abs(sx - px) + np.abs(sy - py)))
            if not np.isnan(sz[j]):
                fig.add_trace(
                    go.Scatter3d(
                        x=[px], y=[py], z=[sz[j] * z_exaggeration + lift],
                        mode="markers+text", text=[lbl], textposition="top center",
                        marker=dict(size=5, color="#22d3ee"),
                        textfont=dict(color="#22d3ee", size=13),
                        showlegend=False, hoverinfo="skip",
                    )
                )

    # Wireframe overlay. Each triangle contributes 3 segments = 9 vertices, so
    # a dense mesh would ship millions of coordinates; skipped past the budget.
    if show_wireframe and len(simplices) <= MAX_WIREFRAME_TRIS:
        a = simplices[:, [0, 1, 2]].ravel()
        b = simplices[:, [1, 2, 0]].ravel()
        gap = np.full(a.size, np.nan)
        fig.add_trace(
            go.Scatter3d(
                x=np.column_stack([x[a], x[b], gap]).ravel(),
                y=np.column_stack([y[a], y[b], gap]).ravel(),
                z=np.column_stack([z[a], z[b], gap]).ravel(),
                mode="lines",
                line=dict(color="rgba(255,255,255,0.15)", width=1),
                name="Wireframe",
                hoverinfo="skip",
                showlegend=True,
            )
        )

    # Contour lines
    if contour_interval and contour_interval > 0:
        z_min, z_max = points[:, 2].min(), points[:, 2].max()
        levels = np.arange(
            np.floor(z_min / contour_interval) * contour_interval,
            z_max + contour_interval,
            contour_interval,
        )
        contour_traces = _compute_contour_lines(points, simplices, levels, z_exaggeration)
        for trace in contour_traces:
            fig.add_trace(trace)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        scene=dict(
            xaxis=dict(
                title=f"X ({u1()})",
                backgroundcolor="#0f172a",
                gridcolor="#1e293b",
                showbackground=True,
            ),
            yaxis=dict(
                title=f"Y ({u1()})",
                backgroundcolor="#0f172a",
                gridcolor="#1e293b",
                showbackground=True,
            ),
            zaxis=dict(
                title=f"Z ({u1()})",
                backgroundcolor="#0f172a",
                gridcolor="#1e293b",
                showbackground=True,
            ),
            aspectmode="data",
            dragmode="orbit",
            camera=camera or CAMERAS["Isometric"],
        ),
        uirevision=f"cam-{st.session_state.get('cam_rev', 0)}",  # keep camera across reruns
        margin=dict(l=0, r=0, t=30, b=0),
        height=660,
        legend=dict(
            bgcolor="rgba(15,23,42,0.8)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(size=11),
        ),
    )
    return fig


def _compute_contour_lines(
    points: np.ndarray,
    simplices: np.ndarray,
    levels: np.ndarray,
    z_exag: float,
    color: str = "#facc15",
    width: int = 2,
    max_segments: int = MAX_CONTOUR_SEGMENTS,
) -> list:
    """
    Compute horizontal contour slices through the triangulated surface.

    Marching triangles, vectorised over every triangle at once. The previous
    per-triangle Python loop ran `levels × len(simplices)` times — on a
    577 000-triangle mesh at 0.5 m intervals that is ~23 million iterations and
    takes minutes. All levels are returned as a single trace (segments
    separated by NaN) because one Plotly trace per contour level also costs the
    browser dearly.
    """
    tx = points[simplices, 0]
    ty = points[simplices, 1]
    tz = points[simplices, 2]
    # Triangle edges, as (from, to) vertex slots.
    EA = np.array([0, 1, 2])
    EB = np.array([1, 2, 0])

    xs, ys, zs, lv = [], [], [], []
    total = 0
    for level in np.atleast_1d(np.asarray(levels, dtype=float)):
        d = tz - level
        # Nudge off any vertex sitting exactly on the plane, so each crossed
        # triangle has a clean two-edge intersection instead of a degenerate one.
        if np.any(np.abs(d) < 1e-12):
            d = tz - (level + 1e-9 * max(abs(level), 1.0))

        da, db = d[:, EA], d[:, EB]
        cross = (da * db) < 0
        sel = np.flatnonzero(cross.sum(axis=1) == 2)
        if sel.size == 0:
            continue
        if total + sel.size > max_segments:
            sel = sel[: max(max_segments - total, 0)]
            if sel.size == 0:
                break

        # The two crossing edges of each selected triangle.
        edges = np.argsort(~cross[sel], axis=1, kind="stable")[:, :2]

        def cut(edge_col):
            a, b = EA[edge_col], EB[edge_col]
            r = np.arange(sel.size)
            za, zb = d[sel, a], d[sel, b]
            t = za / (za - zb)
            return (
                tx[sel, a] + t * (tx[sel, b] - tx[sel, a]),
                ty[sel, a] + t * (ty[sel, b] - ty[sel, a]),
            )

        x0, y0 = cut(edges[:, 0])
        x1, y1 = cut(edges[:, 1])
        gap = np.full(sel.size, np.nan)
        xs.append(np.column_stack([x0, x1, gap]).ravel())
        ys.append(np.column_stack([y0, y1, gap]).ravel())
        zs.append(np.full(sel.size * 3, level * z_exag))
        lv.append(np.full(sel.size * 3, level))
        total += sel.size
        if total >= max_segments:
            break

    if not xs:
        return []
    return [
        go.Scatter3d(
            x=np.concatenate(xs),
            y=np.concatenate(ys),
            z=np.concatenate(zs),
            customdata=np.concatenate(lv),
            mode="lines",
            line=dict(color=color, width=width),
            name="Contours",
            hovertemplate="Contour: %{customdata:.2f}<extra></extra>",
            showlegend=False,
        )
    ]


# ──────────────────────────────────────────────────────────────────────
# Earthwork: plinth cut/fill, optimum level, sections
# ──────────────────────────────────────────────────────────────────────
def _tri_stats(points: np.ndarray, simplices: np.ndarray):
    """Per-triangle plan area and vertex elevations."""
    P = points[simplices]  # (M, 3, 3)
    e1 = P[:, 1, :2] - P[:, 0, :2]
    e2 = P[:, 2, :2] - P[:, 0, :2]
    area = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    return area, P[:, :, 2]


@st.cache_data(show_spinner=False, max_entries=4)
def tri_cache(points: np.ndarray, simplices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-triangle plan area and *sorted* vertex elevations.

    All the volume maths needs the vertex elevations in ascending order. Sorting
    half a million triangles costs ~100 ms, and the insights tab alone asks for
    it 60+ times per rerun, so it is computed once and cached.
    """
    area, z = _tri_stats(points, simplices)
    return area, np.sort(z, axis=1)


def earthwork_core(area: np.ndarray, zs: np.ndarray, level: float) -> dict:
    """Cut/fill volumes from pre-sorted per-triangle elevations (see `earthwork`)."""
    d = zs - level
    d0, d1, d2 = d[:, 0], d[:, 1], d[:, 2]
    s = d.sum(axis=1)
    vol_pos = np.zeros(len(area))
    vol_neg = np.zeros(len(area))

    all_pos = d0 >= 0
    all_neg = d2 <= 0
    one_neg = (~all_pos) & (~all_neg) & (d1 >= 0)   # d0 < 0 <= d1
    one_pos = (~all_pos) & (~all_neg) & (d1 < 0)    # d1 < 0 < d2

    vol_pos[all_pos] = area[all_pos] * s[all_pos] / 3
    vol_neg[all_neg] = -area[all_neg] * s[all_neg] / 3

    m = one_neg
    vol_neg[m] = area[m] * (-d0[m]) ** 3 / (3 * (d1[m] - d0[m]) * (d2[m] - d0[m]))
    vol_pos[m] = area[m] * s[m] / 3 + vol_neg[m]

    m = one_pos
    vol_pos[m] = area[m] * d2[m] ** 3 / (3 * (d2[m] - d0[m]) * (d2[m] - d1[m]))
    vol_neg[m] = vol_pos[m] - area[m] * s[m] / 3

    cut, fill = float(vol_pos.sum()), float(vol_neg.sum())
    return {"cut": cut, "fill": fill, "net": cut - fill, "total": cut + fill,
            "area": float(area.sum())}


def earthwork(points: np.ndarray, simplices: np.ndarray, level: float) -> dict:
    """
    Exact cut/fill volumes between the TIN surface and a horizontal plinth plane.

    cut  = volume of ground ABOVE the plane (to be excavated)
    fill = volume of ground BELOW the plane (to be filled)
    Each triangle is linear, so the volume of the positive / negative part is
    closed-form (pyramid on the sub-triangle where the surface crosses the plane).
    """
    area, zs = tri_cache(points, simplices)
    return earthwork_core(area, zs, level)


def _area_above(area: np.ndarray, zs: np.ndarray, level: float) -> float:
    """Plan area of the surface above `level`, from pre-sorted vertex elevations."""
    d = zs - level
    d0, d1, d2 = d[:, 0], d[:, 1], d[:, 2]
    out = np.zeros(len(area))
    all_pos = d0 >= 0
    one_neg = (d0 < 0) & (d1 >= 0) & (d2 > 0)
    one_pos = (d1 < 0) & (d2 > 0)
    out[all_pos] = area[all_pos]
    m = one_neg
    out[m] = area[m] * (1 - d0[m] ** 2 / ((d1[m] - d0[m]) * (d2[m] - d0[m])))
    m = one_pos
    out[m] = area[m] * d2[m] ** 2 / ((d2[m] - d0[m]) * (d2[m] - d1[m]))
    return float(out.sum())


@st.cache_data(show_spinner=False, max_entries=4)
def optimal_plinth(points: np.ndarray, simplices: np.ndarray) -> dict:
    """
    Two recommended plinth levels:
      balanced : cut == fill (net = 0). cut-fill is linear in the level, so this is
                 the area-weighted mean ground elevation (exact).
      minimum  : minimum cut+fill (least earth moved). Found where half of the plan
                 area is above the plane (area-weighted median), by bisection.
    """
    area, zs = tri_cache(points, simplices)
    total_area = area.sum()
    balanced = float((area * zs.mean(axis=1)).sum() / total_area)

    lo, hi = float(zs.min()), float(zs.max())
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if _area_above(area, zs, mid) > total_area / 2:
            lo = mid
        else:
            hi = mid
    return {"balanced": balanced, "minimum": 0.5 * (lo + hi)}


def _key(simplices: np.ndarray, n: int) -> np.ndarray:
    s = np.sort(simplices, axis=1).astype(np.int64)
    return (s[:, 0] * n + s[:, 1]) * n + s[:, 2]


@st.cache_resource(show_spinner=False, max_entries=2)
def _tin_index(_points: np.ndarray, _simplices: np.ndarray, sig: str):
    """Delaunay search structure plus a mask of which of its triangles were kept.

    Cached because building it costs seconds on a large point set, and a single
    multi-segment section profile used to rebuild it once per segment.
    """
    tri = Delaunay(_points[:, :2])
    kept = np.isin(
        _key(tri.simplices, len(_points)), _key(_simplices, len(_points))
    )
    return tri, kept


def surface_z(points: np.ndarray, simplices: np.ndarray, xy: np.ndarray) -> np.ndarray:
    """Interpolate the TIN elevation at xy (N, 2); NaN outside the (clipped) mesh."""
    tri, kept = _tin_index(points, simplices, mesh_sig(points, simplices))
    sid = tri.find_simplex(xy)
    z = np.full(len(xy), np.nan)
    ok = sid >= 0
    if ok.any():
        ok &= kept[np.where(sid >= 0, sid, 0)]
    if ok.any():
        T = tri.transform[sid[ok]]
        bary2 = np.einsum("ijk,ik->ij", T[:, :2, :], xy[ok] - T[:, 2, :])
        bary = np.c_[bary2, 1 - bary2.sum(axis=1)]
        z[ok] = (bary * points[tri.simplices[sid[ok]], 2]).sum(axis=1)
    return z


def sample_profile(
    points: np.ndarray,
    simplices: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    n: int = 600,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Sample the terrain along a straight line.
    Returns (chainage, x, y, z); z is NaN outside the (clipped) mesh.
    """
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    t = np.linspace(0, 1, n)
    xy = p0[None, :] + t[:, None] * (p1 - p0)[None, :]
    ch = t * float(np.hypot(*(p1 - p0)))

    z = surface_z(points, simplices, xy)
    return ch, xy[:, 0], xy[:, 1], z


def section_path(sec: dict) -> list[tuple[float, float]]:
    """Vertices of a section: a polyline if it has one, else the straight p0-p1 line."""
    return [tuple(p) for p in (sec.get("path") or [sec["p0"], sec["p1"]])]


def sample_path(
    points: np.ndarray,
    simplices: np.ndarray,
    path: list[tuple[float, float]],
    n: int = 600,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sample the terrain along a polyline; chainage runs continuously through the vertices."""
    if len(path) == 2:
        return sample_profile(points, simplices, path[0], path[1], n)
    lens = [float(np.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(path[:-1], path[1:])]
    total = sum(lens) or 1.0
    chs, xs, ys, zs, acc = [], [], [], [], 0.0
    for i, (a, b, L) in enumerate(zip(path[:-1], path[1:], lens)):
        if L == 0:
            continue
        ch, x, y, z = sample_profile(points, simplices, a, b, max(3, int(round(n * L / total))))
        sl = slice(1, None) if chs else slice(0, None)      # drop the duplicated vertex sample
        chs.append(ch[sl] + acc); xs.append(x[sl]); ys.append(y[sl]); zs.append(z[sl])
        acc += L
    return np.concatenate(chs), np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)


def section_areas(ch: np.ndarray, z: np.ndarray, level: float) -> tuple[float, float]:
    """Cut / fill cross-section areas of a profile against the plinth level."""
    d = z - level
    d0, d1 = d[:-1], d[1:]
    ds = np.diff(ch)
    valid = ~(np.isnan(d0) | np.isnan(d1))

    def part(a, b):
        both = (a >= 0) & (b >= 0)
        cross = (a * b < 0)
        out = np.where(both, ds * (a + b) / 2, 0.0)
        out = np.where(cross, ds * np.maximum(a, b) ** 2 / (2 * np.abs(a - b) + 1e-300), out)
        return np.where(valid, out, 0.0).sum()

    return float(part(d0, d1)), float(part(-d0, -d1))


def build_base_solid(
    points: np.ndarray, simplices: np.ndarray, base_z: float, z_exag: float
) -> go.Mesh3d | None:
    """Side walls + bottom face under the terrain so it reads as a block of ground."""
    # Boundary edges are those belonging to exactly one triangle. Found with
    # np.unique rather than a Python dict, which took ~1.7 M operations per
    # render on a half-million-triangle mesh.
    e = np.sort(
        np.column_stack(
            [simplices[:, [0, 1, 2]].ravel(), simplices[:, [1, 2, 0]].ravel()]
        ),
        axis=1,
    )
    uniq, counts = np.unique(e, axis=0, return_counts=True)
    boundary_edges = uniq[counts == 1]
    if len(boundary_edges) == 0:
        return None

    n = len(points)
    top = np.c_[points[:, 0], points[:, 1], points[:, 2] * z_exag]
    bot = np.c_[points[:, 0], points[:, 1], np.full(n, base_z * z_exag)]
    verts = np.vstack([top, bot])
    ba, bb = boundary_edges[:, 0], boundary_edges[:, 1]
    f = np.vstack(
        [
            np.column_stack([ba, bb, bb + n]),          # wall, lower triangle
            np.column_stack([ba, bb + n, ba + n]),      # wall, upper triangle
            simplices + n,                               # bottom face
        ]
    )
    return go.Mesh3d(
        x=verts[:, 0], y=verts[:, 1], z=verts[:, 2],
        i=f[:, 0], j=f[:, 1], k=f[:, 2],
        color="#8b6f4e", opacity=1.0, flatshading=True,
        lighting=dict(ambient=0.55, diffuse=0.6, specular=0.05),
        name="Ground block", hoverinfo="skip", showlegend=True,
    )


# ──────────────────────────────────────────────────────────────────────
# Export helpers
# ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, max_entries=2)
def export_obj(points: np.ndarray, simplices: np.ndarray) -> str:
    """Export mesh as Wavefront .OBJ string."""
    buf = io.StringIO()
    buf.write("# DXF-to-3D Terrain Export\n")
    buf.write(f"# {len(points)} vertices, {len(simplices)} faces\n\n")
    np.savetxt(buf, points, fmt="v %.6f %.6f %.6f")
    buf.write("\n")
    np.savetxt(buf, simplices + 1, fmt="f %d %d %d")
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=2)
def export_dxf_3dface(points: np.ndarray, simplices: np.ndarray) -> bytes:
    """Export mesh as a DXF with 3DFACE entities."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for s in simplices:
        p0, p1, p2 = points[s[0]], points[s[1]], points[s[2]]
        msp.add_3dface(
            [
                (p0[0], p0[1], p0[2]),
                (p1[0], p1[1], p1[2]),
                (p2[0], p2[1], p2[2]),
                (p2[0], p2[1], p2[2]),  # 4th point = 3rd (triangle)
            ]
        )
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


# ══════════════════════════════════════════════════════════════════════
# Main Application
# ══════════════════════════════════════════════════════════════════════
def main():
    # ── Sidebar Header ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🏔️ DXF → 3D Terrain")
        st.caption("Convert 2D survey DXF into interactive 3D surfaces")
        st.divider()

    # ── File Upload ──────────────────────────────────────────────────
    uploaded = st.sidebar.file_uploader(
        "📂 Upload DXF File",
        type=["dxf"],
        help="Drag & drop or browse for a .dxf survey file",
    )

    if uploaded is None:
        _show_landing()
        return

    # ── Parse DXF ────────────────────────────────────────────────────
    # getvalue(), not read(): the uploader's buffer position survives reruns,
    # so read() returns b"" the second time round.
    file_bytes = uploaded.getvalue()
    sig = file_sig(file_bytes)
    with st.spinner("Parsing DXF…"):
        doc = parse_dxf(file_bytes, sig)

    layers, entity_summary = scan_dxf(doc, sig)
    total_entities = sum(entity_summary.values())

    # ── Overview Metrics ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 📊 DXF Overview")
        st.metric("Total Entities", f"{total_entities:,}")
        with st.expander("Entity Breakdown", expanded=False):
            for etype, count in sorted(entity_summary.items(), key=lambda x: -x[1]):
                st.markdown(f"- **{etype}**: {count:,}")
        st.divider()

    # ── Layer Selection ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        level_layer = st.selectbox(
            "📏 Elevation Text Layer",
            layers,
            help="Layer containing TEXT/MTEXT with elevation values",
        )
        UNITS["u"] = st.selectbox(
            "📐 Drawing units", ["m", "ft"],
            help="Unit of the DXF coordinates and elevations. Areas and volumes are labelled accordingly.",
        )
        use_boundary = st.checkbox("✂️ Clip to boundary polygon", value=False)
        boundary_layer = None
        if use_boundary:
            boundary_layer = st.selectbox(
                "🔲 Boundary Layer",
                layers,
                help="Layer with LWPOLYLINE/POLYLINE defining site perimeter",
            )
        max_pts = st.select_slider(
            "🎚️ Surface detail (max points)",
            options=[5_000, 10_000, 25_000, 50_000, 100_000, 0],
            value=MAX_SURFACE_POINTS,
            format_func=lambda v: "No limit (slow)" if v == 0 else f"{v:,}",
            help="Dense spot-level grids are thinned to this many points before "
                 "triangulating. Higher = more detail but much slower, and very "
                 "large meshes can freeze the browser. Volumes change slightly "
                 "with the thinning; use 'No limit' for a final quantity take-off.",
        )
        st.divider()

    # ── Extract Data ─────────────────────────────────────────────────
    all_points, labels, warnings = extract_elevation_points(doc, level_layer, sig)
    boundary = extract_boundary(doc, boundary_layer, sig) if boundary_layer else None

    elev_points = decimate_points(all_points, max_pts)
    thinned = len(elev_points) < len(all_points)

    if use_boundary and boundary_layer and boundary is None:
        st.sidebar.warning(f"No valid polyline found on layer '{boundary_layer}'.")

    # ── Stats ────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 📈 Site Statistics")
        if len(elev_points) > 0:
            z_vals = elev_points[:, 2]
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Min RL ({u1()})", f"{z_vals.min():.2f}")
            c2.metric(f"Max RL ({u1()})", f"{z_vals.max():.2f}")
            c3.metric(f"Relief ({u1()})", f"{z_vals.max() - z_vals.min():.2f}")
            st.metric(
                "Points Found",
                f"{len(elev_points):,}",
                f"thinned from {len(all_points):,}" if thinned else None,
                delta_color="off",
            )
            if thinned:
                st.caption(
                    f"⚡ {len(all_points):,} spot levels found; using {len(elev_points):,} "
                    "on an even grid to keep the viewer responsive. Raise **Surface "
                    "detail** above for finer results."
                )
        else:
            st.warning("No elevation points extracted.")
        st.divider()

    # ── Warnings ─────────────────────────────────────────────────────
    if warnings:
        with st.sidebar.expander(f"⚠️ Warnings ({len(warnings)})", expanded=False):
            for w in warnings:
                st.caption(w)

    # ── Shared surface mesh ──────────────────────────────────────────
    has_surface = len(elev_points) >= 3
    pts = simplices = None
    plinth = None
    base_depth = None
    mode = "Off"
    opt = None
    if has_surface:
        with st.spinner("Triangulating…"):
            bsig = boundary.wkb_hex[:64] if boundary is not None else ""
            pts, simplices, clip_failed = triangulate(elev_points, boundary, bsig)
        if clip_failed:
            st.warning("All triangles were clipped by the boundary. Showing unclipped mesh.")
        st.sidebar.metric("Triangles", f"{len(simplices):,}")

        relief = float(pts[:, 2].max() - pts[:, 2].min())
        opt = optimal_plinth(pts, simplices)
        with st.sidebar:
            st.markdown("### 🏗️ Plinth & Ground Block")
            show_base = st.checkbox("Show ground block (base offset)", value=True)
            if show_base:
                base_depth = st.number_input(
                    f"Depth below lowest point ({u1()})",
                    min_value=0.1,
                    value=max(round(relief * 0.5, 1), 1.0),
                    step=0.5,
                    help="Base of the solid block is this far below the lowest ground level.",
                )
            mode = st.radio(
                "Plinth plane",
                ["Off", "Manual level", "Balanced (cut = fill)", "Least earthwork (min cut+fill)"],
                index=2,
            )
            if mode == "Manual level":
                plinth = st.number_input(
                    f"Plinth level RL ({u1()})", value=round(opt["balanced"], 3), step=0.05, format="%.3f"
                )
            elif mode.startswith("Balanced"):
                plinth = opt["balanced"]
            elif mode.startswith("Least"):
                plinth = opt["minimum"]

            if plinth is not None:
                ew = earthwork(pts, simplices, plinth)
                st.metric(f"Plinth RL ({u1()})", f"{plinth:.3f}")
                st.caption(
                    f"Cut {ew['cut']:,.1f} {u3()} · Fill {ew['fill']:,.1f} {u3()}  \n"
                    "Full breakdown in the **Cut & Fill Insights** tab."
                )
            st.divider()

        if "sections" not in st.session_state:
            st.session_state.sections = []

    # ── Main Content Tabs ────────────────────────────────────────────
    tab_2d, tab_3d, tab_ins, tab_export = st.tabs(
        ["📐 2D Preview", "🏔️ 3D Terrain & Sections", "📊 Cut & Fill Insights", "💾 Export"]
    )

    # ── 2D Preview Tab ───────────────────────────────────────────────
    with tab_2d:
        st.markdown("#### 2D DXF Preview")
        st.caption("Elevation points are highlighted. Hover for details.")
        # Streamlit executes the body of every tab on every rerun, visible or
        # not. For a drawing with ~300 000 entities the preview costs more than
        # everything else combined, so it is drawn on request.
        heavy = total_entities > 50_000
        if heavy:
            st.info(
                f"This drawing has {total_entities:,} entities. The full 2D preview is "
                "the slowest view, so it is off by default."
            )
        if st.checkbox("Show 2D preview", value=not heavy, key="show_2d"):
            with_texts = st.checkbox(
                "Include all text markers",
                value=not heavy,
                key="prev_texts",
                help="Positions of every TEXT/MTEXT entity in the drawing.",
            )
            with st.spinner("Building 2D preview…"):
                entities_2d = extract_all_entities_2d(doc, sig, with_texts)
                fig_2d = build_2d_preview(entities_2d, elev_points, boundary)
            if entities_2d.get("truncated"):
                st.caption(
                    "⚡ Background geometry truncated for speed — the elevation points "
                    "and boundary are complete."
                )
            st.plotly_chart(fig_2d, use_container_width=True, key="preview_2d")

    # ── 3D Terrain Tab ───────────────────────────────────────────────
    with tab_3d:
        if not has_surface:
            st.error(
                "Need at least 3 elevation points to generate a surface. "
                "Check the selected layer or elevation text format."
            )
        else:
            col_t, col_a, col_b, col_c, col_d, col_e = st.columns([1.15, 1.1, 0.9, 0.9, 0.9, 1.1])
            with col_t:
                cutter_on = st.toggle(
                    "✂️ Section Cutter", key="cutter_on",
                    help="Inspect the model with a draggable cutting plane. A visual tool, separate from the "
                         "section lines further down.",
                )
                show_secs = st.checkbox("Show sections", value=True, disabled=cutter_on)
            with col_a:
                colorscale = COLORSCALES[st.selectbox("Colorscale", list(COLORSCALES), index=0, disabled=cutter_on)]
            with col_b:
                contour_interval = st.number_input(
                    f"Contour ({u1()})", min_value=0.0, value=0.5, step=0.1, format="%.2f",
                    help="Contour interval. Set to 0 to disable contour lines", disabled=cutter_on,
                )
            with col_c:
                z_exag = st.number_input(
                    "Z exag. (×)", min_value=0.1, max_value=50.0, value=1.0, step=0.5, format="%.1f"
                )
            with col_d:
                wire_ok = len(simplices) <= MAX_WIREFRAME_TRIS
                show_wire = st.checkbox(
                    "Wireframe", value=False, disabled=cutter_on or not wire_ok,
                    help="Wireframe" if wire_ok else
                         f"Unavailable above {MAX_WIREFRAME_TRIS:,} triangles "
                         f"(this mesh has {len(simplices):,}) — lower Surface detail "
                         "in the sidebar to enable it.",
                )
            with col_e:
                view = st.selectbox(
                    "Camera view", list(CAMERAS), key="cam_view", disabled=cutter_on,
                    on_change=lambda: st.session_state.update(
                        cam_rev=st.session_state.get("cam_rev", 0) + 1
                    ),
                    help="Drag = orbit · Shift+drag / right-drag = pan · Scroll = zoom · Double-click = reset",
                )

            if cutter_on:
                z_lo_all = float(pts[:, 2].min())
                section_cutter(
                    pts=np.round(pts, 4).tolist(),
                    tris=simplices.tolist(),
                    zmin=z_lo_all, zmax=float(pts[:, 2].max()),
                    floor=z_lo_all - (base_depth if base_depth else max(relief * 0.3, 0.5)),
                    plinth=plinth, unit=u1(), zexag=float(z_exag), height=680,
                    sig=f"{len(pts)}-{len(simplices)}-{pts[:, 0].sum():.3f}-{pts[:, 2].sum():.3f}-{z_exag}-{base_depth}-{plinth}",
                    key="cutter_view", default=None,
                )
            else:
                fig_3d = build_3d_figure(
                    pts, simplices,
                    colorscale=colorscale,
                    show_wireframe=show_wire,
                    contour_interval=contour_interval if contour_interval > 0 else None,
                    z_exaggeration=z_exag,
                    base_depth=base_depth,
                    plinth=plinth,
                    sections=st.session_state.sections if show_secs else None,
                    camera=CAMERAS[view],
                )
                st.plotly_chart(fig_3d, use_container_width=True, key="terrain_3d", config=PLOT_CONFIG)

            st.divider()
            _sections_tab(pts, simplices, plinth, base_depth)

    # ── Insights Tab ─────────────────────────────────────────────────
    with tab_ins:
        if not has_surface:
            st.info("Need a surface (≥ 3 elevation points).")
        else:
            _insights_tab(pts, simplices, plinth, mode, opt)

    # ── Export Tab ───────────────────────────────────────────────────
    with tab_export:
        if not has_surface:
            st.info("Generate a terrain first (need ≥ 3 elevation points).")
            return

        st.markdown("#### Export 3D Mesh")
        st.caption("Download the triangulated terrain in your preferred format.")

        st.caption(f"Mesh: {len(pts):,} vertices · {len(simplices):,} triangles")

        # Both exports are built on demand. Generating them eagerly meant every
        # widget change anywhere in the app rebuilt a full 3DFACE DXF — minutes
        # of work for a mesh this size, on a tab the user may never open.
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📦 Wavefront OBJ")
            st.caption("Compatible with Blender, SketchUp, Rhino, and most 3D software.")
            if st.button("Prepare .OBJ", use_container_width=True, key="prep_obj"):
                with st.spinner("Building OBJ…"):
                    st.session_state.obj_data = export_obj(pts, simplices)
            if st.session_state.get("obj_data"):
                st.download_button(
                    "⬇️ Download .OBJ",
                    data=st.session_state.obj_data,
                    file_name="terrain_mesh.obj",
                    mime="text/plain",
                    use_container_width=True,
                )

        with col2:
            st.markdown("##### 📐 AutoCAD DXF (3DFACE)")
            st.caption("Import directly into AutoCAD, Civil 3D, or BricsCAD.")
            if st.button("Prepare .DXF", use_container_width=True, key="prep_dxf"):
                with st.spinner("Building DXF — this can take a while for a large mesh…"):
                    st.session_state.dxf_data = export_dxf_3dface(pts, simplices)
            if st.session_state.get("dxf_data"):
                st.download_button(
                    "⬇️ Download .DXF",
                    data=st.session_state.dxf_data,
                    file_name="terrain_mesh.dxf",
                    mime="application/octet-stream",
                    use_container_width=True,
                )


def _insights_tab(pts, simplices, plinth, mode, opt):
    """Dedicated cut & fill report for the selected plinth."""
    area, zs = tri_cache(pts, simplices)
    total_area = float(area.sum())
    z_lo, z_hi = float(pts[:, 2].min()), float(pts[:, 2].max())

    st.markdown("#### 📊 Cut & Fill Insights")
    if plinth is None:
        st.info("Choose a plinth option in the sidebar (Manual, Balanced or Least earthwork) to see the report.")
        return

    ew = earthwork_core(area, zs, plinth)
    a_cut = _area_above(area, zs, plinth)
    a_fill = total_area - a_cut
    st.caption(f"Plinth mode: **{mode}** · Plinth level: **RL {plinth:.3f} {u1()}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Cut ({u3()})", f"{ew['cut']:,.1f}", help="Ground above the plinth – excavate")
    c2.metric(f"Fill ({u3()})", f"{ew['fill']:,.1f}", help="Ground below the plinth – backfill")
    c3.metric(f"Net cut−fill ({u3()})", f"{ew['net']:+,.1f}")
    c4.metric(f"Total moved ({u3()})", f"{ew['total']:,.1f}")

    if abs(ew["net"]) < 0.005 * max(ew["total"], 1e-9):
        st.success("Cut and fill are balanced – no material to import or export (bank volumes).")
    elif ew["net"] > 0:
        st.warning(f"**Surplus of {ew['net']:,.1f} {u3()}** – excess excavated soil must be carted away (or raise the plinth).")
    else:
        st.warning(f"**Deficit of {-ew['net']:,.1f} {u3()}** – borrow fill must be imported (or lower the plinth).")

    st.markdown("##### Extents")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric(f"Site plan area ({u2()})", f"{total_area:,.1f}")
    e2.metric(f"Area in cut ({u2()})", f"{a_cut:,.1f}", f"{100 * a_cut / total_area:.0f}% of site", delta_color="off")
    e3.metric(f"Area in fill ({u2()})", f"{a_fill:,.1f}", f"{100 * a_fill / total_area:.0f}% of site", delta_color="off")
    e4.metric(f"Mean depth ({u1()})", f"{ew['total'] / total_area:.3f}", help="Total moved ÷ site area")
    d1, d2 = st.columns(2)
    d1.metric(f"Deepest cut ({u1()})", f"{max(z_hi - plinth, 0):.3f}", help="Highest ground point minus plinth")
    d2.metric(f"Deepest fill ({u1()})", f"{max(plinth - z_lo, 0):.3f}", help="Plinth minus lowest ground point")

    st.markdown("##### Haulage estimate")
    h1, h2, h3 = st.columns(3)
    swell = h1.number_input("Swell / bulking (%)", 0.0, 100.0, 25.0, 5.0,
                            help="Loose volume increase when soil is excavated")
    shrink = h2.number_input("Compaction allowance (%)", 0.0, 50.0, 10.0, 5.0,
                             help="Extra loose fill needed to achieve the compacted fill volume")
    truck = h3.number_input(f"Truck capacity ({u3()})", 0.5, 100.0, 10.0, 0.5)
    loose_cut = ew["cut"] * (1 + swell / 100)
    fill_req = ew["fill"] * (1 + shrink / 100)
    export_loose = max(loose_cut - fill_req, 0.0)
    import_loose = max(fill_req - loose_cut, 0.0)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Loose cut ({u3()})", f"{loose_cut:,.1f}")
    k2.metric(f"Fill to place ({u3()})", f"{fill_req:,.1f}", help="Fill volume incl. compaction allowance")
    k3.metric(f"Cart away ({u3()})", f"{export_loose:,.1f}", f"{int(np.ceil(export_loose / truck))} loads", delta_color="off")
    k4.metric(f"Import ({u3()})", f"{import_loose:,.1f}", f"{int(np.ceil(import_loose / truck))} loads", delta_color="off")
    st.caption("Swell/compaction factors are planning assumptions – adjust to your soil report. "
               "The cut/fill figures above are bank (in-situ) volumes.")

    st.markdown("##### Earthwork vs plinth level")
    levels = np.linspace(z_lo, z_hi, 40)
    res = [earthwork_core(area, zs, lv) for lv in levels]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=levels, y=[r["cut"] for r in res], name="Cut", line=dict(color="#ef4444", width=3)))
    fig.add_trace(go.Scatter(x=levels, y=[r["fill"] for r in res], name="Fill", line=dict(color="#3b82f6", width=3)))
    fig.add_trace(go.Scatter(x=levels, y=[r["total"] for r in res], name="Cut + Fill",
                             line=dict(color="#a3a3a3", width=2, dash="dot")))
    for lbl, lv, col in (("Balanced", opt["balanced"], "#22c55e"), ("Least earthwork", opt["minimum"], "#f59e0b")):
        fig.add_vline(x=lv, line=dict(color=col, dash="dash"), annotation_text=lbl, annotation_position="top")
    fig.add_vline(x=plinth, line=dict(color="#38bdf8", width=3), annotation_text="Selected", annotation_position="bottom")
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", height=380,
        margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified",
        xaxis=dict(title=f"Plinth level RL ({u1()})"), yaxis=dict(title=f"Volume ({u3()})"),
    )
    st.plotly_chart(fig, use_container_width=True, key="ins_curve")

    st.markdown("##### Plinth level comparison")
    rows = [("Balanced (cut = fill)", opt["balanced"]), ("Least earthwork (min cut+fill)", opt["minimum"])]
    if mode == "Manual level":
        rows.insert(0, ("Your level", plinth))
    table = []
    for name, lv in rows:
        r = earthwork_core(area, zs, lv)
        table.append({
            "Option": name, f"RL ({u1()})": round(lv, 3),
            f"Cut ({u3()})": round(r["cut"], 1), f"Fill ({u3()})": round(r["fill"], 1),
            f"Net ({u3()})": round(r["net"], 1), f"Total moved ({u3()})": round(r["total"], 1),
        })
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.caption("Volumes are exact against the triangulated surface. Balanced = area-weighted mean ground level; "
               "Least earthwork = area-weighted median ground level.")


def _sections_tab(pts, simplices, plinth, base_depth=None):
    ss = st.session_state
    st.markdown("#### ✂️ Section cuts")
    st.caption(
        "**Drag with the left mouse button** on the plan to draw a section (**Shift** = horizontal/vertical). "
        "Use **Polyline** in the plan toolbar for multi-segment sections. Nothing is processed until you release "
        "(or finish the polyline). Right-drag pans, wheel zooms."
    )

    zr = pts[:, 2]
    drawn = section_canvas(
        pts=np.round(pts, 4).tolist(),
        tris=simplices.tolist(),
        sections=[{"name": sec["name"], "path": [list(q) for q in section_path(sec)]} for sec in ss.sections],
        zmin=float(zr.min()), zmax=float(zr.max()),
        unit=u1(), height=620,
        sig=f"{len(pts)}-{len(simplices)}-{pts[:, 0].sum():.3f}-{pts[:, 2].sum():.3f}",
        key="sec_canvas", default=None,
    )
    # the component keeps returning its last value on every rerun -> only act on a new drawing
    if drawn and drawn.get("id") != ss.get("last_draw_id"):
        ss.last_draw_id = drawn["id"]
        path = []
        for x, y in drawn["path"]:
            q = (round(float(x), 3), round(float(y), 3))
            if not path or q != path[-1]:
                path.append(q)
        if len(path) >= 2:
            ss.sections.append({"name": f"S{len(ss.sections) + 1}", "p0": path[0], "p1": path[-1], "path": path})
            st.rerun()

    if ss.sections and st.button("🗑️ Clear all sections"):
        ss.sections = []
        st.rerun()

    with st.expander("Enter section coordinates manually"):
        c = st.columns(5)
        ax = c[0].number_input("Start X", value=float(pts[:, 0].min()), format="%.3f")
        ay = c[1].number_input("Start Y", value=float(pts[:, 1].mean()), format="%.3f")
        bx = c[2].number_input("End X", value=float(pts[:, 0].max()), format="%.3f")
        by = c[3].number_input("End Y", value=float(pts[:, 1].mean()), format="%.3f")
        if c[4].button("Add section", use_container_width=True) and (ax, ay) != (bx, by):
            ss.sections.append({"name": f"S{len(ss.sections) + 1}", "p0": (ax, ay), "p1": (bx, by)})
            st.rerun()

    if not ss.sections:
        return

    # summary table
    rows = []
    for s in ss.sections:
        ch, _, _, zz = sample_path(pts, simplices, section_path(s))
        row = {"Section": f"{s['name']}–{s['name']}'", f"Length ({u1()})": round(float(ch[-1]), 2)}
        if plinth is not None:
            cut_a, fill_a = section_areas(ch, zz, plinth)
            row.update({f"Cut area ({u2()})": round(cut_a, 3), f"Fill area ({u2()})": round(fill_a, 3)})
        rows.append(row)
    st.dataframe(rows, hide_index=True, use_container_width=True)

    names = [s["name"] for s in ss.sections]
    c1, c2, c3 = st.columns([2, 1, 1])
    chosen = c1.selectbox("Show profile", names, index=len(names) - 1)
    vex = c2.number_input("Vertical exaggeration (×)", min_value=1.0, max_value=50.0, value=2.0, step=1.0)
    sec = ss.sections[names.index(chosen)]
    if c3.button(f"Delete {chosen}"):
        ss.sections.pop(names.index(chosen))
        for n, s in enumerate(ss.sections, 1):
            s["name"] = f"S{n}"
        st.rerun()

    ch, sx, sy, sz = sample_path(pts, simplices, section_path(sec))
    fig = go.Figure()
    if base_depth:
        floor = float(pts[:, 2].min()) - base_depth
        fig.add_trace(go.Scatter(x=[ch[0], ch[-1]], y=[floor, floor], mode="lines",
                                 line=dict(color="#8b6f4e", width=1), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ch, y=sz, mode="lines", line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(139,111,78,0.55)", name="Ground", hoverinfo="skip"))
    if plinth is not None:
        top = np.where(sz >= plinth, sz, plinth)
        bot = np.where(sz <= plinth, sz, plinth)
        line = np.where(np.isnan(sz), np.nan, plinth)
        fig.add_trace(go.Scatter(x=ch, y=line, mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ch, y=np.where(np.isnan(sz), np.nan, top), mode="lines",
                                 line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(239,68,68,0.45)", name="Cut"))
        fig.add_trace(go.Scatter(x=ch, y=line, mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ch, y=np.where(np.isnan(sz), np.nan, bot), mode="lines",
                                 line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(59,130,246,0.45)", name="Fill"))
        fig.add_trace(go.Scatter(x=ch, y=line, mode="lines",
                                 line=dict(color="#38bdf8", dash="dash", width=2),
                                 name=f"Plinth {plinth:.3f}"))
    fig.add_trace(go.Scatter(
        x=ch, y=sz, mode="lines", line=dict(color="#facc15", width=3), name="Ground",
        customdata=np.c_[sx, sy],
        hovertemplate="Ch %{x:.2f}<br>RL %{y:.3f}<br>X %{customdata[0]:.2f}, Y %{customdata[1]:.2f}<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", height=460,
        title=f"Section {chosen}–{chosen}'", margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(title=f"Chainage ({u1()})"), yaxis=dict(title=f"RL ({u1()})", scaleanchor="x", scaleratio=vex),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, key="profile_chart")

    if plinth is not None:
        cut_a, fill_a = section_areas(ch, sz, plinth)
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Cut area ({u2()})", f"{cut_a:,.3f}")
        m2.metric(f"Fill area ({u2()})", f"{fill_a:,.3f}")
        m3.metric(f"Net ({u2()})", f"{cut_a - fill_a:+,.3f}")

    lines = ["chainage,x,y,rl"]
    for a, b, c, d in zip(ch, sx, sy, sz):
        lines.append(f"{a:.4f},{b:.4f},{c:.4f}," + ("" if np.isnan(d) else f"{d:.4f}"))
    st.download_button("⬇️ Download profile CSV", "\n".join(lines),
                       file_name=f"section_{chosen}.csv", mime="text/csv")



def _show_landing():
    """Show a welcoming landing page when no file is uploaded."""
    st.markdown(
        """
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 80px 20px 40px;
            text-align: center;
        ">
            <div style="font-size: 4rem; margin-bottom: 16px;">🏔️</div>
            <h1 style="
                font-size: 2.4rem;
                font-weight: 800;
                background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 12px;
            ">DXF → 3D Terrain Viewer</h1>
            <p style="
                color: #94a3b8;
                font-size: 1.1rem;
                max-width: 520px;
                line-height: 1.7;
            ">
                Upload a landscape survey DXF file to extract elevation points,
                perform Delaunay triangulation, and visualise an interactive 3D
                terrain surface — right in your browser.
            </p>
            <div style="
                margin-top: 40px;
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 24px;
                max-width: 680px;
            ">
                <div style="
                    background: linear-gradient(135deg, #1e293b, #0f172a);
                    border: 1px solid #334155;
                    border-radius: 14px;
                    padding: 28px 20px;
                ">
                    <div style="font-size: 1.6rem; margin-bottom: 10px;">📐</div>
                    <div style="color: #e2e8f0; font-weight: 600; margin-bottom: 6px;">2D Preview</div>
                    <div style="color: #64748b; font-size: 0.85rem;">
                        Inspect DXF entities and verify extracted elevation points
                    </div>
                </div>
                <div style="
                    background: linear-gradient(135deg, #1e293b, #0f172a);
                    border: 1px solid #334155;
                    border-radius: 14px;
                    padding: 28px 20px;
                ">
                    <div style="font-size: 1.6rem; margin-bottom: 10px;">🗻</div>
                    <div style="color: #e2e8f0; font-weight: 600; margin-bottom: 6px;">3D Terrain</div>
                    <div style="color: #64748b; font-size: 0.85rem;">
                        Interactive mesh with contours, wireframe, and elevation heatmap
                    </div>
                </div>
                <div style="
                    background: linear-gradient(135deg, #1e293b, #0f172a);
                    border: 1px solid #334155;
                    border-radius: 14px;
                    padding: 28px 20px;
                ">
                    <div style="font-size: 1.6rem; margin-bottom: 10px;">💾</div>
                    <div style="color: #e2e8f0; font-weight: 600; margin-bottom: 6px;">Export</div>
                    <div style="color: #64748b; font-size: 0.85rem;">
                        Download as OBJ or 3D DXF for CAD workflows
                    </div>
                </div>
            </div>
            <div style="
                margin-top: 48px;
                padding: 16px 28px;
                background: rgba(56, 189, 248, 0.08);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 10px;
                color: #38bdf8;
                font-size: 0.92rem;
            ">
                👈 &nbsp;Upload a <b>.dxf</b> file in the sidebar to get started
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
