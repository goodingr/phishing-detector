from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd


CANONICAL_COLUMNS: Sequence[str] = (
    "source",
    "sender",
    "receiver",
    "date",
    "subject",
    "body",
    "urls",
    "raw_text",
    "label",
    "label_text",
)


@dataclass
class DatasetConfig:
    name: str
    rel_path: str
    column_mapping: Dict[str, str] = field(default_factory=dict)
    label_column: str = "label"
    label_map: Dict[str | int, int] | None = None
    raw_text_columns: Sequence[str] | None = None


DATASETS: Sequence[DatasetConfig] = (
    DatasetConfig(
        name="Phishing_Email",
        rel_path="emails/Phishing_Email.csv",
        column_mapping={"Email Text": "raw_text", "Email Type": "label"},
        label_column="label",
        label_map={"Safe Email": 0, "Phishing Email": 1},
    ),
    DatasetConfig(
        name="CEAS_08",
        rel_path="emails2/CEAS_08.csv",
        raw_text_columns=("subject", "body"),
    ),
    DatasetConfig(
        name="Enron",
        rel_path="emails2/Enron.csv",
        raw_text_columns=("subject", "body"),
    ),
    DatasetConfig(
        name="Ling",
        rel_path="emails2/Ling.csv",
        raw_text_columns=("subject", "body"),
    ),
    DatasetConfig(
        name="Nazario",
        rel_path="emails2/Nazario.csv",
        raw_text_columns=("subject", "body"),
    ),
    DatasetConfig(
        name="Nigerian_Fraud",
        rel_path="emails2/Nigerian_Fraud.csv",
        raw_text_columns=("subject", "body"),
    ),
    DatasetConfig(
        name="SpamAssasin",
        rel_path="emails2/SpamAssasin.csv",
        raw_text_columns=("subject", "body"),
    ),
    DatasetConfig(
        name="phishing_email",
        rel_path="emails2/phishing_email.csv",
        column_mapping={"text_combined": "raw_text"},
        raw_text_columns=("raw_text",),
    ),
)


LABEL_TEXT = {0: "safe", 1: "phishing"}


def _load_dataset(config: DatasetConfig, root: Path) -> pd.DataFrame:
    csv_path = root / config.rel_path
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)
    if config.column_mapping:
        df = df.rename(columns=config.column_mapping)
    df["source"] = config.name

    label_col = config.label_column
    if label_col not in df.columns:
        raise KeyError(f"{label_col} missing from {config.name}")

    if config.label_map:
        df["label"] = df[label_col].map(config.label_map)
    else:
        df["label"] = pd.to_numeric(df[label_col], errors="coerce")

    df["label_text"] = df["label"].map(LABEL_TEXT).fillna("unknown")

    df = _ensure_columns(df, CANONICAL_COLUMNS)
    df["raw_text"] = _build_raw_text(df, config)
    df["raw_text"] = (
        df["raw_text"]
        .fillna("")
        .astype(str)
        .str.replace("\r\n", "\n")
        .str.replace("\r", "\n")
        .str.strip()
    )

    return df.loc[df["raw_text"].str.len() > 0, CANONICAL_COLUMNS]


def _ensure_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df


def _build_raw_text(df: pd.DataFrame, config: DatasetConfig) -> pd.Series:
    if config.raw_text_columns:
        parts: List[pd.Series] = []
        for column in config.raw_text_columns:
            if column not in df.columns:
                continue
            part = df[column].fillna("").astype(str).str.strip()
            parts.append(part)
        if parts:
            combined = parts[0]
            for extra in parts[1:]:
                combined = combined.where(extra.eq(""), combined + "\n\n" + extra)
            return combined
    if "raw_text" in df.columns:
        return df["raw_text"]
    if {"subject", "body"}.issubset(df.columns):
        return (
            df["subject"].fillna("").astype(str).str.strip()
            + "\n\n"
            + df["body"].fillna("").astype(str).str.strip()
        )
    raise ValueError(f"Cannot determine raw_text for {config.name}")


def combine_datasets(output_dir: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    frames = [_load_dataset(config, root) for config in DATASETS]
    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["raw_text", "label"])
    dropped = before - len(combined)

    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "combined_emails.parquet"
    csv_path = output_dir / "combined_emails.csv"

    combined.to_parquet(parquet_path, index=False)
    combined.to_csv(csv_path, index=False)

    label_counts = combined["label_text"].value_counts().to_dict()
    print(f"Saved {len(combined):,} records ({dropped:,} duplicates removed).")
    print(f"Label distribution: {label_counts}")
    print(f"Parquet: {parquet_path}")
    print(f"CSV: {csv_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize phishing/safe email CSVs into a single training file."
    )
    parser.add_argument(
        "--output-dir",
        default=Path("data/processed"),
        type=Path,
        help="Folder to store the consolidated dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    combine_datasets(args.output_dir)


if __name__ == "__main__":
    main()
