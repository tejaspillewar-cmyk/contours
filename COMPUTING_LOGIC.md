# 🧮 DXF → 3D Terrain — Computing Logic

> This document explains **how** the application transforms a flat 2D DXF survey drawing into an interactive 3D terrain surface. No code is shown — only the mathematical and algorithmic logic.

---

## Pipeline at a Glance

```
DXF File → Parse Entities → Extract (X, Y, Z) → Triangulate → Clip → Render → Export
```

Each stage is explained in detail below.

---

## Stage 1 — DXF Parsing & Entity Classification

### What is a DXF?

A DXF (Drawing Exchange Format) is a CAD file that stores geometric entities (lines, arcs, circles, text, polylines, etc.) organised into **layers**. Each entity has:
- A **type** (e.g., `LINE`, `TEXT`, `LWPOLYLINE`)
- A **layer name** (e.g., `LEVELS`, `BOUNDARY`, `GRID`)
- **Geometric properties** (coordinates, radius, text content, etc.)

### What the parser does

1. Opens the DXF binary and reads the **ModelSpace** — the primary 2D drawing area.
2. Iterates through every entity and collects:
   - All unique **layer names** (for the dropdown menus)
   - A **count by entity type** (for the overview)
3. No geometry is modified at this stage — it's purely an inspection pass.

---

## Stage 2 — Elevation Point Extraction

### Goal
Convert scattered text annotations in the DXF into a structured array of 3D coordinates: **(X, Y, Z)**.

### How it works

In a typical survey DXF, the surveyor places **TEXT** or **MTEXT** entities at spot locations. Each text entity has:
- An **insertion point** — the (X, Y) position where the text is anchored in drawing space
- A **text string** — the displayed value, which encodes the **elevation (Z)**

### Coordinate extraction
- The **(X, Y)** comes directly from the text entity's insertion point
- The **(Z)** is parsed from the text string using pattern matching

### Elevation parsing logic

The text string can appear in many formats across different survey conventions:

| Input Text | Parsed Z |
|-----------|----------|
| `12.45` | 12.45 |
| `+12.45` | +12.45 |
| `-3.20` | -3.20 |
| `12.45m` | 12.45 |
| `RL 104.2` | 104.2 |
| `EL: 98.76` | 98.76 |
| `LEVEL-12.5` | 12.5 |
| `FFL +3.500` | 3.500 |
| `TBM 100.000` | 100.000 |

The parser uses a **regular expression** that:
1. Optionally matches common prefixes: `RL`, `EL`, `ELEV`, `LEVEL`, `FL`, `FFL`, `SSL`, `NGL`, `TBM`
2. Skips any separator (spaces, colons, hyphens)
3. Captures the numeric value (with optional sign and decimals)
4. Ignores optional unit suffixes (`m`, `M`, `mtr`, `ft`)

### Edge case handling

| Scenario | Action |
|----------|--------|
| Text contains no numeric value (e.g., "BENCHMARK", "DATUM") | Skipped, logged as warning |
| Two texts at the same (X, Y) with **same** Z | Deduplicated (keep one) |
| Two texts at the same (X, Y) with **different** Z | Keep the first, warn the user |

### Result
An array of **N points**, each with three coordinates: **(X, Y, Z)**.

---

## Stage 3 — Delaunay Triangulation

### The problem
We have a **scattered point cloud** — N points at irregular positions. To create a continuous surface, we need to connect them into a **triangulated mesh** (a surface made of non-overlapping triangles).

### What is Delaunay Triangulation?

Delaunay triangulation is a method for connecting a set of points into triangles such that:

> **No point lies inside the circumcircle of any triangle.**

This property produces triangles that are as close to equilateral as possible, avoiding long, thin "sliver" triangles that distort the surface.

### How it's applied

