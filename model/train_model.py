from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# Project paths
MODEL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = MODEL_DIR.parent

DATA_PATH = PROJECT_DIR / "housing_data.csv"
MODEL_PATH = MODEL_DIR / "house_price_model.pkl"


# Load data
df = pd.read_csv(
    DATA_PATH,
    dtype={"zip_code": str},
)


features = [
    "zip_code",
    "square_feet",
    "bedrooms",
    "bathrooms",
    "year_built",
    "lot_size",
]

X = df[features]
y = df["price"]


categorical_features = ["zip_code"]

numeric_features = [
    "square_feet",
    "bedrooms",
    "bathrooms",
    "year_built",
    "lot_size",
]


preprocessor = ColumnTransformer(
    transformers=[
        (
            "zip_encoder",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
        (
            "numeric",
            "passthrough",
            numeric_features,
        ),
    ]
)


pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "model",
            RandomForestRegressor(
                n_estimators=300,
                random_state=42,
            ),
        ),
    ]
)


pipeline.fit(X, y)

joblib.dump(pipeline, MODEL_PATH)


sample_house = pd.DataFrame(
    [
        {
            "zip_code": "78613",
            "square_feet": 2200,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 2018,
            "lot_size": 7500,
        }
    ]
)

sample_prediction = pipeline.predict(sample_house)[0]


print("Model trained successfully.")
print(f"Model saved at: {MODEL_PATH}")
print(f"Sample prediction: ${sample_prediction:,.2f}")