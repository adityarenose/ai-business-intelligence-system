"""Customer churn forecasting and model pipeline management.

The module trains logistic regression and random forest models, evaluates their
performance on the business churn problem, selects the preferred model, and
exposes a reusable prediction function.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.analytics import load_business_data
from src.feature_engineering import build_customer_features, get_feature_matrix

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RISK_THRESHOLDS = {
    "Low": 0.30,
    "Medium": 0.60,
    "High": 0.80,
}


@dataclass
class ModelMetadata:
    training_date: str
    features: list[str]
    evaluation_metrics: dict[str, Any]
    selected_model: str
    risk_thresholds: dict[str, float]


class ChurnModelPipeline:
    """Wrapper around the churn training and prediction pipeline."""

    def __init__(self, risk_thresholds: dict[str, float] | None = None):
        self.risk_thresholds = risk_thresholds or RISK_THRESHOLDS.copy()
        self.pipeline = None
        self.feature_names = []
        self.model_name = ""
        self.metadata: dict[str, Any] | None = None
        self.training_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _build_pipeline(self, X: pd.DataFrame) -> Pipeline:
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = [col for col in X.columns if col not in numeric_features]

        preprocessor_steps = []
        if numeric_features:
            preprocessor_steps.append(
                (
                    "numeric",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    numeric_features,
                )
            )
        if categorical_features:
            preprocessor_steps.append(
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    categorical_features,
                )
            )

        if not preprocessor_steps:
            raise ValueError("No valid feature columns available for model training.")

        transformer = ColumnTransformer(
            transformers=preprocessor_steps,
            remainder="drop",
        )
        return Pipeline(steps=[("preprocessor", transformer), ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced"))])

    def _build_random_forest_pipeline(self, X: pd.DataFrame) -> Pipeline:
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = [col for col in X.columns if col not in numeric_features]

        preprocessor_steps = []
        if numeric_features:
            preprocessor_steps.append(("numeric", SimpleImputer(strategy="median"), numeric_features))
        if categorical_features:
            preprocessor_steps.append(
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    categorical_features,
                )
            )

        transformer = ColumnTransformer(transformers=preprocessor_steps, remainder="drop")
        return Pipeline(
            steps=[
                ("preprocessor", transformer),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=5,
                        random_state=42,
                        class_weight="balanced_subsample",
                    ),
                ),
            ]
        )

    def _evaluate_model(self, y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        metrics = {
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
            "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        }
        return metrics

    def train(self, feature_df: pd.DataFrame) -> dict[str, Any]:
        X, y, feature_names = get_feature_matrix(feature_df)
        self.feature_names = feature_names

        X_development, X_test, y_development, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )
        X_train, X_validation, y_train, y_validation = train_test_split(
            X_development,
            y_development,
            test_size=0.25,
            random_state=42,
            stratify=y_development,
        )

        models = {
            "logistic_regression": self._build_pipeline(X_train),
            "random_forest": self._build_random_forest_pipeline(X_train),
        }

        validation_results: dict[str, Any] = {}
        for name, estimator in models.items():
            estimator.fit(X_train, y_train)
            y_pred = estimator.predict(X_validation)
            y_prob = estimator.predict_proba(X_validation)[:, 1]
            validation_results[name] = self._evaluate_model(y_validation, y_pred, y_prob)

        selected_model = "random_forest" if validation_results["random_forest"]["f1_score"] >= validation_results["logistic_regression"]["f1_score"] else "logistic_regression"

        # Refit each candidate on all development data, then report holdout metrics.
        final_models = {
            "logistic_regression": self._build_pipeline(X_development),
            "random_forest": self._build_random_forest_pipeline(X_development),
        }
        results: dict[str, Any] = {}
        for name, estimator in final_models.items():
            estimator.fit(X_development, y_development)
            y_pred = estimator.predict(X_test)
            y_prob = estimator.predict_proba(X_test)[:, 1]
            results[name] = self._evaluate_model(y_test, y_pred, y_prob)

        if selected_model == "random_forest":
            best_estimator = final_models["random_forest"]
        else:
            best_estimator = final_models["logistic_regression"]

        self.pipeline = best_estimator
        self.model_name = selected_model
        self.metadata = ModelMetadata(
            training_date=self.training_date,
            features=self.feature_names,
            evaluation_metrics=results,
            selected_model=selected_model,
            risk_thresholds=self.risk_thresholds,
        )
        return results

    def save(self, model_path: str | Path | None = None) -> str:
        if self.pipeline is None:
            raise ValueError("No trained pipeline to save.")

        path = Path(model_path) if model_path is not None else MODEL_DIR / "churn_model.pkl"
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path = path.with_suffix(".metadata.json")

        with open(path, "wb") as file:
            pickle.dump({
                "pipeline": self.pipeline,
                "feature_names": self.feature_names,
                "metadata": self.metadata,
                "risk_thresholds": self.risk_thresholds,
            }, file)

        metadata_payload = {
            "training_date": self.metadata.training_date if self.metadata else self.training_date,
            "features": self.feature_names,
            "evaluation_metrics": self.metadata.evaluation_metrics if self.metadata else {},
            "selected_model": self.model_name or (self.metadata.selected_model if self.metadata else "unknown"),
            "risk_thresholds": self.risk_thresholds,
        }
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata_payload, file, indent=2)

        return str(path)

    def load(self, model_path: str | Path) -> None:
        with open(model_path, "rb") as file:
            bundle = pickle.load(file)
        self.pipeline = bundle["pipeline"]
        self.feature_names = bundle["feature_names"]
        self.metadata = bundle["metadata"]
        self.risk_thresholds = bundle.get("risk_thresholds", self.risk_thresholds)
        self.model_name = self.metadata.selected_model if hasattr(self.metadata, "selected_model") else "loaded_model"

    def predict_proba(self, customer_input: dict[str, Any] | pd.DataFrame) -> np.ndarray:
        if self.pipeline is None:
            raise ValueError("Model has not been trained or loaded.")
        if isinstance(customer_input, dict):
            row = pd.DataFrame([customer_input])
        else:
            row = customer_input.copy()

        if "segment" not in row.columns and "customer_segment" in row.columns:
            row = row.rename(columns={"customer_segment": "segment"})

        if not self.feature_names:
            raise ValueError("Feature names were not set on the model.")

        missing = [feature for feature in self.feature_names if feature not in row.columns]
        if missing:
            raise ValueError(f"Missing required input features: {missing}")

        row = row[self.feature_names]
        return self.pipeline.predict_proba(row)[:, 1]

    def predict_risk(self, customer_input: dict[str, Any] | pd.DataFrame) -> dict[str, Any]:
        probability = float(self.predict_proba(customer_input)[0])

        if probability < self.risk_thresholds["Low"]:
            risk_level = "Low"
        elif probability < self.risk_thresholds["High"]:
            risk_level = "Medium"
        else:
            risk_level = "High"

        predicted_class = 1 if probability >= self.risk_thresholds["Medium"] else 0
        return {
            "churn_probability": round(probability, 4),
            "predicted_class": int(predicted_class),
            "risk_level": risk_level,
        }


def load_model(model_path: str | Path | None = None) -> ChurnModelPipeline:
    if model_path is None:
        model_path = MODEL_DIR / "churn_model.pkl"

    pipeline = ChurnModelPipeline()
    pipeline.load(model_path)
    return pipeline


def train_churn_model() -> tuple[ChurnModelPipeline, dict[str, Any]]:
    data = load_business_data()
    churn_df = build_customer_features(
        customers_df=data["customers"],
        orders_df=data["orders"],
        order_items_df=data["order_items"],
        products_df=data["products"],
    )

    model = ChurnModelPipeline()
    metrics = model.train(churn_df)
    model.save()
    return model, metrics


def predict_churn(customer_data: dict[str, Any]) -> dict[str, Any]:
    """Return churn probability, prediction, and risk level for a single customer.

    The function loads the saved model and predicts churn for a customer record.
    """
    model = load_model()
    return model.predict_risk(customer_data)


def export_model_metadata(model: ChurnModelPipeline) -> dict[str, Any]:
    """Return a dictionary containing model metadata for display or API responses."""
    if model.metadata is None:
        raise ValueError("Model metadata is not available. Train the model first.")
    return {
        "training_date": model.metadata.training_date,
        "features": model.metadata.features,
        "evaluation_metrics": model.metadata.evaluation_metrics,
        "selected_model": model.metadata.selected_model,
        "risk_thresholds": model.metadata.risk_thresholds,
    }


if __name__ == "__main__":
    model, metrics = train_churn_model()
    print("Selected model:", model.model_name)
    print(json.dumps(metrics, indent=2, default=str))
    sample = {
        "customer_id": 999999,
        "age": 31,
        "gender": "Female",
        "city": "Bengaluru",
        "tenure_months": 7,
        "monthly_spend": 3500,
        "support_calls": 6,
        "purchase_frequency": 1.2,
        "total_orders": 2,
        "total_spent": 4200,
        "avg_order_value": 2100,
        "payment_method": "UPI",
        "segment": "At Risk",
        "churn": 0,
    }
    print("Prediction:", predict_churn(sample))
