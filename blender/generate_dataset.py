"""
Moonstone Synthetic Scene Dataset Generator (Blender)

Generates a simple tabletop scene (plane + cube + sphere), then renders controlled variations
for AI evaluation / dataset creation.

Tested target: Blender 3.6+ (should also work on Blender 4.x).

Run headless:
  blender -b -P blender/generate_dataset.py -- --out_dir outputs/run1 --seed 7

Optional args:
  --n_colors 3
  --n_lights 2
  --n_layouts 2
  --n_views 5
  --resolution 512
  --samples_per_combo 1

Outputs:
  - PNG renders with descriptive filenames
  - metadata.csv with per-image settings

UI note:
  If you run from Blender's Scripting tab (Run Script), Blender won't pass CLI args.
  This script includes safe defaults in that case.
"""
import bpy
import os
import random
import csv
import sys

# -----------------------------
# Arg parsing (works for headless CLI)
# -----------------------------
def parse_args():
    argv = sys.argv
    if "--" not in argv:
        return {}
    args = argv[argv.index("--") + 1 :]

    def get(name, default=None, cast=str):
        if name in args:
            i = args.index(name)
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                return cast(args[i + 1])
            return True
        return default

    return {
        "out_dir": get("--out_dir", "outputs/run1", str),
        "seed": get("--seed", 0, int),
        "n_colors": get("--n_colors", 3, int),
        "n_lights": get("--n_lights", 2, int),
        "n_layouts": get("--n_layouts", 2, int),
        "n_views": get("--n_views", 5, int),
        "resolution": get("--resolution", 512, int),
        "samples_per_combo": get("--samples_per_combo", 1, int),
    }


# -----------------------------
# Scene helpers
# -----------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Purge orphan data (safe-ish)
    for _ in range(3):
        try:
            bpy.ops.outliner.orphans_purge(do_recursive=True)
        except Exception:
            pass


def ensure_cycles():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True


def set_render_settings(res):
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    scene.render.resolution_percentage = 100


def make_material(name, rgba, roughness=0.35):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_table():
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, 0))
    table = bpy.context.active_object
    table.name = "Table"
    mat = make_material("Mat_Table", (0.75, 0.68, 0.55, 1.0), roughness=0.6)
    table.data.materials.append(mat)
    return table


def add_cube(loc):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=loc)
    cube = bpy.context.active_object
    cube.name = "Cube"
    return cube


def add_sphere(loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=loc)
    sph = bpy.context.active_object
    sph.name = "Sphere"
    return sph


def add_light(strength):
    bpy.ops.object.light_add(type="AREA", location=(1.5, -1.2, 2.0))
    light = bpy.context.active_object
    light.data.energy = strength
    light.data.size = 1.5
    return light


def add_camera():
    bpy.ops.object.camera_add(location=(2.0, -2.0, 1.2))
    cam = bpy.context.active_object
    cam.data.lens = 45
    bpy.context.scene.camera = cam
    return cam


def look_at(obj, target_vec):
    import mathutils

    direction = target_vec - obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = rot_quat.to_euler()


def render_to(path):
    scene = bpy.context.scene
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


