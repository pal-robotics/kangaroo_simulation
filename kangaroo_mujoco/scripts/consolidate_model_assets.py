#!/usr/bin/env python3
# Copyright (c) 2026 PAL Robotics S.L. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Consolidate duplicated visual mesh assets across pregenerated MuJoCo models.

Each pregenerated model variant under ``models/`` ships its own copy of
``assets/full/`` (the ``.obj`` visual meshes). Shared robot-body meshes
(legs, torso, base, camera, etc.) are byte-identical across variants.  This
script:

1. **Verifies** which assets are duplicated and that same-named files are
   byte-identical (no silent content divergence).
2. **Builds** (or updates) a single shared pool at ``models/assets/full/``
   from the union of all variants.
3. **Replaces** each variant's ``assets/full`` directory with a symlink
   ``../../assets/full`` pointing at the shared pool.
4. **Fixes** any ``<compiler>`` tag in a model's ``mujoco_description.xml``
   that still carries a stale absolute temp path (e.g. ``/tmp/tmpXXX/assets/``)
   instead of the correct relative ``assets/``.

In ``--verify`` mode the script only reports duplication and content conflicts
without making any changes — safe to run at any time.

Regenerating a model variant with the upstream ``robot_description_to_mjcf.sh``
tool will replace the symlink with a fresh per-variant copy.  Re-run this
script (without ``--verify``) afterwards to restore the shared layout.

Usage::

    # Report duplicate/conflicting assets (read-only):
    python3 scripts/consolidate_model_assets.py --verify

    # Apply consolidation (build shared pool, replace per-model full/ dirs):
    python3 scripts/consolidate_model_assets.py

    # Dry-run — shows what would change without touching anything:
    python3 scripts/consolidate_model_assets.py --dry-run
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_model_dirs(models_root: Path) -> list[Path]:
    """Return all mjcf_data_* variant directories directly under models_root."""
    return sorted(p for p in models_root.iterdir()
                  if p.is_dir() and p.name.startswith("mjcf_data_"))


def _full_dir(model_dir: Path) -> Path | None:
    """Return the real (resolved) assets/full directory for a model, or None.

    If assets/full is already a symlink this follows it.  Returns None when
    the directory does not exist.
    """
    candidate = model_dir / "assets" / "full"
    resolved = candidate.resolve()
    return resolved if resolved.is_dir() else None


# ---------------------------------------------------------------------------
# Step 1 – Verify
# ---------------------------------------------------------------------------

