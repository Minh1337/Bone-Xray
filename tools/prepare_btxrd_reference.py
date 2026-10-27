"""Prepare a provenance-rich, local BTXRD image reference manifest.

The images and generated manifest remain under data/external_datasets (Git-ignored).
This tool does not assign train/validation/test membership and does not evaluate a
checkpoint. BTXRD is also named in the current checkpoint's training configuration.
"""

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd


EXPECTED_MD5 = "59132a5036d030580ccade8add8f13df"
EXPECTED_SIZE = 840_474_929
DATASET_DOI = "10.6084/m9.figshare.27865398.v1"
DATASET_URL = (
    "https://figshare.com/articles/dataset/"
    "A_Radiograph_Dataset_for_the_Classification_Localization_and_Segmentation_of_Primary_Bone_Tumors/27865398"
)
LICENSE = "CC BY 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
ATTRIBUTION = (
    "Yao et al. A Radiograph Dataset for the Classification, Localization, and "
    "Segmentation of Primary Bone Tumors. Scientific Data 12, 88 (2025). "
    "https://doi.org/10.1038/s41597-024-04311-y; dataset DOI: " + DATASET_DOI
)
LABELS = [
    "no-tumor", "osteochondroma", "multiple osteochondromas", "simple bone cyst",
    "giant cell tumor", "osteofibroma", "synovial osteochondroma", "other bt",
    "osteosarcoma", "other mt",
]
SUBTYPE_COLUMNS = {
    "osteochondroma": "osteochondroma",
    "multiple osteochondromas": "multiple osteochondromas",
    "simple bone cyst": "simple bone cyst",
    "giant cell tumor": "giant cell tumor",
    "osteofibroma": "osteofibroma",
    "synovial osteochondroma": "synovial osteochondroma",
    "other bt": "other bt",
    "osteosarcoma": "osteosarcoma",
    "other mt": "other mt",
}
META_COLUMNS = [
    "age", "gender", "hand", "ulna", "radius", "humerus", "foot", "tibia",
    "fibula", "femur", "hip bone", "ankle-joint", "knee-joint", "hip-joint",
    "elbow-joint", "shoulder-joint", "upper limb", "lower limb", "pelvis",
    "frontal", "lateral", "oblique",
]


