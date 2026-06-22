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

"""Regression tests for the consolidated pregenerated model asset layout.

Invariants locked in by these tests:

1. A single shared visual mesh pool exists at ``models/assets/full/``.
2. Every ``mjcf_data_*`` variant references that pool via a symlink — no
   per-variant real copy of ``assets/full/`` is present.
3. No real ``.obj`` or ``.stl`` mesh file lives directly inside a variant dir
   (i.e. outside the shared pool) — the only source of truth for visual meshes
   is ``models/assets/full/``.  The per-model ``assets/decomposed/`` dirs are
   intentionally excluded: collision-piece counts differ per variant and are not
   deduplicated.
4. No MJCF ``<compiler>`` tag references a ``/tmp/...`` absolute path for
   ``meshdir``, ``texturedir``, or ``assetdir``.  Such paths leak the generator's
   build-time temp dir and fail to resolve on any other machine.

If any test here fails after regenerating a model variant, run::

    python3 scripts/consolidate_model_assets.py

to restore the shared layout.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve package root and reuse helpers from the consolidation script so the
# logic and the tests stay in sync.
# ---------------------------------------------------------------------------

PKG_ROOT = Path(__file__).resolve().parents[1]
MODELS = PKG_ROOT / "models"
sys.path.insert(0, str(PKG_ROOT / "scripts"))

from consolidate_model_assets import (  # noqa: E402
    _find_model_dirs,
    _STALE_MESHDIR_RE,
)

_MESH_SUFFIXES = {".obj", ".stl"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _real_mesh_files_outside_decomposed():
    """Return all real (non-symlink) mesh files under models/ that are NOT inside
    a decomposed/ subtree, following no symlinks during the walk.
    """
    real_meshes = []
    for dirpath, dirnames, filenames in os.walk(MODELS, followlinks=False):
        p = Path(dirpath)
        # Skip decomposed/ trees entirely — they are intentionally per-model.
        if "decomposed" in p.parts:
            dirnames.clear()
            continue
        for name in filenames:
            fp = p / name
            if fp.suffix in _MESH_SUFFIXES and not fp.is_symlink():
                real_meshes.append(fp)
    return real_meshes


# ---------------------------------------------------------------------------
# Test 1 – shared pool must exist and be non-empty
# ---------------------------------------------------------------------------

def test_shared_pool_exists():
    """models/assets/full/ must be a real directory containing at least one .obj."""
    shared_full = MODELS / "assets" / "full"
    assert shared_full.is_dir() and not shared_full.is_symlink(), (
        f"Shared pool {shared_full} is missing or is itself a symlink — "
        "run 'python3 scripts/consolidate_model_assets.py' to build it."
    )
    obj_files = list(shared_full.rglob("*.obj"))
    assert obj_files, (
        f"Shared pool {shared_full} exists but contains no .obj files."
    )


# ---------------------------------------------------------------------------
# Test 2 – every variant's assets/full must be a symlink to the shared pool
# ---------------------------------------------------------------------------

def test_each_variant_full_is_symlink_to_pool():
    """Every mjcf_data_* variant's assets/full must be a symlink resolving to
    the shared pool, not a real directory.
    """
    model_dirs = _find_model_dirs(MODELS)
    assert model_dirs, f"No mjcf_data_* directories found under {MODELS}."

    shared_real = (MODELS / "assets" / "full").resolve()
    failures = []

    for model_dir in model_dirs:
        link = model_dir / "assets" / "full"
        if not link.is_symlink():
            failures.append(
                f"{link.relative_to(PKG_ROOT)}: is a real directory, not a symlink — "
                "per-model copy still present"
            )
        elif link.resolve() != shared_real:
            failures.append(
                f"{link.relative_to(PKG_ROOT)}: symlink points to {link.resolve()} "
                f"instead of {shared_real}"
            )

    assert not failures, (
        "One or more variant full/ dirs are not correctly symlinked to the shared pool:\n"
        + "\n".join(f"  {f}" for f in failures)
        + "\nRun 'python3 scripts/consolidate_model_assets.py' to fix."
    )


# ---------------------------------------------------------------------------
# Test 3 – no real mesh files inside any variant dir (outside decomposed/)
# ---------------------------------------------------------------------------

def test_no_duplicate_meshes_across_variants():
    """No real .obj/.stl file must live inside a mjcf_data_* variant directory.

    All visual meshes must live exclusively in the shared pool
    (models/assets/full/).  Checks follow no symlinks so the pool itself is
    not traversed via the variant symlinks.  The decomposed/ collision dirs are
    excluded because per-model collision pieces are intentionally not shared.
    """
    model_dirs = _find_model_dirs(MODELS)
    model_dir_names = {d.name for d in model_dirs}

    rogue_files = []
    for fp in _real_mesh_files_outside_decomposed():
        # Relative path from MODELS root (e.g. mjcf_data_.../assets/full/arm1_link.obj)
        rel = fp.relative_to(MODELS)
        # First component is the containing dir
        if rel.parts[0] in model_dir_names:
            rogue_files.append(str(rel))

    assert not rogue_files, (
        f"{len(rogue_files)} mesh file(s) found inside variant directories "
        "(expected all meshes to live only in the shared pool):\n"
        + "\n".join(f"  {f}" for f in sorted(rogue_files))
        + "\nRun 'python3 scripts/consolidate_model_assets.py' to consolidate."
    )


# ---------------------------------------------------------------------------
# Test 4 – no /tmp compiler paths in any model XML
# ---------------------------------------------------------------------------

def test_no_tmp_compiler_paths():
    """No <compiler> tag in any model XML may reference a /tmp/... asset dir.

    Such paths leak the generator's build-time temp directory and fail to
    resolve on any other machine.  The correct value is the relative 'assets/'.
    """
    offending = []
    for xml_path in MODELS.rglob("*.xml"):
        text = xml_path.read_text()
        for match in _STALE_MESHDIR_RE.finditer(text):
            offending.append(
                f"{xml_path.relative_to(PKG_ROOT)}: "
                f"{match.group(1)}=\"{match.group(2)}\""
            )

    assert not offending, (
        "Stale /tmp compiler path(s) found in model XML(s) — "
        "they must use the relative 'assets/' instead:\n"
        + "\n".join(f"  {o}" for o in offending)
        + "\nRun 'python3 scripts/consolidate_model_assets.py' to fix."
    )