def verify(models_root: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Scan all model variants and report duplicated / conflicting mesh files.

    Returns:
        basenames: mapping ``filename -> {model_dir_name: md5}``.
        conflicts: list of filename strings where the same name has different
            content across models (these must NOT be silently merged).
    """
    model_dirs = _find_model_dirs(models_root)
    if not model_dirs:
        print("No mjcf_data_* directories found — nothing to verify.", file=sys.stderr)
        return {}, []

    # Collect every file path relative to assets/full/, keyed by basename
    # Structure: basenames[rel_path][model_name] = md5
    basenames: dict[str, dict[str, str]] = {}

    for model_dir in model_dirs:
        full = _full_dir(model_dir)
        if full is None:
            print(f"  WARNING: {model_dir.name}/assets/full/ missing or not a directory — skipped.")
            continue
        for path in sorted(full.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(full))
            basenames.setdefault(rel, {})[model_dir.name] = _md5(path)

    # Separate duplicated-and-identical from conflicting
    duplicated: dict[str, dict[str, str]] = {}
    conflicts: list[str] = []

    for rel, model_map in sorted(basenames.items()):
        if len(model_map) < 2:
            continue  # unique to one model — fine
        unique_hashes = set(model_map.values())
        if len(unique_hashes) == 1:
            duplicated[rel] = model_map
        else:
            conflicts.append(rel)

    # Report
    total_files = sum(len(m) for m in basenames.values())
    dup_copies = sum(len(m) - 1 for m in duplicated.values())
    print(f"\nModels found      : {len(model_dirs)}")
    print(f"Total asset files : {total_files}")
    print(f"Duplicated files  : {len(duplicated)}  ({dup_copies} redundant copies)")
    print(f"Content conflicts : {len(conflicts)}")

    if duplicated:
        print("\nDuplicated (byte-identical across models) — safe to share:")
        for rel, model_map in sorted(duplicated.items()):
            models_str = ", ".join(sorted(model_map))
            print(f"  {rel}  [{models_str}]")

    if conflicts:
        print("\nCONFLICTS — same filename, different content — NOT merged:")
        for rel in conflicts:
            for model_name, digest in sorted(basenames[rel].items()):
                print(f"  {rel}  {digest[:10]}  {model_name}")

    return basenames, conflicts


# ---------------------------------------------------------------------------
# Step 2 – Build shared pool
# ---------------------------------------------------------------------------

def build_shared_pool(models_root: Path, dry_run: bool = False) -> Path:
    """Merge all model variants' assets/full/ trees into models_root/assets/full/.

    Uses a no-clobber copy strategy.  Files that already exist in the pool are
    skipped (they are identical, verified by verify()).

    Returns the path to the shared pool directory.
    """
    shared_full = models_root / "assets" / "full"
    model_dirs = _find_model_dirs(models_root)

    if not dry_run:
        shared_full.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    for model_dir in model_dirs:
        full = _full_dir(model_dir)
        if full is None:
            continue
        # Skip if this model's full/ already resolves to the shared pool
        # (i.e. it's already a symlink pointing there).
        if full == shared_full.resolve():
            continue

        for src in sorted(full.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(full)
            dst = shared_full / rel
            if dst.exists():
                skipped += 1
                continue
            if dry_run:
                print(f"  [dry-run] would copy {src.relative_to(models_root)} -> {dst.relative_to(models_root)}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            copied += 1

    action = "Would copy" if dry_run else "Copied"
    print(f"\nShared pool: {shared_full.relative_to(models_root)}")
    print(f"  {action} {copied} file(s), skipped {skipped} already-present file(s).")
    return shared_full


# ---------------------------------------------------------------------------
# Step 3 – Replace per-model full/ with symlink
# ---------------------------------------------------------------------------

def install_symlinks(models_root: Path, dry_run: bool = False) -> None:
    """Replace each model variant's assets/full dir with a symlink to the pool.

    The symlink target is a path relative to the symlink's location so it
    survives being installed into the colcon/ament share directory.  The
    target ``../../assets/full`` from ``models/<variant>/assets/full`` resolves
    to ``models/assets/full`` in both the source and install trees.
    """
    shared_full = models_root / "assets" / "full"
    if not shared_full.is_dir():
        print("ERROR: shared pool does not exist yet — run without --verify first.",
              file=sys.stderr)
        return

    model_dirs = _find_model_dirs(models_root)
    symlink_target = Path("../../assets/full")

    for model_dir in model_dirs:
        link_path = model_dir / "assets" / "full"

        # Already the correct symlink — nothing to do.
        if link_path.is_symlink() and link_path.readlink() == symlink_target:
            print(f"  {link_path.relative_to(models_root)}  already symlinked — skipped.")
            continue

        if dry_run:
            if link_path.is_symlink():
                print(f"  [dry-run] would re-point {link_path.relative_to(models_root)} "
                      f"(currently -> {link_path.readlink()}) -> {symlink_target}")
            elif link_path.is_dir():
                print(f"  [dry-run] would replace directory {link_path.relative_to(models_root)} "
                      f"with symlink -> {symlink_target}")
            else:
                print(f"  [dry-run] would create symlink {link_path.relative_to(models_root)} "
                      f"-> {symlink_target}")
            continue

        # Remove existing real directory or stale symlink.
        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.is_dir():
            shutil.rmtree(link_path)

        link_path.symlink_to(symlink_target)
        print(f"  {link_path.relative_to(models_root)} -> {symlink_target}")


# ---------------------------------------------------------------------------
# Step 4 – Fix stale /tmp compiler paths
# ---------------------------------------------------------------------------

_STALE_MESHDIR_RE = re.compile(
    r'\b(meshdir|texturedir|assetdir)\s*=\s*"(/tmp/[^"]+)"'
)


def fix_compiler_paths(models_root: Path, dry_run: bool = False) -> None:
    """Fix <compiler> tags that still reference absolute /tmp/... asset dirs.

    The correct relative value is ``assets/`` (resolved by MuJoCo against the
    XML file's own directory).  Only ``mujoco_description.xml`` files are
    patched; the formatted variants carry correct paths already.
    """
    model_dirs = _find_model_dirs(models_root)
    fixed = 0

    for model_dir in model_dirs:
        xml_path = model_dir / "mujoco_description.xml"
        if not xml_path.is_file():
            continue

        original = xml_path.read_text()
        patched = _STALE_MESHDIR_RE.sub(r'\1="assets/"', original)

        if patched == original:
            continue

        fixed += 1
        if dry_run:
            print(f"  [dry-run] would fix stale /tmp compiler path in "
                  f"{xml_path.relative_to(models_root)}")
        else:
            xml_path.write_text(patched)
            print(f"  Fixed stale /tmp compiler path in {xml_path.relative_to(models_root)}")

    if fixed == 0:
        print("  No stale /tmp compiler paths found.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consolidate duplicated visual mesh assets across pregenerated "
                    "MuJoCo model variants into a single shared pool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only report duplication and conflicts; make no changes (implies --dry-run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying anything on disk.",
    )
    parser.add_argument(
        "--models-dir",
        default=None,
        metavar="PATH",
        help="Path to the models/ directory.  Defaults to ../models relative to this script.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    if args.models_dir:
        models_root = Path(args.models_dir).resolve()
    else:
        models_root = (script_dir / ".." / "models").resolve()

    if not models_root.is_dir():
        print(f"ERROR: models directory not found: {models_root}", file=sys.stderr)
        return 1

    dry_run = args.dry_run or args.verify
    print(f"Models directory : {models_root}")
    if dry_run:
        print("Mode             : DRY-RUN (no changes will be made)\n")

    # Step 1 — always run
    print("=" * 60)
    print("Step 1: Verify duplicate assets")
    print("=" * 60)
    _basenames, conflicts = verify(models_root)

    if conflicts:
        print(
            "\nERROR: Content conflicts detected (see above).  "
            "Consolidation aborted to avoid data loss.",
            file=sys.stderr,
        )
        return 1

    if args.verify:
        return 0

    # Step 2 — build shared pool
    print("\n" + "=" * 60)
    print("Step 2: Build shared pool")
    print("=" * 60)
    build_shared_pool(models_root, dry_run=dry_run)

    # Step 3 — install symlinks
    print("\n" + "=" * 60)
    print("Step 3: Install symlinks")
    print("=" * 60)
    install_symlinks(models_root, dry_run=dry_run)

    # Step 4 — fix stale compiler paths
    print("\n" + "=" * 60)
    print("Step 4: Fix stale /tmp compiler paths")
    print("=" * 60)
    fix_compiler_paths(models_root, dry_run=dry_run)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