def normalized_column(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path):
    digest = hashlib.md5(usedforsecurity=False)
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_extract(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = (destination / info.filename).resolve()
            if target != destination and destination not in target.parents:
                raise ValueError(f"Unsafe archive path: {info.filename}")
        zf.extractall(destination)


def read_table(root):
    files = list(Path(root).rglob("dataset.csv"))
    if files:
        return pd.read_csv(files[0], dtype=object), files[0]
    files = list(Path(root).rglob("dataset.xlsx")) + list(Path(root).rglob("dataset.xls"))
    if files:
        return pd.read_excel(files[0], dtype=object), files[0]
    raise FileNotFoundError("BTXRD archive has no dataset.csv or dataset.xlsx")


def binary(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip().casefold()
        if value in {"1", "1.0", "true", "yes"}:
            return 1
        if value in {"0", "0.0", "false", "no"}:
            return 0
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number in (0, 1) else None


def resolve_label(row, columns):
    tumor_col = columns.get("tumor")
    tumor = binary(row[tumor_col]) if tumor_col is not None else None
    active = []
    for label, column_name in SUBTYPE_COLUMNS.items():
        column = columns.get(normalized_column(column_name))
        if column is not None and binary(row[column]) == 1:
            active.append(label)
    if len(active) == 1:
        if tumor == 0:
            return "", "conflicting_normal_and_tumor_labels"
        return active[0], "ok"
    if tumor == 0 and active:
        return "", "conflicting_normal_and_tumor_labels"
    if tumor == 0:
        return "no-tumor", "ok"
    if len(active) > 1:
        return "", "multiple_subtype_labels"
    if tumor == 1:
        return "", "tumor_subtype_missing_or_unknown"
    return "", "tumor_presence_missing"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/external_datasets/BTXRD/BTXRD.zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/external_datasets/BTXRD/reference"))
    args = parser.parse_args()
    archive = args.archive.resolve()
    if archive.stat().st_size != EXPECTED_SIZE:
        raise ValueError(f"Unexpected archive size: {archive.stat().st_size}")
    archive_md5 = md5(archive)
    if archive_md5 != EXPECTED_MD5:
        raise ValueError(f"Figshare MD5 mismatch: {archive_md5}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    extracted = args.output_dir / "source"
    table, table_path = read_table(extracted) if extracted.exists() else (None, None)
    if table is None:
        safe_extract(archive, extracted)
        table, table_path = read_table(extracted)

    columns = {normalized_column(column): column for column in table.columns}
    image_column = next((columns[key] for key in ("image id", "image id jpeg", "filename", "file name")
                         if key in columns), None)
    if image_column is None:
        raise ValueError(f"Could not identify image ID column in {list(table.columns)}")
    image_paths = {path.name.casefold(): path for path in extracted.rglob("*")
                   if path.is_file() and path.suffix.casefold() in {".jpg", ".jpeg", ".png"}}
    if not image_paths:
        raise FileNotFoundError("No raster images found in extracted BTXRD archive")

    canonical_meta_columns = {normalized_column(name): name for name in META_COLUMNS}
    required_labels = {normalized_column("tumor"), *(normalized_column(x) for x in SUBTYPE_COLUMNS.values())}
    missing_label_columns = required_labels - set(columns)
    if missing_label_columns:
        raise ValueError(f"Missing source label columns: {sorted(missing_label_columns)}")
    missing_meta_columns = set(canonical_meta_columns) - set(columns)
    rows = []
    seen_ids = set()
    for _, source_row in table.iterrows():
        image_id = Path(str(source_row[image_column])).name
        if image_id.casefold() in seen_ids:
            raise ValueError(f"Duplicate image ID in source metadata: {image_id}")
        seen_ids.add(image_id.casefold())
        image = image_paths.get(image_id.casefold())
        if image is None:
            stem = Path(image_id).stem.casefold()
            image = next((p for name, p in image_paths.items() if Path(name).stem.casefold() == stem), None)
        if image is None:
            raise FileNotFoundError(f"No archive image found for metadata row: {image_id}")
        label, label_status = resolve_label(source_row, columns)
        metadata = {}
        metadata_errors = []
        for normalized, canonical in canonical_meta_columns.items():
            column = columns.get(normalized)
            if column is None:
                metadata_errors.append(f"missing_column:{canonical}")
                continue
            value = source_row[column]
            if canonical == "age":
                try:
                    number = float(value)
                    if not (0 <= number <= 120):
                        raise ValueError
                    metadata[canonical] = number
                except (TypeError, ValueError):
                    metadata_errors.append("invalid_age")
            elif canonical == "gender":
                gender = str(value).strip().upper()
                if gender not in {"M", "F"}:
                    metadata_errors.append("invalid_gender")
                else:
                    metadata[canonical] = gender
            else:
                value = binary(value)
                if value is None:
                    metadata_errors.append(f"invalid_binary:{canonical}")
                else:
                    metadata[canonical] = value
        center_col = columns.get("center")
        image_hash = sha256(image)
        group_col = next((columns[key] for key in ("patient id", "lesion id", "case id")
                          if key in columns and not pd.isna(source_row[columns[key]])), None)
        group_value = str(source_row[group_col]).strip() if group_col is not None else ""
        group_id = hashlib.sha256((DATASET_DOI + ":" + group_value).encode()).hexdigest() if group_value else "unavailable"
        rows.append({
            "image_id": image_id,
            "relative_path": image.relative_to(extracted).as_posix(),
            "sha256": image_hash,
            "duplicate_group_id": "pending",
            "source_dataset": "BTXRD",
            "source_center": str(source_row[center_col]) if center_col is not None else "unknown",
            "group_id": group_id,
            "partition": "unassigned",
            "independent_of_checkpoint_training": False,
            "ground_truth": label,
            "ground_truth_status": label_status,
            "metadata_json": json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            "metadata_status": "ok" if not metadata_errors else ";".join(metadata_errors),
            "license": LICENSE,
            "license_url": LICENSE_URL,
            "dataset_doi": DATASET_DOI,
            "attribution": ATTRIBUTION,
        })

    hashes = [row["sha256"] for row in rows]
    counts_by_hash = Counter(hashes)
    for row in rows:
        row["duplicate_group_id"] = "sha256:" + row["sha256"] if counts_by_hash[row["sha256"]] > 1 else "unique:" + row["sha256"]
    manifest = args.output_dir / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False, encoding="utf-8")
    counts = {label: sum(row["ground_truth"] == label and row["ground_truth_status"] == "ok"
                         for row in rows) for label in LABELS}
    summary = {
        "dataset": "BTXRD",
        "dataset_doi": DATASET_DOI,
        "official_url": DATASET_URL,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "attribution": ATTRIBUTION,
        "archive_name": archive.name,
        "archive_size": archive.stat().st_size,
        "archive_md5_figshare": archive_md5,
        "archive_sha256": sha256(archive),
        "metadata_file": table_path.relative_to(extracted).as_posix(),
        "image_count": len(rows),
        "label_counts": counts,
        "unmapped_label_count": sum(row["ground_truth_status"] != "ok" for row in rows),
        "metadata_valid_count": sum(row["metadata_status"] == "ok" for row in rows),
        "patient_or_lesion_group_ids_available": any(row["group_id"] != "unavailable" for row in rows),
        "exact_duplicate_groups": sum(count > 1 for count in counts_by_hash.values()),
        "images_in_exact_duplicate_groups": sum(count for count in counts_by_hash.values() if count > 1),
        "split_status": "unassigned; no patient IDs or checkpoint split IDs were recovered",
        "evaluation_eligibility": "development/reference only; checkpoint training used BTXRD source",
        "manifest": manifest.name,
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