# -----------------------------
# Main
# -----------------------------
def main():
    cfg = parse_args()

    # IMPORTANT: Make UI runs safe (no CLI args passed)
    # If you're running inside Blender UI, set OUT_DIR below to your absolute path.
    # Example Mac:
    #   /Users/yourname/Desktop/moonstone_synthetic_scene_dataset/outputs/run1
    # Example Windows:
    #   C:\\Users\\yourname\\Desktop\\moonstone_synthetic_scene_dataset\\outputs\\run1
    cfg.setdefault("out_dir", "/Users/custoyang/Downloads/moonstone_synthetic_scene_dataset/outputs/samples/run1")
    cfg.setdefault("seed", 7)
    cfg.setdefault("n_colors", 3)
    cfg.setdefault("n_lights", 2)
    cfg.setdefault("n_layouts", 2)
    cfg.setdefault("n_views", 5)
    cfg.setdefault("resolution", 512)
    cfg.setdefault("samples_per_combo", 1)

    random.seed(int(cfg["seed"]))

    out_dir = os.path.abspath(cfg["out_dir"])
    os.makedirs(out_dir, exist_ok=True)

    clear_scene()
    ensure_cycles()
    set_render_settings(int(cfg["resolution"]))

    # base scene
    add_table()
    cube = add_cube((-0.5, 0.0, 0.25))
    sphere = add_sphere((0.3, 0.3, 0.25))
    light = add_light(800)
    cam = add_camera()

    # controlled variations
    palette = [
        ("red", (0.80, 0.12, 0.12, 1.0)),
        ("blue", (0.10, 0.35, 0.85, 1.0)),
        ("green", (0.10, 0.70, 0.25, 1.0)),
        ("yellow", (0.90, 0.80, 0.10, 1.0)),
        ("purple", (0.55, 0.20, 0.80, 1.0)),
    ]
    n_colors = max(1, min(int(cfg["n_colors"]), len(palette)))
    colors = palette[:n_colors]

    cube_mat = make_material("Mat_Cube", (0.70, 0.70, 0.72, 1.0), roughness=0.35)
    cube.data.materials.clear()
    cube.data.materials.append(cube_mat)

    # light energy presets (max 3)
    all_light_levels = [600, 1200, 2000]
    n_lights = max(1, min(int(cfg["n_lights"]), len(all_light_levels)))
    light_levels = all_light_levels[:n_lights]

    # layouts (max 2)
    all_layouts = [
        ("A", (-0.5, 0.0, 0.25), (0.3, 0.3, 0.25)),
        ("B", (-0.2, -0.2, 0.25), (0.6, 0.1, 0.25)),
    ]
    n_layouts = max(1, min(int(cfg["n_layouts"]), len(all_layouts)))
    layouts = all_layouts[:n_layouts]

    # camera views (max 5)
    all_views = [
        ("v1", (2.0, -2.0, 1.2)),
        ("v2", (2.2, -1.2, 1.0)),
        ("v3", (1.6, -2.4, 1.3)),
        ("v4", (1.8, -1.6, 0.8)),
        ("top", (0.0, -1.2, 2.2)),
    ]
    n_views = max(1, min(int(cfg["n_views"]), len(all_views)))
    views = all_views[:n_views]

    samples_per = max(1, int(cfg["samples_per_combo"]))

    metadata_path = os.path.join(out_dir, "metadata.csv")
    fieldnames = ["filename", "color", "light_energy", "layout", "view", "seed"]

    idx = 0
    with open(metadata_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for (color_name, rgba) in colors:
            sph_mat = make_material(f"Mat_Sphere_{color_name}", rgba, roughness=0.25)
            sphere.data.materials.clear()
            sphere.data.materials.append(sph_mat)

            for energy in light_levels:
                light.data.energy = float(energy)

                for (layout_name, cube_loc, sph_loc) in layouts:
                    cube.location = cube_loc
                    sphere.location = sph_loc

                    for (view_name, cam_loc) in views:
                        cam.location = cam_loc

                        import mathutils
                        target = (cube.location + sphere.location) / 2.0
                        look_at(cam, target)

                        for _ in range(samples_per):
                            idx += 1
                            fname = (
                                f"img_{idx:04d}_color-{color_name}"
                                f"_light-{int(energy)}_layout-{layout_name}"
                                f"_view-{view_name}.png"
                            )
                            fpath = os.path.join(out_dir, fname)
                            render_to(fpath)
                            writer.writerow(
                                {
                                    "filename": fname,
                                    "color": color_name,
                                    "light_energy": int(energy),
                                    "layout": layout_name,
                                    "view": view_name,
                                    "seed": int(cfg["seed"]),
                                }
                            )

    print(f"Done. Wrote renders + metadata to: {out_dir}")


if __name__ == "__main__":
    main()
