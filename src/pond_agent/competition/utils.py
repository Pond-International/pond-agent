"""Utility functions for data loading and processing."""

import logging
from pathlib import Path

import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)

def read_markdown(file_path: str | Path) -> str:
    """Read markdown file content.

    Args:
        file_path: Path to markdown file

    Returns:
        String containing file content

    """
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def read_data_dictionary(file_path: str | Path) -> dict[str, dict]:
    """Read data dictionary from Excel file.

    Expected Excel format:
    - Row 1: table name
    - Row 2: table description
    - Row 4+: column name and description pairs

    Args:
        file_path: Path to data dictionary Excel file

    Returns:
        Dictionary mapping dataset names to their metadata

    """
    file_path = Path(file_path)

    if file_path.suffix.lower() != ".xlsx":
        raise ValueError("Data dictionary must be an Excel (.xlsx) file")

    logger.info(f"Reading Excel data dictionary from {file_path}")

    try:
        # Read all sheets from Excel file
        sheets = pd.read_excel(
            file_path,
            sheet_name=None,
            engine="openpyxl",
            dtype=str,  # Read all cells as strings
            header=None,  # No header row
            na_filter=False,  # Don't convert empty cells to NaN
        )

        # Convert sheets to dictionary format
        data_dict = {}
        for sheet_name, df in sheets.items():
            logger.debug(f"\nProcessing sheet: {sheet_name}")
            logger.debug("First 10 rows of the sheet:")
            logger.debug(f"\n{df.head(10)}")
            logger.debug(f"\nColumns: {df.columns.tolist()}")
            logger.debug(f"\nFirst row: {df.iloc[0].tolist()}")
            logger.debug(f"\nSecond row: {df.iloc[1].tolist()}")

            try:
                # Get table name and description from first two rows
                table_name_cell = df.iloc[0, 0]  # A1 cell
                table_name_value = df.iloc[0, 1]  # B1 cell
                table_desc_cell = df.iloc[1, 0]  # A2 cell
                table_desc_value = df.iloc[1, 1]  # B2 cell

                logger.debug(f"\nTable name cell (A1): '{table_name_cell}'")
                logger.debug(f"Table name value (B1): '{table_name_value}'")
                logger.debug(f"Table desc cell (A2): '{table_desc_cell}'")
                logger.debug(f"Table desc value (B2): '{table_desc_value}'")

                if not isinstance(table_name_value, str):
                    logger.debug(f"Table name value type: {type(table_name_value)}")
                    table_name_value = str(table_name_value)

                if not isinstance(table_desc_value, str):
                    logger.debug(f"Table desc value type: {type(table_desc_value)}")
                    table_desc_value = str(table_desc_value)

                table_name = table_name_value.strip()
                table_desc = table_desc_value.strip()

                # Find where column definitions start
                col_start_idx = None
                for idx, row in df.iterrows():
                    if isinstance(row[0], str) and row[0].strip().lower() == "column name":
                        col_start_idx = idx + 1
                        logger.debug(f"\nFound column definitions starting at row {idx + 1}")
                        break

                if col_start_idx is None:
                    logger.warning(f"Could not find column definitions in sheet {sheet_name}")
                    continue

                # Get column definitions
                columns = {}
                for idx in range(col_start_idx, len(df)):
                    row = df.iloc[idx]
                    col_name = row[0]
                    col_desc = row[1]

                    if pd.isna(col_name) or pd.isna(col_desc):
                        continue

                    col_name = str(col_name).strip()
                    col_desc = str(col_desc).strip()

                    if col_name and col_desc:
                        columns[col_name] = col_desc

                # Store table info
                data_dict[table_name] = {
                    "description": table_desc,
                    "columns": columns,
                }

            except Exception as e:
                logger.error(f"Error processing sheet {sheet_name}: {e!s}")
                continue

        return data_dict

    except Exception as e:
        logger.error(f"Error reading Excel file: {e!s}")
        raise


def load_parquet_data(data_dir: str | Path, return_path: bool = False) -> dict[str, pl.DataFrame]:
    """Load all parquet files from a directory.

    Args:
        data_dir: Directory containing parquet files

    Returns:
        Dictionary mapping dataset names to DataFrames

    """
    data_dir = Path(data_dir)
    datasets = {}
    data_paths = {}

    # Process all items in the directory
    for item in data_dir.iterdir():
        if item.is_file() and item.suffix == ".parquet":
            # Single parquet file
            name = item.stem.upper()
            datasets[name] = pl.read_parquet(item)
            data_paths[name] = str(item.resolve())
        elif item.is_dir():
            # Directory of parquet files
            if any(f.suffix == ".parquet" for f in item.iterdir()):
                name = item.name.upper()
                datasets[name] = pl.read_parquet(item)
                data_paths[name] = str(item.resolve())

    logger.info(f"Loaded {len(datasets)} datasets from {data_dir}")
    for name, df in datasets.items():
        logger.info(f"  - {name}: shape={df.shape}")

    if return_path:
        return datasets, data_paths

    return datasets

def read_problem_description(overview_path: str | Path) -> str:
    """Load problem description from overview.md file.

    Args:
        overview_path: Path to overview.md file

    Returns:
        String containing problem description

    """
    overview_path = Path(overview_path)

    if not overview_path.exists():
        logger.warning(f"overview.md not found in {overview_path}")
        return ""

    try:
        return read_markdown(overview_path)
    except Exception as e:
        logger.error(f"Error reading overview.md: {e!s}")
        return ""
