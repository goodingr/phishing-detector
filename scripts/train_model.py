from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline phishing detector.")
    parser.add_argument(
        "--input-path",
        default=Path("data/processed/combined_emails.parquet"),
        type=Path,
        help="Path to consolidated dataset (parquet or csv).",
    )
    parser.add_argument(
        "--text-column",
        default="raw_text",
        help="Column containing raw message text.",
    )
    parser.add_argument(
        "--label-column",
        default="label",
        help="Column containing integer labels (0=safe, 1=phishing).",
    )
    parser.add_argument(
        "--model-output",
        default=Path("models/baseline_tfidf.joblib"),
        type=Path,
        help="Location to store the trained pipeline.",
    )
    parser.add_argument(
        "--metrics-output",
        default=Path("models/baseline_metrics.json"),
        type=Path,
        help="Location to store evaluation metrics.",
    )
    parser.add_argument(
        "--test-size",
        default=0.2,
        type=float,
        help="Proportion of data to reserve for testing.",
    )
    parser.add_argument(
        "--random-state",
        default=42,
        type=int,
        help="Random seed for train/test split and model init.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Optional cap on number of samples for quicker experiments.",
    )
    parser.add_argument(
        "--test-predictions-output",
        default=Path("models/test_predictions.csv"),
        type=Path,
        help="CSV file to record hold-out predictions for inspection.",
    )
    return parser.parse_args()


def load_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file type: {path}")


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=3,
                    max_features=50000,
                    lowercase=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )


def evaluate(
    pipeline: Pipeline,
    X_test: pd.Series,
    y_test: pd.Series,
) -> Dict[str, Any]:
    predictions = pipeline.predict(X_test)
    probabilities = None
    roc_auc = None
    if hasattr(pipeline, "predict_proba"):
        probabilities = pipeline.predict_proba(X_test)[:, 1]
    if probabilities is not None:
        roc_auc = roc_auc_score(y_test, probabilities)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, predictions, average="binary", zero_division=0
    )
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "classification_report": report,
    }


def main() -> None:
    args = parse_args()
    df = load_dataframe(args.input_path)
    df[args.text_column] = df[args.text_column].fillna("").astype(str)
    df[args.label_column] = pd.to_numeric(
        df[args.label_column], errors="coerce"
    ).astype("Int64")
    mask = df[args.label_column].isin([0, 1]) & df[args.text_column].str.len().gt(0)
    df = df.loc[mask].copy()

    if args.max_samples and len(df) > args.max_samples:
        df = df.sample(n=args.max_samples, random_state=args.random_state)

    X_train, X_test, y_train, y_test = train_test_split(
        df[args.text_column],
        df[args.label_column],
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=df[args.label_column],
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    metrics = evaluate(pipeline, X_test, y_test)

    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.model_output)
    args.metrics_output.write_text(json.dumps(metrics, indent=2))

    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(X_test)[:, 1]
    elif hasattr(pipeline, "decision_function"):
        decision = pipeline.decision_function(X_test)
        probs = 1 / (1 + np.exp(-decision))
    else:
        probs = np.full(len(y_test), np.nan, dtype=float)
    predictions = pipeline.predict(X_test)
    report_df = pd.DataFrame(
        {
            "text": X_test.reset_index(drop=True),
            "actual_label": y_test.reset_index(drop=True),
            "predicted_label": predictions,
            "probability_phishing": probs,
        }
    )
    args.test_predictions_output.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(args.test_predictions_output, index=False)

    print(f"Model saved to {args.model_output}")
    print(f"Metrics written to {args.metrics_output}")
    print(
        f"Precision: {metrics['precision']:.3f} | "
        f"Recall: {metrics['recall']:.3f} | F1: {metrics['f1']:.3f} | "
        f"ROC-AUC: {metrics['roc_auc']:.3f}"
    )


if __name__ == "__main__":
    main()
