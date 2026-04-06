"""
data/download_datasets.py — Auto-download datasets from Kaggle API
"""
from __future__ import annotations
import os
import json
import zipfile
from pathlib import Path
from backend.core.config import settings
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

RAW_DIR = settings.data_dir / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle dataset slugs to download
DATASETS = [
    {
        "slug": "gauravduttakiit/resume-dataset",
        "description": "Resume Dataset (2400+ resumes across 25 categories)",
    },
    {
        "slug": "snehaanbhawal/resume-dataset",
        "description": "Updated Resume DataSet (multi-category)",
    },
    {
        "slug": "arshkon/linkedin-job-postings",
        "description": "LinkedIn Job Postings (~30k entries)",
    },
]


def configure_kaggle():
    """Configure Kaggle credentials from env vars or settings."""
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"

    # Use settings values if kaggle.json doesn't exist
    if not kaggle_json.exists() and settings.kaggle_username and settings.kaggle_key:
        kaggle_dir.mkdir(exist_ok=True)
        creds = {
            "username": settings.kaggle_username,
            "key": settings.kaggle_key,
        }
        kaggle_json.write_text(json.dumps(creds))
        kaggle_json.chmod(0o600)
        logger.info("Created ~/.kaggle/kaggle.json from settings")

    if not kaggle_json.exists():
        raise RuntimeError(
            "Kaggle credentials not found. Set KAGGLE_USERNAME and KAGGLE_KEY "
            "in your .env file, or place kaggle.json in ~/.kaggle/"
        )
    os.environ["KAGGLE_CONFIG_DIR"] = str(kaggle_dir)


def download_all(force: bool = False) -> dict[str, bool]:
    """
    Download all configured datasets.

    Args:
        force: Re-download even if already present.

    Returns:
        Dict mapping dataset slug → success bool.
    """
    configure_kaggle()

    try:
        import kaggle  # noqa: F401 (triggers auth)
        from kaggle.api.kaggle_api_extended import KaggleApiExtended
        api = KaggleApiExtended()
        api.authenticate()
    except Exception as exc:
        logger.error("Kaggle API authentication failed", error=str(exc))
        raise

    results: dict[str, bool] = {}
    for dataset in DATASETS:
        slug = dataset["slug"]
        dest = RAW_DIR / slug.replace("/", "_")
        if dest.exists() and not force:
            logger.info("Dataset already downloaded, skipping", slug=slug)
            results[slug] = True
            continue

        try:
            logger.info("Downloading dataset", slug=slug, description=dataset["description"])
            dest.mkdir(parents=True, exist_ok=True)
            api.dataset_download_files(slug, path=str(dest), unzip=True, quiet=False)
            logger.info("Download complete", slug=slug, path=str(dest))
            results[slug] = True
        except Exception as exc:
            logger.error("Dataset download failed", slug=slug, error=str(exc))
            results[slug] = False

    return results


def list_downloaded() -> list[Path]:
    """Return list of downloaded dataset directories."""
    if not RAW_DIR.exists():
        return []
    return [p for p in RAW_DIR.iterdir() if p.is_dir()]


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    results = download_all(force=force)
    for slug, ok in results.items():
        status = "✅ Success" if ok else "❌ Failed"
        print(f"{status}: {slug}")
