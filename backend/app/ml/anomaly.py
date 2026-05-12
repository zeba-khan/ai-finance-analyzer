"""
Isolation Forest anomaly detector.
Model is trained on ALL transactions and persisted with joblib.
Re-trains automatically when new transactions are added.
"""
import os
import joblib  # type: ignore[import]
import numpy as np
import pandas as pd  # type: ignore[import]
from sklearn.ensemble import IsolationForest 

MODEL_PATH = os.path.join(os.path.dirname(__file__), "anomaly_model.pkl")


def _build_features(transactions: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hour"] = df["date"].dt.hour.fillna(12)
    df["day"] = df["date"].dt.day.fillna(1)
    df["weekday"] = df["date"].dt.weekday.fillna(0)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    # Rolling stats per category — catches category-specific anomalies
    df["amount_zscore"] = (
        df.groupby("category")["amount"]
        .transform(lambda x: (x - x.mean()) / (x.std() + 1e-9))
        .fillna(0)
    )

    return df[["amount", "hour", "day", "weekday", "amount_zscore"]]


def train_and_save(transactions: list[dict]) -> None:
    """Train Isolation Forest and persist to disk."""
    if len(transactions) < 5:
        return
    features = _build_features(transactions)
    model = IsolationForest(
        contamination=0.1,
        n_estimators=100,
        random_state=42,
        max_samples="auto",
    )
    model.fit(features)
    joblib.dump(model, MODEL_PATH)


def detect(transactions: list[dict]) -> tuple[list[int], list[float]]:
    """
    Returns (anomaly_flags, scores).
    anomaly_flags: 1 = anomaly, 0 = normal
    scores: raw decision function values (lower = more anomalous)
    """
    if len(transactions) < 5:
        return [0] * len(transactions), [0.0] * len(transactions)

    features = _build_features(transactions)

    # Load persisted model or train fresh
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        model = IsolationForest(contamination=0.1, n_estimators=100, random_state=42)
        model.fit(features)
        joblib.dump(model, MODEL_PATH)

    preds = model.predict(features)
    scores = model.decision_function(features)

    flags = [1 if p == -1 else 0 for p in preds]
    return flags, scores.tolist()


def invalidate_model() -> None:
    """Delete cached model so it retrains on next call."""
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