```
Input:  N points with (X, Y, Z)
        ↓
Step 1: Project to 2D — use only (X, Y) for triangulation
        ↓
Step 2: Compute Delaunay triangulation in 2D
        → Produces M triangles, each defined by 3 vertex indices
        ↓
Step 3: Map Z values back — each vertex index already has a Z
        → Result: a 3D triangulated surface
```

### Why triangulate in 2D, not 3D?

Survey points are distributed across a **plan view** (a roughly horizontal spread). Triangulating in 2D (X, Y only) produces a surface that represents the **terrain** — one Z value for each (X, Y) location. A 3D triangulation would produce a **volume** (tetrahedra), which is not what we want.

### Visual intuition

Imagine looking straight down at the survey points:

```
    •       •
        •
    •       •
      •   •
        •
```

Delaunay connects them:

```
    •───────•
    │╲  △  ╱│
    │  •  ╱ │
    •╱  ╲╱  •
    │ △ ╱╲△ │
    │ •╱──•─│
    │╱  △  ╲│
        •
```

Each triangle is then "lifted" to its correct elevation using the Z values.

---

## Stage 4 — Boundary Clipping (Optional)

### The problem
Delaunay triangulation creates a **convex hull** — the outermost triangles stretch to enclose all points in a convex shape. But the actual site boundary may be concave (L-shaped, irregular, etc.), so triangles outside the site should be removed.

### How clipping works

```
For each triangle in the mesh:
    1. Compute the triangle's CENTROID:
       centroid = average of the three vertex positions (X, Y only)
    
    2. Test: does the boundary polygon CONTAIN this centroid?
       - Yes → Keep the triangle
       - No  → Discard the triangle
```

### Centroid calculation

For a triangle with vertices A, B, C:

```
centroid_x = (A.x + B.x + C.x) / 3
centroid_y = (A.y + B.y + C.y) / 3
```

### Point-in-polygon test

The application uses the **ray casting algorithm** (via Shapely):

1. Cast a ray from the centroid in any direction (typically +X)
2. Count how many times it crosses the polygon boundary
3. **Odd** number of crossings → point is **inside**
4. **Even** number of crossings → point is **outside**

### Boundary extraction

The boundary polygon is read from a `LWPOLYLINE` or `POLYLINE` entity on the user-selected layer. The vertex coordinates define the polygon perimeter.

---

## Stage 5 — Contour Line Generation

### The problem
Contour lines are horizontal slices through the 3D surface at regular elevation intervals (e.g., every 0.5 m). They help visualise gradient and slope.

### How contour lines are computed

```
For each contour level Z_level (e.g., 100.0, 100.5, 101.0, ...):
    For each triangle in the mesh:
        For each edge of the triangle (3 edges per triangle):
            
            Let Z_a = elevation at vertex A
            Let Z_b = elevation at vertex B
            
            Does this edge CROSS the contour level?
            → Yes, if Z_a and Z_b are on opposite sides of Z_level
              i.e., (Z_a - Z_level) × (Z_b - Z_level) < 0
            
            If yes, find the INTERSECTION POINT by linear interpolation:
                t = (Z_level - Z_a) / (Z_b - Z_a)
                intersection_X = A.x + t × (B.x - A.x)
                intersection_Y = A.y + t × (B.y - A.y)
        
        If the triangle has exactly 2 edge crossings:
            → Draw a line segment between the two intersection points
            (This is one piece of the contour line)
```

### Visual intuition

Consider a single triangle with vertices at elevations 99.0, 100.3, and 101.2. For a contour at Z = 100.0:

```
         101.2
          /\
         /  \          ← contour level 100.0 cuts
        /----\            through two edges here
       /      \
    99.0──────100.3
```

The contour line intersects two edges. Linear interpolation finds the exact crossing points, and a line segment is drawn between them.

---

## Stage 6 — 3D Mesh Rendering

### Mesh representation

The terrain surface is rendered as a **triangle mesh** defined by:

| Data | Description |
|------|-------------|
| **x, y, z** arrays | The N vertex positions (z optionally scaled by exaggeration factor) |
| **i, j, k** arrays | Each row defines one triangle by referencing 3 vertex indices |
| **intensity** | The raw Z (elevation) at each vertex, mapped to a colour scale |

### Colour mapping

Each vertex is assigned a colour based on its elevation:
- The colour scale maps the **minimum elevation → one end** and **maximum elevation → other end**
- Available palettes: Earth, Viridis, Turbo, Inferno, Cividis, Terrain, Hot
- Interpolation is continuous — smooth gradients across triangle faces

### Wireframe overlay

To make individual triangles visible:
- For every triangle, its 3 edges are drawn as semi-transparent white line segments
- This creates a mesh grid overlay on top of the coloured surface

### Z exaggeration

Terrain often has very small vertical variation compared to horizontal extent. Z exaggeration multiplies all Z values by a user-chosen factor:

```
displayed_Z = actual_Z × exaggeration_factor
```

- **1.0×** = true proportions
- **5.0×** = vertical differences appear 5× larger (useful for flat sites)
- **0.5×** = flatten the view (useful for steep terrain)

> [!IMPORTANT]
> The colour mapping always uses the **real** elevation values, not the exaggerated ones, so the heatmap remains accurate regardless of the exaggeration setting.

### Lighting

The 3D surface uses flat shading with a simulated directional light:
- **Ambient light** (60%): base illumination so no face is completely dark
- **Diffuse light** (50%): faces angled toward the light source appear brighter
- **Specular light** (20%): subtle highlights on faces directly facing the light

---

## Stage 7 — Export

### OBJ Format (Wavefront)

A plain-text format listing vertices and faces:

```
Structure:
    Line "v X Y Z"    → one line per vertex (N lines)
    Line "f i j k"     → one line per triangle face (M lines)
                         (indices are 1-based)
```

This format is universally supported by 3D software (Blender, SketchUp, Rhino, 3ds Max, Unity, Unreal).

### DXF Format (3DFACE)

A new DXF file is created containing `3DFACE` entities:
- Each triangle becomes one `3DFACE` entity with 4 vertices (the 4th repeats the 3rd for triangles)
- The DXF version is R2010 for broad AutoCAD compatibility
- Can be opened directly in AutoCAD, Civil 3D, or BricsCAD

---

## Summary of Algorithms Used

| Algorithm | Where Used | Purpose |
|-----------|-----------|---------|
| **Regular expression matching** | Elevation extraction | Parse numeric values from varied text formats |
| **Hash-based deduplication** | Elevation extraction | Detect duplicate (X, Y) points |
| **Delaunay triangulation** | Mesh generation | Connect scattered points into optimal triangles |
| **Centroid computation** | Boundary clipping | Find the centre of each triangle |
| **Ray casting** | Boundary clipping | Test if a point lies inside a polygon |
| **Linear interpolation** | Contour generation | Find where contour level crosses triangle edges |
| **Colour mapping** | 3D rendering | Map elevation values to a continuous colour scale |
| **Flat shading** | 3D rendering | Simulate lighting on triangle faces |

---

## Computational Complexity

| Stage | Complexity | Typical for 500 points |
|-------|-----------|----------------------|
| DXF parsing | O(E) where E = total entities | < 1 second |
| Elevation extraction | O(T) where T = text entities on layer | < 0.1 seconds |
| Delaunay triangulation | O(N log N) where N = elevation points | < 0.01 seconds |
| Boundary clipping | O(M) where M = number of triangles | < 0.1 seconds |
| Contour generation | O(L × M) where L = contour levels | < 0.5 seconds |
| 3D rendering | Handled by browser GPU (WebGL) | Real-time |

> [!TIP]
> The most computationally intensive part is **rendering**, not computing. The browser's WebGL engine handles the 3D graphics, so even meshes with thousands of triangles remain interactive.
