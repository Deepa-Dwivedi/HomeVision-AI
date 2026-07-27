from pathlib import Path
import sqlite3
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "predictions.db"
def get_connection():
	connection = sqlite3.connect(DATABASE_PATH)
	connection.row_factory = sqlite3.Row
	return connection

def create_predictions_table():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                zip_code TEXT NOT NULL,
                square_feet INTEGER NOT NULL,
                bedrooms INTEGER NOT NULL,
                bathrooms INTEGER NOT NULL,
                year_built INTEGER NOT NULL,
                lot_size INTEGER NOT NULL,
                predicted_price REAL NOT NULL
            )
            """
        )


        connection.commit()

def save_prediction(
    zip_code,
    square_feet,
    bedrooms,
    bathrooms,
    year_built,
    lot_size,
    predicted_price,
):
    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO predictions(
                zip_code,
                square_feet,
                bedrooms,
                bathrooms,
                year_built,
                lot_size,
                predicted_price
            )
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                zip_code,
                square_feet,
                bedrooms,
                bathrooms,
                year_built,
                lot_size,
                predicted_price,
            ),
        )

        connection.commit()
def get_predictions():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                zip_code,
                square_feet,
                bedrooms,
                bathrooms,
                year_built,
                lot_size,
                predicted_price
            FROM predictions
            ORDER BY id DESC
            """
        ).fetchall()

    return rows
def get_dashboard_stats():

    with get_connection() as connection:

        stats = connection.execute(
            """
            SELECT

                COUNT(*) as total_predictions,

                AVG(predicted_price) as average_price,

                MAX(predicted_price) as highest_price,

                MIN(predicted_price) as lowest_price

            FROM predictions
            """
        ).fetchone()

    return stats
def search_predictions(zip_code):

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT *
            FROM predictions
            WHERE zip_code = ?
            ORDER BY id DESC
            """,
            (zip_code,)
        ).fetchall()

    return rows
def get_zip_summary():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                zip_code,
                COUNT(*) AS prediction_count,
                AVG(predicted_price) AS average_price
            FROM predictions
            GROUP BY zip_code
            ORDER BY average_price DESC
            """
        ).fetchall()

    return rows
def get_prediction_trend():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                created_at,
                predicted_price
            FROM predictions
            ORDER BY created_at ASC
            """
        ).fetchall()

    return rows
def filter_predictions(
    zip_code=None,
    bedrooms=None,
    bathrooms=None,
    year_built=None,
):
    query = """
        SELECT *
        FROM predictions
        WHERE 1 = 1
    """

    parameters = []

    if zip_code:
        query += " AND zip_code = ?"
        parameters.append(zip_code)

    if bedrooms is not None:
        query += " AND bedrooms = ?"
        parameters.append(bedrooms)

    if bathrooms is not None:
        query += " AND bathrooms = ?"
        parameters.append(bathrooms)

    if year_built is not None:
        query += " AND year_built = ?"
        parameters.append(year_built)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return rows
def filter_predictions(
    zip_code=None,
    bedrooms=None,
    bathrooms=None,
    year_built=None,
):
    query = """
        SELECT *
        FROM predictions
        WHERE 1 = 1
    """

    parameters = []

    if zip_code:
        query += " AND zip_code = ?"
        parameters.append(zip_code)

    if bedrooms is not None:
        query += " AND bedrooms = ?"
        parameters.append(bedrooms)

    if bathrooms is not None:
        query += " AND bathrooms = ?"
        parameters.append(bathrooms)

    if year_built is not None:
        query += " AND year_built = ?"
        parameters.append(year_built)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return rows
def get_prediction_by_id(prediction_id: int):
    with get_connection() as connection:
        prediction = connection.execute(
            """
            SELECT *
            FROM predictions
            WHERE id = ?
            """,
            (prediction_id,),
        ).fetchone()

    return prediction
