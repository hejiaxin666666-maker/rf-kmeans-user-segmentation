"""CSV loading with header detection and chunked parsing."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Iterator

import pandas as pd

from .preprocessing import EXPECTED_COLUMNS, clean_behavior_frame


Source = str | Path | bytes | bytearray | BinaryIO


def _to_rewindable_source(source: Source):
    if isinstance(source, (bytes, bytearray)):
        return BytesIO(bytes(source))
    if hasattr(source, "read"):
        try:
            source.seek(0)
            return source
        except (AttributeError, OSError):
            return BytesIO(source.read())
    return source


def _source_has_header(source: Source) -> bool:
    reader = _to_rewindable_source(source)
    try:
        header = pd.read_csv(reader, nrows=0, encoding="utf-8-sig")
        names = [str(column).strip() for column in header.columns]
        return names == EXPECTED_COLUMNS
    except (pd.errors.ParserError, UnicodeDecodeError):
        return False
    finally:
        if hasattr(reader, "seek"):
            reader.seek(0)


def read_behavior_chunks(source: Source, chunksize: int = 100_000) -> Iterator[pd.DataFrame]:
    """Yield cleaned behavior chunks from a headered or headerless CSV source."""

    if chunksize < 1:
        raise ValueError("chunksize 必须大于 0")
    reader = _to_rewindable_source(source)
    has_header = _source_has_header(reader)
    if hasattr(reader, "seek"):
        reader.seek(0)
    csv_chunks = pd.read_csv(
        reader,
        header=0 if has_header else None,
        names=None if has_header else EXPECTED_COLUMNS,
        encoding="utf-8-sig",
        chunksize=chunksize,
        low_memory=False,
    )
    for chunk in csv_chunks:
        cleaned, _ = clean_behavior_frame(chunk)
        if not cleaned.empty:
            yield cleaned


def load_behavior_data(source: Source, chunksize: int = 100_000) -> tuple[pd.DataFrame, dict]:
    """Load all cleaned chunks and combine their quality reports."""

    total_report = {
        "input_rows": 0,
        "cleaned_rows": 0,
        "removed_rows": 0,
        "duplicate_rows": 0,
        "empty_user_rows": 0,
        "invalid_timestamp_rows": 0,
        "invalid_behavior_rows": 0,
        "min_timestamp": None,
        "max_timestamp": None,
    }
    cleaned_chunks: list[pd.DataFrame] = []

    reader = _to_rewindable_source(source)
    has_header = _source_has_header(reader)
    if hasattr(reader, "seek"):
        reader.seek(0)
    csv_chunks = pd.read_csv(
        reader,
        header=0 if has_header else None,
        names=None if has_header else EXPECTED_COLUMNS,
        encoding="utf-8-sig",
        chunksize=chunksize,
        low_memory=False,
    )
    for chunk in csv_chunks:
        cleaned, report = clean_behavior_frame(chunk)
        for key in (
            "input_rows",
            "cleaned_rows",
            "removed_rows",
            "duplicate_rows",
            "empty_user_rows",
            "invalid_timestamp_rows",
            "invalid_behavior_rows",
        ):
            total_report[key] += int(report[key])
        for key in ("min_timestamp", "max_timestamp"):
            value = report[key]
            if value is None:
                continue
            if total_report[key] is None:
                total_report[key] = value
            elif key == "min_timestamp":
                total_report[key] = min(total_report[key], value)
            else:
                total_report[key] = max(total_report[key], value)
        if not cleaned.empty:
            cleaned_chunks.append(cleaned)

    if cleaned_chunks:
        combined = pd.concat(cleaned_chunks, ignore_index=True)
        cross_chunk_duplicates = combined.duplicated(keep="first")
        cross_chunk_duplicate_count = int(cross_chunk_duplicates.sum())
        if cross_chunk_duplicate_count:
            combined = combined.loc[~cross_chunk_duplicates].reset_index(drop=True)
            total_report["duplicate_rows"] += cross_chunk_duplicate_count
            total_report["cleaned_rows"] = int(len(combined))
            total_report["removed_rows"] = int(total_report["input_rows"] - len(combined))
    else:
        combined = pd.DataFrame(columns=EXPECTED_COLUMNS)
    return combined, total_report
