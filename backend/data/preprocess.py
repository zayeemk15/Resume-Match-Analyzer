"""
data/preprocess.py — Clean and preprocess downloaded datasets
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
from backend.core.config import settings
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

RAW_DIR  = settings.data_dir / "raw"
PROC_DIR = settings.data_dir / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def process_resume_dataset() -> pd.DataFrame | None:
    """Process Kaggle resume dataset → clean parquet."""
    # Try known CSV names from both Kaggle resume datasets
    candidates = [
        *RAW_DIR.rglob("*.csv"),
        *RAW_DIR.rglob("UpdatedResumeDataSet.csv"),
        *RAW_DIR.rglob("resume_dataset.csv"),
    ]
    if not candidates:
        logger.warning("No resume CSV found in raw/")
        return None

    dfs = []
    for csv_path in candidates[:3]:      # limit to 3 files
        try:
            df = pd.read_csv(csv_path, encoding="utf-8", errors="replace")
            # Normalize column names
            df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
            # Look for text column
            text_col = next(
                (c for c in df.columns if "resume" in c or "text" in c or "cv" in c),
                df.columns[0],
            )
            label_col = next(
                (c for c in df.columns if "category" in c or "label" in c or "job" in c),
                None,
            )
            out = pd.DataFrame({"text": df[text_col].astype(str)})
            if label_col:
                out["category"] = df[label_col]
            out["text"] = out["text"].apply(_clean_text)
            out = out[out["text"].str.len() > 100]
            dfs.append(out)
            logger.info("Loaded resume CSV", path=str(csv_path), rows=len(out))
        except Exception as exc:
            logger.warning("Could not load CSV", path=str(csv_path), error=str(exc))

    if not dfs:
        return None

    combined = pd.concat(dfs, ignore_index=True).drop_duplicates(subset="text")
    out_path = PROC_DIR / "resumes.parquet"
    combined.to_parquet(out_path, index=False)
    logger.info("Resume dataset saved", path=str(out_path), rows=len(combined))
    return combined


def process_jd_dataset() -> pd.DataFrame | None:
    """Process job posting dataset → clean parquet."""
    jd_candidates = list(RAW_DIR.rglob("job_postings.csv")) + list(RAW_DIR.rglob("linkedin*.csv"))
    if not jd_candidates:
        logger.warning("No JD CSV found in raw/")
        return None

    dfs = []
    for csv_path in jd_candidates[:2]:
        try:
            df = pd.read_csv(csv_path, encoding="utf-8", errors="replace", nrows=50_000)
            df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
            text_col = next(
                (c for c in df.columns if "description" in c or "text" in c or "summary" in c),
                df.columns[0],
            )
            title_col = next((c for c in df.columns if "title" in c), None)
            out = pd.DataFrame({"description": df[text_col].astype(str)})
            if title_col:
                out["title"] = df[title_col]
            out["description"] = out["description"].apply(_clean_text)
            out = out[out["description"].str.len() > 100]
            dfs.append(out)
            logger.info("Loaded JD CSV", path=str(csv_path), rows=len(out))
        except Exception as exc:
            logger.warning("Could not load JD CSV", path=str(csv_path), error=str(exc))

    if not dfs:
        return None

    combined = pd.concat(dfs, ignore_index=True).drop_duplicates(subset="description")
    out_path = PROC_DIR / "job_descriptions.parquet"
    combined.to_parquet(out_path, index=False)
    logger.info("JD dataset saved", path=str(out_path), rows=len(combined))
    return combined


def run_all():
    """Run full preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    resumes = process_resume_dataset()
    jds     = process_jd_dataset()
    logger.info(
        "Preprocessing complete",
        resume_rows=len(resumes) if resumes is not None else 0,
        jd_rows    =len(jds)     if jds     is not None else 0,
    )


if __name__ == "__main__":
    run_all()
