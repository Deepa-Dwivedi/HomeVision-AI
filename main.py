from datetime import datetime
from pathlib import Path
from app.database import(
create_predictions_table,
save_prediction,get_predictions,
get_dashboard_stats,
search_predictions,
get_zip_summary,
get_prediction_trend,
filter_predictions,
get_prediction_by_id,
)
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv
from io import StringIO



BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "house_price_model.pkl"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="AI House Price Predictor",
    description=(
        "Predict house prices using ZIP code "
        "and property characteristics."
    ),
    version="2.0.0",
)
@app.on_event("startup")
def startup():
    create_predictions_table()


app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "The trained model was not found. "
        "Run 'py model\\train_model.py' first."
    )


model = joblib.load(MODEL_PATH)


ZIP_CODES = [
    "78701",
    "78759",
    "78613",
    "78664",
    "78626",
    "78660",
]


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "zip_codes": ZIP_CODES,
            "prediction": None,
            "price_range": None,
            "error": None,
            "selected_zip": None,
            "square_feet": None,
            "bedrooms": None,
            "bathrooms": None,
            "year_built": None,
            "lot_size": None,

        },
    )


@app.post("/predict", response_class=HTMLResponse)
def predict(
    request: Request,
    zip_code: str = Form(...),
    square_feet: int = Form(...),
    bedrooms: int = Form(...),
    bathrooms: int = Form(...),
    year_built: int = Form(...),
    lot_size: int = Form(...),
):
    error = None
    prediction = None
    price_range = None

    if zip_code not in ZIP_CODES:
        error = "Please select a valid ZIP code."
    elif square_feet < 300:
        error = "Square feet must be at least 300."
    elif bedrooms < 1:
        error = "Bedrooms must be at least 1."
    elif bathrooms < 1:
        error = "Bathrooms must be at least 1."
    elif year_built < 1800 or year_built > 2026:
        error = "Please enter a valid year built."
    elif lot_size < 500:
        error = "Lot size must be at least 500 square feet."
    else:
      input_data = pd.DataFrame(
        [{
            "zip_code": zip_code,
            "square_feet": square_feet,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "year_built": year_built,
            "lot_size": lot_size,
        }]
    )

    predicted_price = model.predict(input_data)[0]

    save_prediction(
        zip_code,
        square_feet,
        bedrooms,
        bathrooms,
        year_built,
        lot_size,
        float(predicted_price),
    )

    transformed_data = model.named_steps["preprocessor"].transform(input_data)

    tree_predictions = np.array([
        tree.predict(transformed_data)[0]
        for tree in model.named_steps["model"].estimators_
    ])

    lower_price = np.percentile(tree_predictions, 10)
    upper_price = np.percentile(tree_predictions, 90)

    prediction = f"${predicted_price:,.0f}"
    price_range = f"${lower_price:,.0f} - ${upper_price:,.0f}"

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "zip_codes": ZIP_CODES,
            "prediction": prediction,
            "price_range": price_range,
            "error": error,
            "selected_zip": zip_code,
            "square_feet": square_feet,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "year_built": year_built,
            "lot_size": lot_size,
        },
        status_code=400 if error else 200,
    )
@app.get("/history", response_class=HTMLResponse)
def history(
    request: Request,
    zip_code: str | None = None,
    bedrooms: int | None = None,
    bathrooms: int | None = None,
    year_built: int | None = None,
):
    stats = get_dashboard_stats()
    zip_summary = get_zip_summary()
    trend_data = get_prediction_trend()

    trend_labels = [
        datetime.strptime(
            row["created_at"],
            "%Y-%m-%d %H:%M:%S",
        ).strftime("%b %d, %I:%M %p")
        for row in trend_data
    ]

    trend_prices = [
        float(row["predicted_price"])
        for row in trend_data
    ]

    predictions = filter_predictions(
        zip_code=zip_code.strip() if zip_code else None,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        year_built=year_built,
    )

    zip_labels = [
        row["zip_code"]
        for row in zip_summary
    ]

    zip_prices = [
        float(row["average_price"])
        for row in zip_summary
    ]

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "predictions": predictions,
            "stats": stats,
            "zip_summary": zip_summary,
            "zip_labels": zip_labels,
            "zip_prices": zip_prices,
            "trend_labels": trend_labels,
            "trend_prices": trend_prices,

            # Keep selected filter values
            "search_zip": zip_code,
            "selected_bedrooms": bedrooms,
            "selected_bathrooms": bathrooms,
            "selected_year": year_built,
        },
    )
@app.get(
    "/prediction/{prediction_id}",
    response_class=HTMLResponse,
)
def prediction_details(
    request: Request,
    prediction_id: int,
):
    prediction = get_prediction_by_id(prediction_id)

    if prediction is None:
        return templates.TemplateResponse(
            request=request,
            name="prediction_details.html",
            context={
                "prediction": None,
                "error": "Prediction not found.",
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="prediction_details.html",
        context={
            "prediction": prediction,
            "error": None,
        },
    )
@app.get("/export-csv")
def export_csv(
    zip_code: str | None = None,
    bedrooms: int | None = None,
    bathrooms: int | None = None,
    year_built: int | None = None,
):
    predictions = filter_predictions(
        zip_code=zip_code.strip() if zip_code else None,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        year_built=year_built,
    )

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "ID",
            "Created At",
            "ZIP Code",
            "Square Feet",
            "Bedrooms",
            "Bathrooms",
            "Year Built",
            "Lot Size",
            "Predicted Price",
        ]
    )

    for item in predictions:
        writer.writerow(
            [
                item["id"],
                item["created_at"],
                item["zip_code"],
                item["square_feet"],
                item["bedrooms"],
                item["bathrooms"],
                item["year_built"],
                item["lot_size"],
                item["predicted_price"],
            ]
        )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="predictions.csv"'
        },
    )
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": "model/house_price_model.pkl",
    }
