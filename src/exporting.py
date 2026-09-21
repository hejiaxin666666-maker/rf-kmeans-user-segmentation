"""Downloadable analysis result packaging."""

from __future__ import annotations

import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .pipeline import AnalysisResult
from .visualization import save_static_figures


def build_results_zip(result: AnalysisResult, output_dir: str | Path) -> bytes:
    """Return CSV, JSON, and PNG outputs as an in-memory ZIP archive."""

    directory = Path(output_dir)
    output_root = directory.parent if directory.name.lower() == "figures" else directory
    output_root.mkdir(parents=True, exist_ok=True)
    figure_paths = save_static_figures(result, directory)
    metadata = json.dumps(result.metadata | {"quality_report": result.quality_report}, ensure_ascii=False, indent=2)
    result.user_features.to_csv(output_root / "user_rf_features.csv", index=False, encoding="utf-8-sig")
    result.cluster_summary.to_csv(output_root / "cluster_summary.csv", index=False, encoding="utf-8-sig")
    (output_root / "run_metadata.json").write_text(metadata, encoding="utf-8")
    archive = io.BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("user_rf_features.csv", result.user_features.to_csv(index=False).encode("utf-8-sig"))
        zip_file.writestr("cluster_summary.csv", result.cluster_summary.to_csv(index=False).encode("utf-8-sig"))
        zip_file.writestr("run_metadata.json", metadata.encode("utf-8"))
        for filename in figure_paths.values():
            zip_file.write(directory / filename, arcname=f"figures/{filename}")
    return archive.getvalue()
