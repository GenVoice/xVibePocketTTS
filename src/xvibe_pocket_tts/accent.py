"""Pinned and reproducible RUAccent resource loading."""

import os
from pathlib import Path

import ruaccent as ruaccent_package
from huggingface_hub import snapshot_download
from ruaccent import RUAccent

RUACCENT_REPO = "ruaccent/accentuator"
RUACCENT_REVISION = "b78ae5ea1e62beaf138bed1865cd8c3b0b5ca855"
RUACCENT_MODEL_SIZE = "turbo3.1"

_PIPELINE_PATTERNS = [
    "dictionary/**",
    "nn/nn_accent/**",
    "nn/nn_stress_usage_predictor/**",
    "nn/nn_yo_homograph_resolver/**",
    f"nn/nn_omograph/{RUACCENT_MODEL_SIZE}/**",
]


def _prefetch_resources(workdir: Path) -> None:
    """Download only the selected pipeline instead of the full 6.2 GB repository."""

    workdir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=RUACCENT_REPO,
        revision=RUACCENT_REVISION,
        allow_patterns=_PIPELINE_PATTERNS,
        local_dir=workdir,
    )

    # Full RUAccent mode imports Koziev's rule engine from inside the installed
    # ruaccent package. Prefetch it at the same pinned revision so RUAccent.load()
    # does not fall back to mutable Hub main.
    module_dir = Path(ruaccent_package.__file__).resolve().parent
    snapshot_download(
        repo_id=RUACCENT_REPO,
        revision=RUACCENT_REVISION,
        allow_patterns=["koziev/**"],
        local_dir=module_dir,
    )


def load_ruaccent(workdir: Path | None = None) -> RUAccent:
    if workdir is None:
        cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        workdir = cache / "xvibe-pocket-tts" / "ruaccent" / RUACCENT_REVISION
    _prefetch_resources(workdir)
    accentizer = RUAccent()
    accentizer.load(
        omograph_model_size=RUACCENT_MODEL_SIZE,
        use_dictionary=True,
        device="CPU",
        workdir=str(workdir),
        tiny_mode=False,
    )
    return accentizer
