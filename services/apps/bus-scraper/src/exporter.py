import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from tabulate import tabulate
import config

def format_terminal_table(records: List[Dict[str, Any]]) -> str:
    """Formats scraped bus records into a clean terminal ASCII table."""
    if not records:
        return "No bus records found."

    display_data = []
    # Sort records by price ascending
    sorted_records = sorted(records, key=lambda x: x.get('price', 0))

    for f in sorted_records:
        sl = f"₹{f['single_lower_price']:.0f} ({f.get('single_lower_seats', 0)})" if f.get('single_lower_price') else "-"
        su = f"₹{f['single_upper_price']:.0f} ({f.get('single_upper_seats', 0)})" if f.get('single_upper_price') else "-"
        dl = f"₹{f['double_lower_price']:.0f} ({f.get('double_lower_seats', 0)})" if f.get('double_lower_price') else "-"
        du = f"₹{f['double_upper_price']:.0f} ({f.get('double_upper_seats', 0)})" if f.get('double_upper_price') else "-"

        display_data.append([
            f.get('operator_name', '')[:25],
            f.get('departure_time', ''),
            f.get('travel_date', ''),
            f"₹{f.get('price', 0):.0f}",
            sl,
            su,
            dl,
            du,
            f"{'Yes 🚽' if f.get('has_toilet') else 'No'}"
        ])

    headers = ["Operator", "Dep", "Date", "Min Fare", "Single Lower", "Single Upper", "Double Lower", "Double Upper", "Toilet"]
    return tabulate(display_data, headers=headers, tablefmt="fancy_grid")

def print_terminal_table(records: List[Dict[str, Any]]):
    """Prints formatted table to stdout."""
    print(format_terminal_table(records))

def export_to_csv(records: List[Dict[str, Any]], travel_date: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Exports scraped records to a timestamped CSV file in `exports/` folder.
    Also updates `exports/redbus_latest_fares.csv` for data pipeline ingestion.
    Returns path to timestamped CSV file.
    """
    if not records:
        return ""

    df = pd.DataFrame(records)

    # Standardized column order for downstream data pipelines
    cols_order = [
        "scraped_at", "travel_date", "operator_name", "bus_type", 
        "departure_time", "arrival_time", "duration", "source", "destination",
        "price", "single_lower_price", "single_lower_seats",
        "single_upper_price", "single_upper_seats",
        "double_lower_price", "double_lower_seats",
        "double_upper_price", "double_upper_seats",
        "has_toilet", "available_seats", "rating_count"
    ]
    df_cols = [c for c in cols_order if c in df.columns]
    df = df[df_cols]

    # Timestamped export path
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = travel_date.replace("-", "") if travel_date else "all"
    timestamped_filename = f"redbus_fares_{date_str}_{ts_str}.csv"
    timestamped_filepath = os.path.join(config.EXPORTS_DIR, timestamped_filename)
    
    df.to_csv(timestamped_filepath, index=False)

    # Update fixed filename `exports/redbus_latest_fares.csv` for pipeline pickup
    latest_filepath = os.path.join(config.EXPORTS_DIR, "redbus_latest_fares.csv")
    df.to_csv(latest_filepath, index=False)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path, index=False)

    # Push to MinIO S3 raw-data bucket if MINIO_ENDPOINT is set
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "")
    if minio_endpoint:
        try:
            from common.lake import DataLakeWriter
            writer = DataLakeWriter(
                minio_endpoint=minio_endpoint,
                access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
                secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
            )
            csv_str = df.to_csv(index=False)
            s3_uri = writer.write_csv(bucket="raw-data", dataset="bus_scraper", csv_content=csv_str)
            print(f"☁️ Exported bus fares to MinIO Data Lake: {s3_uri}")
        except Exception as e:
            print(f"⚠️ MinIO data lake export skipped or failed: {e}")

    return timestamped_filepath


def export_to_json(records: List[Dict[str, Any]], output_path: str) -> str:
    """Exports scraped records to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    return output_path
