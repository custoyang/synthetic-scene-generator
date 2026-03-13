# Controlled Synthetic Scene Generator

This repository is a small **Blender-based synthetic media pipeline** designed to generate **controlled image variations** (camera views, object color, lighting, and layout) for **AI evaluation / dataset building**.

The goal is to demonstrate comfort with creative tooling (Blender + optional image/vector tools) in a way that matches how AI research teams often create **repeatable, parameterized media assets**.

## What it produces

- A simple tabletop scene (plane + cube + sphere)
- A grid of **controlled variations**:
  - **Camera views** (e.g., 5 angles)
  - **Sphere color** (e.g., 3 colors)
  - **Light intensity** (e.g., 2 settings)
  - **Layout** (e.g., 2 object arrangements)
- Output:
  - PNG images
  - `metadata.csv` describing each render

## Quickstart (headless)

1) Install Blender (3.6+ recommended).

2) From the repo root:

```bash
# mac/linux
blender -b -P blender/generate_dataset.py -- --out_dir outputs/run1 --seed 7 --n_colors 3 --n_lights 2 --n_layouts 2 --n_views 5 --resolution 512
```

On Windows (example):

```bat
"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe" -b -P blender\generate_dataset.py -- --out_dir outputs\run1 --seed 7
```

## Sample outputs

See `outputs/samples/` for example renders (included for preview).  
When you run the generator, your full dataset will be written to `outputs/run1/`.

## How to explain this in an application

- *“I used Blender’s Python API (bpy) to generate controlled synthetic scenes and render systematic variations (camera angle, lighting, color, layout), exporting images and metadata for downstream AI evaluation.”*
- This mirrors common AI media workflows: **controlled generation → labeled outputs → evaluation-ready assets**.

## Repo structure

- `blender/generate_dataset.py` — dataset generator (bpy)
- `outputs/samples/` — included preview images
- `outputs/samples_metadata.csv` — preview metadata

## Extensions (easy upgrades)

If you want to push this further:
- Add **random textures** (Krita/GIMP-made) on the plane/object
- Add **SVG decals** (Inkscape) and apply as textures
- Output **segmentation masks** / depth maps (Blender render passes)
- Add more primitives / props and constraints
