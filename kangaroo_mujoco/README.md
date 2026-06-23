# kangaroo_mujoco

MuJoCo simulation package for the Kangaroo robot. Provides pregenerated MJCF
model variants and the launch infrastructure to run them under
`mujoco_ros2_control`.

## Contents

```
models/                        Pregenerated MJCF model variants
  assets/
    full/                      Shared visual mesh pool (all .obj files live here)
  mjcf_data_<variant>/
    mujoco_description_formatted.xml   Runtime MJCF (loaded by the launch file)
    mujoco_description.xml             Intermediate MJCF (not loaded at runtime)
    robot_description_formatted.urdf   Source URDF
    assets/
      full -> ../../assets/full        Symlink to the shared mesh pool
      decomposed/                      Per-variant convex-collision meshes
scripts/
  publish_mjcf.py              Latched ROS 2 publisher for a pregenerated MJCF
  consolidate_model_assets.py  Tool to deduplicate visual meshes across variants
test/
  test_model_assets.py         Regression tests for the consolidated asset layout
```

### Model variants

Each variant is named `mjcf_data_{arm_type}_{end_effector_right}_{end_effector_left}[_fixed]`.
Currently pregenerated variants:

| Directory | Arm | End-effectors |
|---|---|---|
| `mjcf_data_5dof_RH8D_RH8D_fixed` | 5-DoF (fixed ankle type) | RH8D dexterous hands |
| `mjcf_data_4dof_fake-forearm_fake-forearm_fixed` | 4-DoF (fixed ankle type) | Fake forearm stubs |
| `mjcf_data_no-arm_no-end-effector_no-end-effector_fixed` | None (fixed ankle type) | None |

---

## Consolidated asset layout

All visual `.obj` meshes live in a **single shared pool** at `models/assets/full/`.
Each variant's `assets/full` is a symlink pointing at that pool:

```
models/
  assets/
    full/               <-- one copy of every visual mesh
      d435/d435.obj
      torso_link/torso_link.obj
      arm1_link/arm1_link.obj
      ...
  mjcf_data_5dof_RH8D_RH8D/
    assets/
      full -> ../../assets/full   <-- symlink (no per-variant copy)
      decomposed/                 <-- real dir, collision meshes only
  mjcf_data_4dof_fake-forearm_fake-forearm/
    assets/
      full -> ../../assets/full
      decomposed/
  ...
```

This avoids triplicating ~55 MB of identical mesh data. The `decomposed/`
convex-collision sets are intentionally kept per-variant because the number
of collision pieces differs across variants.

### After regenerating a model variant

The upstream generator (`mujoco_ros2_control`'s `robot_description_to_mjcf.sh`)
writes a fresh per-variant `assets/full/` directory, replacing the symlink.
After regeneration, restore the shared layout by running the consolidation
script (see below).

---

## Consolidating model assets

### What the script does

`scripts/consolidate_model_assets.py` performs four idempotent steps:

1. **Verify** — MD5-scans all `assets/full/` trees, reports duplicated files
   and aborts if any same-named file has different content across variants
   (conflict guard).
2. **Build shared pool** — merges all variant `assets/full/` trees into
   `models/assets/full/` (no-clobber, lossless union).
3. **Install symlinks** — replaces each variant's `assets/full/` directory
   with a symlink `../../assets/full`.
4. **Fix stale paths** — patches any `<compiler meshdir="/tmp/...">` in
   `mujoco_description.xml` files back to the correct relative `assets/`.

### Usage

```bash
# Report duplicates and conflicts only (read-only):
python3 scripts/consolidate_model_assets.py --verify

# Preview what would change without touching anything:
python3 scripts/consolidate_model_assets.py --dry-run

# Apply consolidation (idempotent — safe to re-run):
python3 scripts/consolidate_model_assets.py
```

A custom models directory can be specified with `--models-dir <path>` (default:
`../models` relative to the script).

### Typical workflow after regenerating a variant

1. Navigate to the models folder of the kangaroo_mujoco package

2. Regenerate the variant (replaces the symlink with a real copy):

```bash
ros2 launch kangaroo_mujoco generate_decomposed_collision_meshes.launch.py \
    arm_type:=5dof end_effector_right:=RH8D end_effector_left:=RH8D
```

3. Restore the shared layout:
```bash
ros2 run kangaroo_mujoco consolidate_model_assets.py
```

---

## Running the simulation

```bash
ros2 launch kangaroo_mujoco kangaroo_mujoco.launch.py \
    arm_type:=5dof \
    end_effector_right:=RH8D \
    end_effector_left:=RH8D
```

The launch file checks for a pregenerated variant in `models/`. If found, it
publishes the MJCF directly via `publish_mjcf.py`. If not found, it falls back
to regenerating from the robot description.
